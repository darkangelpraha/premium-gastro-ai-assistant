#!/usr/bin/env python3
"""Quarantine obvious dev artifacts that ended up in Google Drive "My Drive" root.

Why this exists
- Cloud-synced folders (Google Drive for Desktop) are a bad place to keep dev caches
  and internal repo guts (node_modules packages, git objects, etc.).
- When those artifacts land at the top-level of "My Drive", Finder becomes unusable
  and conflicts create endless "(1)", "(2)" duplicates.

What this does (safe-by-default)
- DRY RUN by default: scans and produces a plan.
- With --apply: moves matching entries into a quarantine folder INSIDE the same
  Google Drive "My Drive". This is a rename on the same filesystem, not a copy.
- Never deletes anything.

Scope
- Only scans the top-level of "My Drive".
- Does not touch normal business folders.

Notes
- The Czech "Můj disk" folder name can contain a combining diacritic; this tool
  locates it via Unicode normalization.
"""

from __future__ import annotations

import argparse
import json
import re
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


DEFAULT_ACCOUNT = "ps@premium-gastro.com"


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _today() -> str:
    return time.strftime("%Y-%m-%d")


def _simplify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.casefold()


def _drive_root_from_account(account: str) -> Path:
    return Path.home() / "Library/CloudStorage" / f"GoogleDrive-{account}"


def _find_my_drive(drive_root: Path) -> Path:
    # Common names: "My Drive" or Czech "Můj disk".
    want = {"my drive", "muj disk"}
    for p in drive_root.iterdir():
        if p.is_dir() and _simplify(p.name) in want:
            return p
    raise FileNotFoundError(f"My Drive folder not found under {drive_root}")


_RX_DUP_SUFFIX = re.compile(r"\s*\(\d+\)\s*$")


def _strip_dup_suffix(name: str) -> str:
    return _RX_DUP_SUFFIX.sub("", name).strip()


@dataclass(frozen=True)
class Candidate:
    src: Path
    category: str
    reason: str


def _classify_entry(p: Path) -> Optional[Candidate]:
    name = p.name
    base = _strip_dup_suffix(name)

    # NPM scoped packages (e.g., @grpc, @google-cloud).
    if re.match(r"^@[A-Za-z0-9._-]+$", base):
        return Candidate(p, "node_pkgs/scoped", "Looks like npm scoped package")

    # Common unscoped npm packages seen in the incident.
    if base.lower() in {"rimraf", "glob", "node-which"}:
        return Candidate(p, "node_pkgs/unscoped", "Looks like npm package")

    # Git objects layout: directories named by 2-hex prefixes.
    if p.is_dir() and re.match(r"^[0-9a-fA-F]{2}$", base):
        return Candidate(p, "git_objects/dirs_2hex", "Looks like git objects prefix dir")

    # Git object IDs and similar hashes dumped into root.
    if re.match(r"^[0-9a-fA-F]{24,}$", base):
        return Candidate(p, "git_objects/hex_items", "Looks like hex hash/object")

    return None


def _iter_top_level(my_drive: Path) -> Iterable[Path]:
    for p in my_drive.iterdir():
        yield p


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _unique_dest(dest: Path) -> Path:
    if not dest.exists():
        return dest
    # Avoid collisions deterministically.
    stem = dest.name
    parent = dest.parent
    for i in range(1, 10_000):
        alt = parent / f"{stem}__moved__{i}"
        if not alt.exists():
            return alt
    raise RuntimeError(f"Could not find free destination name near {dest}")


def _write_jsonl(path: Path, rec: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=True) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", default=DEFAULT_ACCOUNT)
    ap.add_argument(
        "--drive-root",
        default="",
        help="Optional explicit GoogleDrive-* mount root (defaults to ~/Library/CloudStorage/GoogleDrive-<account>)",
    )
    ap.add_argument(
        "--quarantine-name",
        default="",
        help="Folder name created under My Drive (default: __QUARANTINE__DevArtifacts__YYYY-MM-DD)",
    )
    ap.add_argument(
        "--batch",
        type=int,
        default=500,
        help="Max items to move per run (safety throttle)",
    )
    ap.add_argument("--apply", action="store_true", help="Actually move items (default: dry-run)")
    args = ap.parse_args()

    drive_root = Path(args.drive_root).expanduser() if args.drive_root else _drive_root_from_account(args.account)
    if not drive_root.exists():
        print(f"ERROR: Google Drive mount not found: {drive_root}")
        return 2

    my_drive = _find_my_drive(drive_root)
    qname = args.quarantine_name or f"__QUARANTINE__DevArtifacts__{_today()}"
    quarantine = my_drive / qname

    # Pre-create quarantine subfolders.
    for sub in [
        "node_pkgs/scoped",
        "node_pkgs/unscoped",
        "git_objects/dirs_2hex",
        "git_objects/hex_items",
        "_logs",
    ]:
        _ensure_dir(quarantine / sub)

    log_path = quarantine / "_logs" / f"quarantine_{time.strftime("%Y%m%d-%H%M%S")}.jsonl"

    candidates: List[Candidate] = []
    skipped = 0
    for p in _iter_top_level(my_drive):
        if p == quarantine:
            skipped += 1
            continue
        if p.name.startswith("__QUARANTINE__"):
            # Never touch other quarantine folders.
            skipped += 1
            continue
        c = _classify_entry(p)
        if c:
            candidates.append(c)

    by_cat: Dict[str, int] = {}
    for c in candidates:
        by_cat[c.category] = by_cat.get(c.category, 0) + 1

    print(f"My Drive: {my_drive}")
    print(f"Quarantine: {quarantine}")
    print(f"Candidates: {len(candidates)} (skipped={skipped})")
    for k in sorted(by_cat):
        print(f"- {k}: {by_cat[k]}")

    if not args.apply:
        print("DRY RUN: no changes made. Re-run with --apply to move items.")
        return 0

    moved = 0
    errors = 0
    for c in candidates[: max(args.batch, 0) or len(candidates)]:
        dest_dir = quarantine / c.category
        dest = _unique_dest(dest_dir / c.src.name)
        rec = {
            "ts": _now_iso(),
            "action": "move",
            "src": str(c.src),
            "dest": str(dest),
            "category": c.category,
            "reason": c.reason,
        }
        try:
            c.src.rename(dest)
            moved += 1
            rec["ok"] = True
        except Exception as e:
            errors += 1
            rec["ok"] = False
            rec["error"] = f"{type(e).__name__}: {e}"
        _write_jsonl(log_path, rec)

    print(f"DONE: moved={moved} errors={errors} log={log_path}")
    if moved < len(candidates):
        left = len(candidates) - moved
        print(f"Remaining candidates: {left} (run again to continue)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
