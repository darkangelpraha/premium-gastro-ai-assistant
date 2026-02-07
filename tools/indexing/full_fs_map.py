#!/usr/bin/env python3
import gzip
import json
import os
import stat
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Set


def default_roots() -> List[str]:
    roots: List[str] = []
    home = "/Users/premiumgastro"
    if os.path.exists(home):
        roots.append(home)
    vols = "/Volumes"
    if os.path.isdir(vols):
        for name in sorted(os.listdir(vols)):
            path = os.path.join(vols, name)
            if os.path.isdir(path):
                roots.append(path)
    # de-dup by realpath
    seen: Set[str] = set()
    out: List[str] = []
    for r in roots:
        rp = os.path.realpath(r)
        if rp in seen:
            continue
        seen.add(rp)
        out.append(r)
    return out


def iter_paths(root: str) -> Iterable[str]:
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        yield dirpath
        for name in filenames:
            yield os.path.join(dirpath, name)


def file_entry(path: str, st: os.stat_result, is_dir: bool, is_link: bool) -> Dict:
    mode = stat.S_IMODE(st.st_mode)
    return {
        "path": path,
        "type": "dir" if is_dir else ("symlink" if is_link else "file"),
        "size": st.st_size if not is_dir else None,
        "mtime": int(st.st_mtime),
        "mode": oct(mode),
    }


def main() -> int:
    roots = default_roots()
    output_dir: Path | None = None
    args = [a for a in sys.argv[1:] if a.strip()]
    if args:
        # Allow: --output-dir /path and/or custom roots
        if "--output-dir" in args:
            i = args.index("--output-dir")
            if i + 1 < len(args):
                output_dir = Path(args[i + 1])
                args = [a for j, a in enumerate(args) if j not in (i, i + 1)]
        if args:
            roots = [r for r in args if os.path.exists(r)]
    if not roots:
        print("No roots found.")
        return 1

    base = Path.cwd()
    ts = time.strftime("%Y%m%d-%H%M%S")
    snap = output_dir or (base / f"FSMapSnapshot-{ts}")
    snap.mkdir(exist_ok=True)

    out_jsonl_tmp = snap / "FS_MAP.jsonl.gz.tmp"
    out_jsonl = snap / "FS_MAP.jsonl.gz"
    out_err = snap / "FS_ERRORS.log"
    out_summary = snap / "FS_SUMMARY.json"
    out_roots = snap / "FS_ROOTS.json"
    out_progress = snap / "FS_PROGRESS.json"

    total_files = 0
    total_dirs = 0
    total_links = 0
    total_errors = 0
    total_bytes = 0

    out_roots.write_text(json.dumps({"roots": roots}, indent=2), encoding="utf-8")

    last_progress = time.time()
    with gzip.open(out_jsonl_tmp, "wt", encoding="utf-8") as jf, out_err.open("w", encoding="utf-8") as ef:
        for root in roots:
            for path in iter_paths(root):
                try:
                    st = os.lstat(path)
                    is_dir = stat.S_ISDIR(st.st_mode)
                    is_link = stat.S_ISLNK(st.st_mode)
                    entry = file_entry(path, st, is_dir, is_link)
                    jf.write(json.dumps(entry) + "\n")
                    if is_dir:
                        total_dirs += 1
                    elif is_link:
                        total_links += 1
                        total_files += 1
                        total_bytes += st.st_size
                    else:
                        total_files += 1
                        total_bytes += st.st_size
                    # progress heartbeat every ~5s
                    if time.time() - last_progress > 5:
                        out_progress.write_text(json.dumps({
                            "root": root,
                            "total_files": total_files,
                            "total_dirs": total_dirs,
                            "total_symlinks": total_links,
                            "total_errors": total_errors,
                            "total_bytes": total_bytes,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        }, indent=2), encoding="utf-8")
                        last_progress = time.time()
                except Exception as e:
                    total_errors += 1
                    ef.write(f"{path}\t{type(e).__name__}: {e}\n")

    # finalize: move tmp to final to signal a complete map
    try:
        out_jsonl_tmp.replace(out_jsonl)
    except Exception:
        # If rename fails, keep tmp so data is not lost
        pass

    summary = {
        "roots": roots,
        "total_files": total_files,
        "total_dirs": total_dirs,
        "total_symlinks": total_links,
        "total_errors": total_errors,
        "total_bytes": total_bytes,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "snapshot": str(snap),
        "map_file": str(out_jsonl) if out_jsonl.exists() else str(out_jsonl_tmp),
        "errors_file": str(out_err),
    }
    out_summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
