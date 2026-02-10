#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Iterable, Sequence


def _parse_windows(s: str) -> list[int]:
    out: list[int] = []
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        n = int(part)
        if n <= 1:
            raise ValueError("windows must be > 1")
        out.append(n)
    if not out:
        raise ValueError("no windows provided")
    return out


def _get_meta(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return str(row[0]) if row and row[0] is not None else None


def _count(conn: sqlite3.Connection, sql: str, params: Sequence[object] = ()) -> int:
    row = conn.execute(sql, params).fetchone()
    return int(row[0]) if row else 0


def _updated_at_window(conn: sqlite3.Connection, cfg_hash: str, n: int) -> list[int]:
    rows = conn.execute(
        "SELECT updated_at FROM file_state WHERE cfg_hash = ? ORDER BY updated_at DESC LIMIT ?",
        (cfg_hash, n),
    ).fetchall()
    out: list[int] = []
    for (ts,) in rows:
        if ts is None:
            continue
        out.append(int(ts))
    return out


def _fmt_pct(done: int, total: int) -> str:
    if total <= 0:
        return "0.000%"
    return f"{(done / total) * 100:.3f}%"


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Show Dropbox->Qdrant index status from the SQLite state DB.")
    p.add_argument(
        "--db",
        default=str(Path.cwd() / ".cache" / "qdrant_dropbox_state.sqlite"),
        help="Path to SQLite state DB (default: ./.cache/qdrant_dropbox_state.sqlite)",
    )
    p.add_argument(
        "--windows",
        type=_parse_windows,
        default=[100, 200, 400, 800],
        help="Comma-separated sizes for rate/ETA estimation (default: 100,200,400,800)",
    )
    args = p.parse_args(list(argv) if argv is not None else None)

    db = Path(str(args.db)).expanduser()
    if not db.exists():
        raise SystemExit(f"State DB not found: {db}")

    conn = sqlite3.connect(str(db))
    try:
        run_cfg_hash = _get_meta(conn, "run_cfg_hash") or _get_meta(conn, "config_hash")
        if not run_cfg_hash:
            raise SystemExit("Missing meta.run_cfg_hash (state DB is not initialized).")

        total = _count(conn, "SELECT COUNT(*) FROM file_state")
        done = _count(conn, "SELECT COUNT(*) FROM file_state WHERE cfg_hash = ?", (run_cfg_hash,))
        remaining = max(0, total - done)

        print(f"db={db}")
        print(f"run_cfg_hash={run_cfg_hash}")
        print(f"total_files={total}")
        print(f"indexed_files={done}")
        print(f"remaining_files={remaining}")
        print(f"progress={_fmt_pct(done, total)}")

        for n in args.windows:
            ts = _updated_at_window(conn, run_cfg_hash, n)
            if len(ts) < 2:
                print(f"window_{n}_rate_per_hour=NA")
                print(f"window_{n}_eta_days=NA")
                continue
            tmax = max(ts)
            tmin = min(ts)
            dt = max(1, tmax - tmin)
            rate_per_hour = ((len(ts) - 1) / dt) * 3600.0
            eta_days = (remaining / rate_per_hour / 24.0) if rate_per_hour > 0 else float("inf")
            print(f"window_{n}_rate_per_hour={rate_per_hour:.1f}")
            print(f"window_{n}_eta_days={eta_days:.2f}")

        # Optional: OCR queue status
        try:
            rows = conn.execute(
                "SELECT status, COUNT(*) FROM ocr_queue GROUP BY status ORDER BY status"
            ).fetchall()
        except sqlite3.Error:
            rows = []
        if rows:
            print("ocr_queue=" + ",".join(f"{status}:{count}" for status, count in rows))
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

