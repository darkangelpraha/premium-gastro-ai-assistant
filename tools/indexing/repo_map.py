#!/usr/bin/env python3
import configparser
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

HOME = Path.home()
from typing import Dict, List, Optional, Tuple

DEFAULT_ROOT_CANDIDATES = [
    str(HOME / "Projects"),
    str(HOME / "Development"),
    str(HOME / "Documents"),
    str(HOME / "Desktop"),
    str(HOME / "GitHub"),
    str(HOME / "Repos"),
    str(HOME / "src"),
    str(HOME / "code"),
    str(HOME / "workspace"),
    str(HOME / "Workspaces"),
    str(HOME / "Library" / "CloudStorage"),
]

SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "node_modules",
    ".cache",
    ".Trash",
    ".npm",
    ".pnpm-store",
    ".yarn",
    ".gradle",
    ".m2",
    ".idea",
    ".vscode",
    "__pycache__",
}

SKIP_PATH_PREFIXES = [
    str(HOME / "Library" / "Containers"),
    str(HOME / "Library" / "Caches"),
    str(HOME / "Library" / "Application Support" / "Code" / "Cache"),
    str(HOME / "Library" / "Application Support" / "Cursor" / "Cache"),
    str(HOME / "Library" / "Group Containers"),
]


def sanitize_url(url: str) -> str:
    # Remove credentials if present (https://user:pass@host)
    url = re.sub(r"//[^/@]+@", "//", url)
    return url.strip()


def parse_origin_repo(url: str) -> Tuple[str, str]:
    if not url:
        return "", ""
    # git@github.com:owner/repo.git
    if "@" in url and ":" in url and not url.startswith("http"):
        host = url.split("@", 1)[1].split(":", 1)[0]
        path = url.split(":", 1)[1]
        return host, path.replace(".git", "")
    # https://host/owner/repo.git
    if url.startswith("http"):
        try:
            rest = url.split("://", 1)[1]
            host = rest.split("/", 1)[0]
            path = rest.split("/", 1)[1] if "/" in rest else ""
            return host, path.replace(".git", "")
        except Exception:
            return "", ""
    return "", ""


def resolve_git_dir(repo_path: Path) -> Optional[Path]:
    git_path = repo_path / ".git"
    if git_path.is_dir():
        return git_path
    if git_path.is_file():
        try:
            text = git_path.read_text(encoding="utf-8", errors="ignore").strip()
            if text.startswith("gitdir:"):
                rel = text.split("gitdir:", 1)[1].strip()
                gd = Path(rel)
                if not gd.is_absolute():
                    gd = (repo_path / gd).resolve()
                return gd
        except Exception:
            return None
    return None


def resolve_head(git_dir: Path) -> Tuple[str, str]:
    head_file = git_dir / "HEAD"
    if not head_file.exists():
        return "", ""
    head = head_file.read_text(encoding="utf-8", errors="ignore").strip()
    if head.startswith("ref: "):
        ref = head.replace("ref: ", "").strip()
        ref_path = git_dir / ref
        if ref_path.exists():
            return ref, ref_path.read_text(encoding="utf-8", errors="ignore").strip()
        # fallback to packed-refs
        packed = git_dir / "packed-refs"
        if packed.exists():
            for line in packed.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.startswith("#") or line.startswith("^"):
                    continue
                parts = line.split(" ")
                if len(parts) == 2 and parts[1] == ref:
                    return ref, parts[0]
        return ref, ""
    # detached HEAD
    return "DETACHED", head


def read_origin_url(git_dir: Path) -> str:
    config_path = git_dir / "config"
    if not config_path.exists():
        return ""
    parser = configparser.RawConfigParser()
    try:
        parser.read(config_path)
        section = 'remote "origin"'
        if parser.has_section(section):
            return parser.get(section, "url", fallback="").strip()
    except Exception:
        return ""
    return ""


def is_repo_root(path: Path) -> bool:
    return (path / ".git").exists()


