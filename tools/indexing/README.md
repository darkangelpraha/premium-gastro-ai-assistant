# Indexing Toolkit (Qdrant + Filesystems)

This folder contains the canonical, versioned scripts for building auditable semantic indexes.

## Dropbox to Qdrant (Semantic Index)
Script: `tools/indexing/index_dropbox_qdrant.py`

Key features:
- Incremental indexing via a local SQLite state DB (skips unchanged files).
- Chunking + overlap (better recall and relevance on long documents).
- Large-file support (bounded sampling windows across huge text files).
- File-level dedup across multiple roots (avoids indexing identical duplicates).
- Embedding-level dedup cache (avoids repeated embedding calls for identical chunks).
- PDF page sampling (spreads extraction across the document, not only the first pages).
- Audit log per batch + structured run summary.
- Payload indexes in Qdrant (`path`, `name`, `source`, `mtime`) for fast filtering.

Safety model:
- No deletes on disk.
- When a file changes, old vectors for that file (`payload.path`) are deleted inside Qdrant first to prevent stale chunks.

### Quickstart
```bash
export QDRANT_URL="http://127.0.0.1:6333"
export QDRANT_COLLECTION="dropbox_semantic_v2"
export QDRANT_EMBEDDING_PROVIDER="ollama"   # or openai
export OLLAMA_MODEL="nomic-embed-text"

python3 tools/indexing/index_dropbox_qdrant.py   "$HOME/Library/CloudStorage/Dropbox"   "$HOME/Library/CloudStorage/Dropbox (Backup)"
```

### Important env vars
- `QDRANT_URL`: Qdrant endpoint.
- `QDRANT_COLLECTION`: collection name.
- `QDRANT_EMBEDDING_PROVIDER`: `ollama` or `openai`.
- `QDRANT_BATCH_SIZE`: Qdrant upsert batch size (points).
- `QDRANT_CHUNK_SIZE`, `QDRANT_CHUNK_OVERLAP`: chunking controls.
- `QDRANT_MAX_BYTES`: max bytes read per file (sampling budget).
- `QDRANT_SAMPLE_WINDOWS`: number of windows sampled across large files.
- `QDRANT_MAX_CHUNKS_PER_FILE`: cap points per file.
- `QDRANT_DEDUP_FILES`: 1/0 for cross-root file dedup.
- `QDRANT_DEDUP_EMBEDDINGS`: 1/0 for embedding cache.

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
