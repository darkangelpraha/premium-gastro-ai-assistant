#!/usr/bin/env python3
"""Read-only audit of quarantine/restore/recovered holding areas.

Purpose
- Produce a human-readable inventory of holding folders so they can be
  re-integrated into the correct hierarchy or safely removed later.

Safety
- Read-only. Never deletes or moves anything.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


def _simplify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.casefold()


def _run(cmd: List[str], timeout: int = 120) -> Tuple[int, str, str]:
    p = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
    )
    return p.returncode, p.stdout, p.stderr


def _du_size_mb(path: Path) -> float:
    rc, out, _ = _run(["du", "-sk", str(path)], timeout=300)
    if rc != 0:
        return 0.0
    try:
        kb = int(out.strip().split()[0])
        return round(kb / 1024.0, 1)
    except Exception:
        return 0.0


def _iter_google_drive_mounts() -> Iterable[Path]:
    cs = Path.home() / "Library" / "CloudStorage"
    if not cs.exists():
        return
    for p in cs.iterdir():
        if p.is_dir() and p.name.startswith("GoogleDrive-"):
            yield p


def _find_my_drive(drive_root: Path) -> Optional[Path]:
    want = {"my drive", "muj disk"}
    try:
        for p in drive_root.iterdir():
            if p.is_dir() and _simplify(p.name) in want:
                return p
    except Exception:
        return None
    return None


def _iter_holding_dirs(root: Path) -> Iterable[Path]:
    if not root.exists():
        return
    try:
        for p in root.iterdir():
            if not p.is_dir():
                continue
            n = p.name
            if n.startswith("__QUARANTINE__") or n.startswith("RESTORE__"):
                yield p
    except Exception:
        return


_RX_HOLDING = re.compile(r"(__QUARANTINE__|RESTORE__|Recovered|Recovery|_RecoveredFromDriveBackup|Recovered_Backup)", re.IGNORECASE)


def _iter_projects_holding(projects: Path) -> Iterable[Path]:
    if not projects.exists():
        return
    # Shallow scan: look at top-level buckets + a few known heavy buckets.
    buckets: List[Path] = []
    try:
        buckets = [p for p in projects.iterdir() if p.is_dir()]
    except Exception:
        buckets = []

    # Always include 99-Legacy (holding area by definition).
    for b in buckets:
        if b.name == "99-Legacy":
            yield b

    # Also include any bucket with obvious holding markers.
    for b in buckets:
        if b.name == "99-Legacy":
            continue
        if _RX_HOLDING.search(b.name):
            yield b


def _count_top_level(path: Path) -> int:
    try:
        return sum(1 for _ in path.iterdir())
    except Exception:
        return 0


def _find_git_repos(root: Path, max_depth: int = 6, max_hits: int = 2000) -> int:
    # Count repo roots by detecting ".git" directories.
    # Depth limit keeps this safe and fast.
    root = root.resolve()
    hits = 0
    for dirpath, dirnames, _filenames in os.walk(root, followlinks=False):
        rel = Path(dirpath).relative_to(root)
        if len(rel.parts) > max_depth:
            dirnames[:] = []
            continue
        if ".git" in dirnames:
            hits += 1
            if hits >= max_hits:
                return hits
            dirnames[:] = []
            continue
        # prune common huge dirs
        for skip in ("node_modules", ".venv", "venv", "__pycache__", ".pytest_cache"):
            if skip in dirnames:
                dirnames.remove(skip)
    return hits


@dataclass(frozen=True)
class HoldingInfo:
    path: str
    kind: str
    size_mb: float
    top_level_items: int
    git_repos: int


def _write_tsv(out_path: Path, rows: List[HoldingInfo]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["path", "kind", "size_mb", "top_level_items", "git_repos"])
        for r in rows:
            w.writerow([r.path, r.kind, f"{r.size_mb:.1f}", str(r.top_level_items), str(r.git_repos)])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="Output TSV path")
    ap.add_argument("--projects", default=str(Path.home() / "Projects"), help="Projects root")
    ap.add_argument("--max-depth", type=int, default=6, help="Max depth when counting git repos")
    ns = ap.parse_args()

    rows: List[HoldingInfo] = []

    # Google Drive holding folders.
    for mount in _iter_google_drive_mounts():
        my_drive = _find_my_drive(mount)
        if not my_drive:
            continue
        for d in _iter_holding_dirs(my_drive):
            rows.append(
                HoldingInfo(
                    path=str(d),
                    kind="gdrive_holding",
                    size_mb=_du_size_mb(d),
                    top_level_items=_count_top_level(d),
                    git_repos=_find_git_repos(d, max_depth=ns.max_depth),
                )
            )

    # Projects holding folders.
    projects = Path(ns.projects).expanduser()
    for d in _iter_projects_holding(projects):
        rows.append(
            HoldingInfo(
                path=str(d),
                kind="projects_holding",
                size_mb=_du_size_mb(d),
                top_level_items=_count_top_level(d),
                git_repos=_find_git_repos(d, max_depth=ns.max_depth),
            )
        )

    rows = sorted(rows, key=lambda r: (r.kind, -r.size_mb, r.path))
    out_path = Path(ns.out).expanduser()
    _write_tsv(out_path, rows)

    print(f"holding_dirs={len(rows)} out={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
