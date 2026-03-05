#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=0
for arg in "$@"; do
  if [[ "$arg" == "--dry-run" ]]; then
    DRY_RUN=1
  fi
done

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

BLUEJET_BASE_URL="${BLUEJET_BASE_URL:-https://czeco.bluejet.cz}"
QDRANT_URL="${QDRANT_URL:-http://127.0.0.1:6333}"
BLUEJET_API_TOKEN_ID="${BLUEJET_API_TOKEN_ID:-}"
BLUEJET_API_TOKEN_HASH="${BLUEJET_API_TOKEN_HASH:-}"
BLUEJET_API_TOKEN_ID_OP_REF="${BLUEJET_API_TOKEN_ID_OP_REF:-}"
BLUEJET_API_TOKEN_HASH_OP_REF="${BLUEJET_API_TOKEN_HASH_OP_REF:-}"
BLUEJET_API_DIRECT_TOKEN="${BLUEJET_API_DIRECT_TOKEN:-}"
BLUEJET_API_DIRECT_TOKEN_OP_REF="${BLUEJET_API_DIRECT_TOKEN_OP_REF:-}"

echo "[info] BlueJet mirror preflight"
echo "[info] Base URL: $BLUEJET_BASE_URL"
echo "[info] Qdrant URL: $QDRANT_URL"
echo "[info] Mode: $([[ "$DRY_RUN" -eq 1 ]] && echo "dry-run" || echo "write")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[fail] python3 not found"
  exit 1
fi

TOKEN_OK=0
if [[ -n "$BLUEJET_API_TOKEN_ID" && -n "$BLUEJET_API_TOKEN_HASH" ]]; then
  TOKEN_OK=1
  echo "[pass] BlueJet tokens found in environment"
fi

if [[ "$TOKEN_OK" -eq 0 && -n "$BLUEJET_API_DIRECT_TOKEN" ]]; then
  TOKEN_OK=1
  echo "[pass] BlueJet direct token found in environment"
fi

if [[ "$TOKEN_OK" -eq 0 && -n "$BLUEJET_API_TOKEN_ID_OP_REF" && -n "$BLUEJET_API_TOKEN_HASH_OP_REF" ]]; then
  if command -v op >/dev/null 2>&1; then
    TOKEN_OK=1
    echo "[pass] 1Password OP refs configured and op CLI detected"
  else
    echo "[fail] OP refs are set but 'op' CLI is missing"
    exit 1
  fi
fi

if [[ "$TOKEN_OK" -eq 0 && -n "$BLUEJET_API_DIRECT_TOKEN_OP_REF" ]]; then
  if command -v op >/dev/null 2>&1; then
    TOKEN_OK=1
    echo "[pass] 1Password direct token OP ref configured and op CLI detected"
  else
    echo "[fail] Direct token OP ref is set but 'op' CLI is missing"
    exit 1
  fi
fi

if [[ "$TOKEN_OK" -eq 0 ]]; then
  echo "[fail] Missing BlueJet credentials."
  echo "       Set BLUEJET_API_TOKEN_ID + BLUEJET_API_TOKEN_HASH"
  echo "       or BLUEJET_API_DIRECT_TOKEN"
  echo "       or BLUEJET_API_TOKEN_ID_OP_REF + BLUEJET_API_TOKEN_HASH_OP_REF"
  echo "       or BLUEJET_API_DIRECT_TOKEN_OP_REF"
  exit 1
fi

if [[ "$DRY_RUN" -eq 0 ]]; then
  if ! command -v curl >/dev/null 2>&1; then
    echo "[fail] curl not found (required for Qdrant probe)"
    exit 1
  fi
  if curl -fsS --max-time 5 "$QDRANT_URL/collections" >/dev/null 2>&1; then
    echo "[pass] Qdrant endpoint reachable"
  else
    echo "[fail] Qdrant endpoint is not reachable: $QDRANT_URL"
    exit 1
  fi
fi

echo "[pass] Preflight OK"
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "[next] python3 tools/indexing/index_bluejet_qdrant.py --dry-run --evidences 293"
else
  echo "[next] python3 tools/indexing/index_bluejet_qdrant.py --evidences 293,356,323"
fi
