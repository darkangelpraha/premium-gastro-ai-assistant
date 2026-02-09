#!/usr/bin/env python3
"""
Dev repo inventory for non-IT workflows.

Goals:
- Find git repositories under one or more roots (default: ~/Projects).
- Emit a TSV inventory that is easy to sort/filter (Excel, Numbers, etc.).
- Provide safe, human-friendly tag suggestions:
  - dev OK (green): actively relevant to current stack / business.
  - dev MAY (orange): keepable tools/experiments; not critical day-to-day.
  - dev NO (red): quarantine/legacy/recovered; not in active use.
- Detect "web-ish" repos and mark them as dev WEB (blue) candidates.

This script is read-only: it never modifies files. Tagging is done by a separate tool.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


PRIMARY_TAGS = ("dev OK", "dev MAY", "dev NO")


@dataclass(frozen=True)
class RepoInfo:
    path: str
    projects_bucket: str
    size_mb: float
    origin: str
    gh_owner: str
    gh_repo: str
    head: str
    last_commit: str
    dirty_files: int
    tag_suggest: str
    tag_reason: str
    is_web: int
    web_reason: str


def _run(cmd: List[str], timeout: int = 20, cwd: Optional[str] = None) -> Tuple[int, str, str]:
    p = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
    )
    return p.returncode, p.stdout, p.stderr


def _du_size_mb(path: Path) -> float:
    # macOS du supports -sk. Use 1024-based MB for stability.
    rc, out, _ = _run(["du", "-sk", str(path)], timeout=60)
    if rc != 0:
        return 0.0
    try:
        kb = int(out.strip().split()[0])
        return round(kb / 1024.0, 1)
    except Exception:
        return 0.0


def _git(cmd: List[str], repo: Path, timeout: int = 20) -> Tuple[int, str, str]:
    return _run(["git", "-C", str(repo)] + cmd, timeout=timeout)


def _git_origin(repo: Path) -> str:
    rc, out, _ = _git(["remote", "get-url", "origin"], repo, timeout=10)
    if rc == 0:
        return out.strip()
    return ""


_GH_PATTERNS = [
    # https://github.com/owner/repo(.git)
    re.compile(r"^https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$"),
    # git@github.com:owner/repo(.git)
    re.compile(r"^git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$"),
    # ssh://git@github.com/owner/repo(.git)
    re.compile(r"^ssh://git@github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$"),
]


def _parse_github_origin(origin: str) -> Tuple[str, str]:
    origin = (origin or "").strip()
    for pat in _GH_PATTERNS:
        m = pat.match(origin)
        if m:
            return m.group("owner"), m.group("repo")
    return "", ""


def _git_head(repo: Path) -> str:
    rc, out, _ = _git(["rev-parse", "--short", "HEAD"], repo, timeout=10)
    if rc == 0:
        return out.strip()
    return ""


def _git_last_commit(repo: Path) -> str:
    rc, out, _ = _git(["log", "-1", "--format=%cI"], repo, timeout=10)
    if rc == 0:
        return out.strip()
    return ""


def _git_dirty_files(repo: Path) -> int:
    rc, out, _ = _git(["status", "--porcelain"], repo, timeout=20)
    if rc != 0:
        return 0
    lines = [ln for ln in out.splitlines() if ln.strip()]
    return len(lines)


def _projects_bucket(path: Path) -> str:
    # Best-effort: detect ".../Projects/<bucket>/..."
    parts = path.parts
    for i, p in enumerate(parts):
        if p == "Projects" and i + 1 < len(parts):
            return parts[i + 1]
    return ""


def _suggest_primary_tag(repo_path: Path, bucket: str) -> Tuple[str, str]:
    p = str(repo_path)

    # Strong "NO" signals first.
    no_markers = (
        "/99-Legacy/",
        "/_RecoveredFromDriveBackup/",
        "/Recovered_Backup",
        "/_Quarantine/",
        "/RESTORE__",
        "/__QUARANTINE__",
        "/Trash",
        "/KOS",
        "/Koš",
    )
    if any(m in p for m in no_markers):
        return "dev NO", "Legacy/recovered/quarantine path"

    # Bucket defaults.
    ok_buckets = {"00-Premium-Gastro", "01-Pan-Talir", "03-Business-Tools", "04-Integrations", "05-Data-Storage"}
    no_buckets = {"99-Legacy"}
    may_buckets = {"02-MCP-Servers", "05-AI-Experiments", "06-Development-Tools", "07-Scripts", "08-Design-Assets", "99-Forks"}

    if bucket in ok_buckets:
        return "dev OK", f"Bucket={bucket}"
    if bucket in no_buckets:
        return "dev NO", f"Bucket={bucket}"
    if bucket in may_buckets:
        return "dev MAY", f"Bucket={bucket}"

    # Fallback: keep but de-prioritize.
    return "dev MAY", "Unclassified bucket"


def _is_web_repo(repo: Path) -> Tuple[bool, str]:
    pkg = repo / "package.json"
    if not pkg.exists():
        return False, "no package.json"

    web_cfgs = [
        "next.config.js",
        "next.config.mjs",
        "next.config.cjs",
        "next.config.ts",
        "vite.config.js",
        "vite.config.mjs",
        "vite.config.cjs",
        "vite.config.ts",
        "astro.config.mjs",
        "astro.config.js",
        "astro.config.ts",
        "nuxt.config.js",
        "nuxt.config.ts",
        "svelte.config.js",
        "svelte.config.mjs",
        "remix.config.js",
        "gatsby-config.js",
    ]
    for n in web_cfgs:
        if (repo / n).exists():
            return True, "config:" + n

    try:
        data = json.loads(pkg.read_text(encoding="utf-8"))
    except Exception:
        return False, "package.json parse failed"

    deps: Dict[str, str] = {}
    for k in ("dependencies", "devDependencies", "peerDependencies"):
        if isinstance(data.get(k), dict):
            deps.update({str(a): str(b) for a, b in data[k].items()})

    markers = {
        "next",
        "nuxt",
        "vite",
        "astro",
        "gatsby",
        "@sveltejs/kit",
        "svelte",
        "react",
        "react-dom",
        "vue",
        "@vue/runtime-dom",
        "angular",
        "@angular/core",
        "remix",
        "@remix-run/dev",
        "solid-js",
        "@builder.io/qwik",
        "tailwindcss",
        "postcss",
        "sass",
        "wrangler",
    }
    hits = sorted([m for m in markers if m in deps])
    if hits:
        return True, "deps:" + ",".join(hits[:6])

    if (repo / "pages").is_dir() or (repo / "app").is_dir() or (repo / "public").is_dir():
        return True, "dirs:app/pages/public"

    return False, "no web markers"


def _walk_git_repos(root: Path) -> Iterable[Path]:
    # Detect repo root by the presence of a ".git" directory.
    for dirpath, dirnames, _filenames in os.walk(root, followlinks=False):
        # Skip heavy / irrelevant paths early.
        dn = set(dirnames)
        if ".git" in dn:
            yield Path(dirpath)
            # Do not descend into repo subfolders.
            dirnames[:] = []
            continue

        # Prune common huge dirs.
        for skip in (".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", ".next", "dist", "build"):
            if skip in dn:
                dirnames.remove(skip)


def _write_tsv(out_path: Path, rows: List[RepoInfo]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(
            [
                "path",
                "projects_bucket",
                "size_mb",
                "origin",
                "gh_owner",
                "gh_repo",
                "head",
                "last_commit",
                "dirty_files",
                "tag_suggest",
                "tag_reason",
                "is_web",
                "web_reason",
            ]
        )
        for r in rows:
            w.writerow(
                [
                    r.path,
                    r.projects_bucket,
                    f"{r.size_mb:.1f}",
                    r.origin,
                    r.gh_owner,
                    r.gh_repo,
                    r.head,
                    r.last_commit,
                    str(r.dirty_files),
                    r.tag_suggest,
                    r.tag_reason,
                    str(r.is_web),
                    r.web_reason,
                ]
            )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--root",
        action="append",
        default=[],
        help="Root to scan (repeatable). Default: ~/Projects",
    )
    ap.add_argument("--out", required=True, help="Output TSV path")
    ap.add_argument("--log", default="", help="Optional JSONL log path (append)")
    ap.add_argument("--max", type=int, default=0, help="Optional max repos (0 = no limit)")
    ns = ap.parse_args()

    roots = [Path(os.path.expanduser(r)) for r in ns.root] if ns.root else [Path.home() / "Projects"]
    out_path = Path(os.path.expanduser(ns.out))
    log_path = Path(os.path.expanduser(ns.log)) if ns.log else None

    ts = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    repos: List[Path] = []
    for root in roots:
        if root.exists():
            repos.extend(list(_walk_git_repos(root)))

    # Stable order for diffing.
    repos = sorted(set(repos), key=lambda p: str(p))
    if ns.max and ns.max > 0:
        repos = repos[: ns.max]

    rows: List[RepoInfo] = []
    logf = log_path.open("a", encoding="utf-8") if log_path else None
    try:
        for repo in repos:
            bucket = _projects_bucket(repo)
            size_mb = _du_size_mb(repo)
            origin = _git_origin(repo)
            owner, gh_repo = _parse_github_origin(origin)
            head = _git_head(repo)
            last_commit = _git_last_commit(repo)
            dirty = _git_dirty_files(repo)

            tag, reason = _suggest_primary_tag(repo, bucket)
            is_web, web_reason = _is_web_repo(repo)

            info = RepoInfo(
                path=str(repo),
                projects_bucket=bucket,
                size_mb=size_mb,
                origin=origin,
                gh_owner=owner,
                gh_repo=gh_repo,
                head=head,
                last_commit=last_commit,
                dirty_files=dirty,
                tag_suggest=tag,
                tag_reason=reason,
                is_web=1 if is_web else 0,
                web_reason=web_reason,
            )
            rows.append(info)
            if logf:
                logf.write(
                    json.dumps(
                        {
                            "ts": ts,
                            "action": "dev_repo_inventory_row",
                            "path": info.path,
                            "bucket": info.projects_bucket,
                            "size_mb": info.size_mb,
                            "origin": info.origin,
                            "tag_suggest": info.tag_suggest,
                            "is_web": info.is_web,
                        },
                        ensure_ascii=True,
                    )
                    + "\n"
                )
    finally:
        if logf:
            logf.close()

    _write_tsv(out_path, rows)
    print(f"repos={len(rows)} out={out_path}")
    if log_path:
        print(f"log={log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

