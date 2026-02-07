# Indexing Toolkit (Qdrant + Filesystems)

This folder contains the canonical, versioned scripts for building auditable semantic indexes.

## Dropbox to Qdrant (Semantic Index)
Script: `tools/indexing/index_dropbox_qdrant.py`

### What This Script Guarantees
- No deletes on disk.
- When a file is reindexed, old vectors for that file are deleted inside Qdrant first (by `payload.path`) to prevent stale chunks.
- A file is only marked "complete" in the SQLite state DB after its vectors were successfully upserted to Qdrant.
  This avoids a classic correctness bug: marking files as indexed even when embedding/upsert failed, which would cause permanent gaps.

### Core Features
- Incremental indexing via a local SQLite state DB (`QDRANT_STATE_DB`).
- Config-sensitive caching: `cfg_hash` is stored per file so changing chunking/model/extraction settings triggers reindex.
- Chunking + overlap (better recall on long documents).
- Large-file support:
  - For huge text files: bounded sampling windows across the file.
  - For PDFs: page sampling across the document, not only the first pages.
  - For XLSX: streaming read with cell cap.
- Deduplication:
  - File-level dedup across multiple roots (prefix+suffix hashing, bounded reads).
  - Embedding-level in-memory cache (avoids repeated embedding calls for identical chunks).
  - Stale canonical path handling (if the canonical path disappears or is outside the scanned roots, the script promotes a valid copy and deletes stale Qdrant points).
- Auditing:
  - JSONL audit file (`QDRANT_AUDIT_PATH`).
  - Each run emits a unique `run_id` and includes it in batch events.

### Embeddings Providers
- `openai`:
  - Uses `POST /v1/embeddings` with batch input.
- `ollama` (recommended for local/offline):
  - Uses `POST /api/embed` with batch inputs and `truncate` support (modern Ollama API).
  - Falls back to legacy `POST /api/embeddings` if needed.

### Qdrant Best-Practice Writes
- Supports `QDRANT_WAIT` and `QDRANT_ORDERING` (wait for completion + write ordering semantics).
- Supports Qdrant API key via `QDRANT_API_KEY` (sent as `api-key` header).
- Creates payload indexes for: `path`, `name`, `source`, `mtime`.
  - Supports on-disk payload indexes via `QDRANT_PAYLOAD_INDEX_ON_DISK=1`.
  - Supports principal index for `mtime` via `QDRANT_MTIME_IS_PRINCIPAL=1`.

### Quickstart
```bash
export QDRANT_URL="http://127.0.0.1:6333"
export QDRANT_COLLECTION="dropbox_semantic_v3"
export QDRANT_EMBEDDING_PROVIDER="ollama"   # or openai
export OLLAMA_MODEL="nomic-embed-text"

python3 tools/indexing/index_dropbox_qdrant.py \
  "$HOME/Library/CloudStorage/Dropbox" \
  "$HOME/Library/CloudStorage/Dropbox (Backup)"
```

### Important Env Vars
- `QDRANT_URL`: Qdrant endpoint.
- `QDRANT_API_KEY`: optional; uses `api-key` header.
- `QDRANT_COLLECTION`: collection name.
- `QDRANT_EMBEDDING_PROVIDER`: `ollama` or `openai`.
- `QDRANT_BATCH_SIZE`: Qdrant upsert batch size (points).
- `QDRANT_WAIT`: `1` or `0`.
- `QDRANT_ORDERING`: `weak` | `medium` | `strong`.
- `QDRANT_CHUNK_SIZE`, `QDRANT_CHUNK_OVERLAP`: chunking controls.
- `QDRANT_MAX_BYTES`: max bytes read per file (sampling budget).
- `QDRANT_SAMPLE_WINDOWS`: number of windows sampled across large files.
- `QDRANT_MAX_CHUNKS_PER_FILE`: cap points per file.
- `QDRANT_DEDUP_FILES`: `1`/`0` for cross-root file dedup.
- `QDRANT_DEDUP_EMBEDDINGS`: `1`/`0` for embedding cache.
- `QDRANT_EMBED_MAX_CHARS`: clamp text length sent to embeddings to avoid context-length failures.
- `QDRANT_EXCLUDE_DIRS`: comma-separated directory names to skip (defaults include `.dropbox.cache`, `.git`, `node_modules`).
- `QDRANT_EXCLUDE_FILES`: comma-separated file names to skip (defaults include `.DS_Store`).
- `OLLAMA_HOST`, `OLLAMA_MODEL`.
- `OLLAMA_USE_BATCH`: `1`/`0`.
- `OLLAMA_BATCH_SIZE`.
- `OLLAMA_TRUNCATE`: `1`/`0`.
- `INDEX_HTTP_CONNECT_TIMEOUT`, `INDEX_HTTP_MAX_TIME`: curl timeouts (seconds).
- `INDEX_HTTP_RETRIES`, `INDEX_HTTP_RETRY_SLEEP_SECONDS`: retry policy for transient network failures.

### Operational Notes (Do/Don\x27t)
- Do keep `QDRANT_BATCH_SIZE >= QDRANT_MAX_CHUNKS_PER_FILE` to avoid splitting a single file across multiple upserts.
  The script enforces this internally, but matching it avoids surprises.
- Do treat audit logs as sensitive: they contain file paths.
- Don\x27t put API keys in repo.
- Don\x27t mark files complete before Qdrant confirms the upsert.

## Full Filesystem Map (Inventory)
Script: `tools/indexing/full_fs_map.py`

Outputs a snapshot directory with:
- `FS_MAP.jsonl.gz` (atomic: written to `.tmp` then renamed on completion)
- `FS_PROGRESS.json` heartbeat (every ~5s)
- `FS_SUMMARY.json` totals + metadata
- `FS_ERRORS.log` permission and stat errors

## Repo Map (Git Inventory)
Script: `tools/indexing/repo_map.py`

Maps all reachable git repos under chosen roots.
Outputs CSV/JSON/MD summaries with:
- repo path, origin remote (sanitized), HEAD ref/sha
- duplicates and orphans

Last updated: 2026-02-07
