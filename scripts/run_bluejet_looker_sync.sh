#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

set -a
[ -f .env ] && source .env
set +a

PYTHONPATH="${PYTHONPATH:-}:$(pwd)" python3 tools/agents/pipelines/bluejet_bq_sync.py "$@"