def should_skip_dir(path: Path) -> bool:
    sp = str(path)
    for pref in SKIP_PATH_PREFIXES:
        if sp.startswith(pref):
            return True
    if path.name in SKIP_DIR_NAMES:
        return True
    return False


def collect_repos(roots: List[str]) -> List[Dict[str, str]]:
    repos: List[Dict[str, str]] = []
    for root in roots:
        for dirpath, dirnames, _ in os.walk(root):
            p = Path(dirpath)
            # prune
            dirnames[:] = [d for d in dirnames if not should_skip_dir(p / d)]
            if is_repo_root(p):
                git_dir = resolve_git_dir(p)
                origin = read_origin_url(git_dir) if git_dir else ""
                origin = sanitize_url(origin)
                host, repo = parse_origin_repo(origin)
                head_ref, head_sha = resolve_head(git_dir) if git_dir else ("", "")
                repos.append({
                    "path": str(p),
                    "name": p.name,
                    "git_dir": str(git_dir) if git_dir else "",
                    "origin_url": origin,
                    "origin_host": host,
                    "origin_repo": repo,
                    "head_ref": head_ref,
                    "head_commit": head_sha,
                })
    return repos


def main() -> int:
    roots = [r for r in DEFAULT_ROOT_CANDIDATES if os.path.exists(r)]
    if len(sys.argv) > 1:
        roots = [r for r in sys.argv[1:] if os.path.exists(r)]
    if not roots:
        print("No roots found.")
        return 1

    t0 = time.time()
    repos = collect_repos(roots)

    # classify
    duplicates: Dict[str, List[str]] = {}
    orphans: List[str] = []
    for r in repos:
        if not r["origin_url"]:
            orphans.append(r["path"])
        else:
            duplicates.setdefault(r["origin_url"], []).append(r["path"])

    dupes = {k: v for k, v in duplicates.items() if len(v) > 1}

    # write outputs
    out_csv = Path("REPO_MAP.csv")
    out_md = Path("REPO_MAP.md")
    out_json = Path("REPO_MAP.json")

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "path", "name", "origin_url", "origin_host", "origin_repo",
            "head_ref", "head_commit", "git_dir",
        ])
        w.writeheader()
        for r in repos:
            w.writerow(r)

    summary = {
        "roots": roots,
        "total_repos": len(repos),
        "orphans": len(orphans),
        "duplicate_remotes": len(dupes),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    out_json.write_text(json.dumps({
        "summary": summary,
        "repos": repos,
        "orphans": orphans,
        "duplicates": dupes,
    }, indent=2), encoding="utf-8")

    with out_md.open("w", encoding="utf-8") as f:
        f.write("# Repo Map\n\n")
        f.write(f"Generated: {summary['generated_at']}\n\n")
        f.write("## Summary\n")
        f.write(f"- Roots scanned: {len(roots)}\n")
        for r in roots:
            f.write(f"- {r}\n")
        f.write(f"\n- Total repos: {summary['total_repos']}\n")
        f.write(f"- Orphans (no origin): {summary['orphans']}\n")
        f.write(f"- Duplicate remotes: {summary['duplicate_remotes']}\n\n")

        f.write("## Duplicate Remotes\n")
        if dupes:
            for url, paths in sorted(dupes.items(), key=lambda x: len(x[1]), reverse=True):
                f.write(f"- {url}\n")
                for p in paths:
                    f.write(f"  - {p}\n")
        else:
            f.write("- None\n")

        f.write("\n## Orphaned Repos (no origin)\n")
        if orphans:
            for p in sorted(orphans):
                f.write(f"- {p}\n")
        else:
            f.write("- None\n")

    dt = time.time() - t0
    print(json.dumps({
        "summary": summary,
        "seconds": round(dt, 2),
        "csv": str(out_csv.resolve()),
        "md": str(out_md.resolve()),
        "json": str(out_json.resolve()),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
