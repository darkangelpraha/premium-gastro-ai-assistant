#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys


def _indexer_running() -> bool:
    try:
        out = subprocess.check_output(["ps", "ax", "-o", "command="], text=True)
    except Exception:
        return False
    needle = "scripts/index_dropbox_qdrant.py"
    for line in out.splitlines():
        if needle in line and "python" in line:
            return True
    return False


def main() -> int:
    # Avoid parallel runs: the main indexer may already be running for days.
    if _indexer_running():
        return 0

    # Low-impact mode: this wrapper is intended for periodic catch-up runs after completion
    # (or after a crash) to pick up newly added/changed files. The heavy work is in the indexer.
    cmd = [sys.executable, "scripts/index_dropbox_qdrant.py"]
    env = dict(os.environ)
    return subprocess.call(cmd, env=env)


if __name__ == "__main__":
    raise SystemExit(main())

