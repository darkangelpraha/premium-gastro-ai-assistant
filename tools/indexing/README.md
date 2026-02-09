# Indexing Toolkit (Qdrant + Filesystems)

This folder contains the canonical, versioned scripts for building auditable semantic indexes.

## Dropbox to Qdrant (Semantic Index)
Script: `tools/indexing/index_dropbox_qdrant.py`

### What This Script Guarantees
- No deletes on disk (your Dropbox files are never modified or removed).
- Incremental indexing: unchanged files are skipped reliably.
- Correctness under failures:
  - A file is only marked `complete=1` in the SQLite state DB after Qdrant confirms the upsert.
  - On reindex, the script avoids wiping an existing file index up front. It upserts new vectors first, then deletes only stale chunks (`chunk_index >= new_chunk_total`) to prevent lingering old chunks.

### Core Features
- Incremental indexing via a local SQLite state DB (`QDRANT_STATE_DB`).
- Config-sensitive caching: `cfg_hash` is stored per file so changing chunking/model/extraction settings triggers reindex.
- Chunking + overlap (better recall on long documents).
- Large-file support:
  - Huge text files: bounded sampling windows across the file (`QDRANT_MAX_BYTES`, `QDRANT_SAMPLE_WINDOWS`).
  - PDFs: page sampling across the document (bounded by `QDRANT_PDF_MAX_PAGES`).
  - XLSX: capped extraction (`QDRANT_XLSX_MAX_CELLS`).
- Deduplication:
  - File-level dedup across multiple roots (prefix+suffix hashing, bounded reads).
  - Embedding-level in-memory cache (avoids repeated embedding calls for identical chunks).
  - Stale canonical path handling (if the canonical path disappears or is outside scanned roots, the script promotes a valid copy and deletes stale Qdrant points).
- Auditing:
  - JSONL audit file (`QDRANT_AUDIT_PATH`).
  - Each run emits a unique `run_id` and includes it in batch events.

### Preview Snippets (Search Result Previews)
- Each Qdrant point payload includes a short `preview` field (default 400 chars).
- Optional local snippets DB for richer previews and keyword search:
  - SQLite DB: `QDRANT_SNIPPETS_DB`
  - Table: `chunks` (and optional `chunks_fts` for FTS5)

### OCR Support (Scanned PDFs / Images)
The indexer itself does not do heavy OCR inline.

Instead:
1. Indexer extracts text normally (PDFs via `pdftotext`, DOCX/XLSX via OOXML parsing).
2. If a PDF/image has too little text and there is no OCR sidecar present, it enqueues a job in `ocr_queue` (in the state DB).
3. Run the OCR backfill worker to generate sidecars into `QDRANT_OCR_SIDECAR_DIR`:
   - Script: `tools/indexing/ocr_backfill.py`
   - Uses: `tesseract`, `pdftoppm`, `pdfinfo` (and `sips`/`convert` for HEIC)
4. Next index run will reprocess those files automatically because sidecar `mtime/size` is tracked in `file_state`.

### Embeddings Providers
- `openai`:
  - Uses `POST /v1/embeddings` with batch input.
- `ollama` (recommended for local/offline):
  - Uses `POST /api/embed` with batch inputs (modern Ollama API).
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
export QDRANT_COLLECTION="dropbox_semantic_v4"
export QDRANT_EMBEDDING_PROVIDER="ollama"   # or openai
export OLLAMA_MODEL="nomic-embed-text"

python3 tools/indexing/index_dropbox_qdrant.py \
  "$HOME/Library/CloudStorage/Dropbox" \
  "$HOME/Library/CloudStorage/Dropbox (Backup)"
```

### Search Tool (Shows Previews)
Script: `tools/indexing/search_dropbox_index.py`

Examples:
```bash
python3 tools/indexing/search_dropbox_index.py "invoice 2024" --limit 10
python3 tools/indexing/search_dropbox_index.py "proforma" --fts --limit 10
python3 tools/indexing/search_dropbox_index.py "proforma" --hybrid --limit 10
```

### Evaluation Harness (Quality Tests)
Script: `tools/indexing/eval_index.py`

Input format: JSONL lines, e.g.:
```jsonl
{"query":"invoice 2024","expect_any":["Invoices/2024"],"k":10}
{"query":"serial number DS423","expect_any":["Synology"],"k":10}
```

Run:
```bash
python3 tools/indexing/eval_index.py --queries queries.sample.jsonl --k 10
```

### Important Env Vars (Indexing)
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
- `QDRANT_EXCLUDE_DIRS`: comma-separated directory names to skip.
- `QDRANT_EXCLUDE_FILES`: comma-separated file names to skip.
- `QDRANT_PAYLOAD_PREVIEW_MAX_CHARS`: preview length stored in Qdrant payload (`preview`).
- `QDRANT_SNIPPETS_ENABLED`: `1`/`0` to enable snippets DB.
- `QDRANT_SNIPPETS_DB`: snippets DB path.
- `QDRANT_SNIPPET_MAX_CHARS`: snippet text length stored in snippets DB.
- `QDRANT_SNIPPETS_FTS`: `1`/`0` enable FTS5 virtual table + triggers.
- `QDRANT_OCR_SIDECAR_DIR`: where OCR sidecars live.
- `QDRANT_OCR_PDF_MIN_TEXT_CHARS`: threshold to treat a PDF as "no text" and queue OCR.

### Important Env Vars (OCR Worker)
- `OCR_LANGS`: tesseract language(s), e.g. `eng` or `eng+ces` (if installed).
- `OCR_MAX_FILES`: max files processed per run.
- `OCR_MAX_PAGES`: max pages OCR'd per PDF (sampled).
- `OCR_RENDER_DPI`: render DPI for PDF OCR.
- `OCR_LOG_PATH`: log path for OCR worker.
- `OCR_FORCE=1`: reprocess even already `done`.

### Operational Notes (Do/Don't)
- Do treat audit logs, snippet DB, and OCR sidecars as sensitive: they contain file paths and extracted text.
- Don't put API keys in git.
- Don't run OCR at unlimited scale; keep it in small batches and let it catch up gradually.

## Dev Repo Audit + Finder Tags (macOS)

In addition to indexing, this repo contains a safe inventory + Finder tagging workflow to keep `~/Projects` human-readable:
- Inventory script: `tools/indexing/dev_repo_inventory.py`
- Tag applier: `tools/indexing/finder_tags_apply.py` (Finder metadata only, no moves/deletes)
- Methodology: `ops/DEV_REPO_AUDIT_AND_TAGS_2026-02-09.md`

Last updated: 2026-02-09
