#!/usr/bin/env python3
"""
SUPABASE INTELLIGENCE AGENT - APIFY SCRAPE + QDRANT INGEST

This guide documents the Supabase intelligence agent that:
- Crawls Supabase docs, GitHub, and YouTube transcripts via Apify website-content-crawler
- Generates embeddings and ingests to Qdrant collection tech_docs_vectors
- Supports staggered cron schedules per source/tool and webhook callbacks for release/fix updates

Notes & constraints:
- Apify plan may block running public actors (HTTP 403 public-actor-disabled). Use a private actor or run locally with your token.
- Apify task names must be lowercase with hyphens.
- Prefer launchctl/cron with exported env for non-interactive runs.
"""

# 🧩 Requirements
- Python 3.12+
- Environment variables set (see `env.example`):
  - `APIFY_API_TOKEN`
  - `APIFY_TASK_ID` (lowercase-hyphen task name)
  - `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION` (defaults to `tech_docs_vectors`)
  - `APIFY_WEBHOOK_URL` (optional webhook for release/fix updates)
  - `SUPABASE_URL`, `SUPABASE_KEY` (for manifest storage if needed)

# ⚙️ Staggered schedules
- Use separate cron entries per tool/source to avoid concurrent load:
  - Docs: `5 */6 * * *` (every 6h)
  - GitHub: `15 2 * * *` (daily)
  - YouTube transcripts: `45 3 * * 1,4` (twice weekly)
- Ensure each cron exports the required env vars before invoking the script.

# 🚀 Running locally (backfill)
```bash
python3 supabase_apify_agent.py --run-now
```
- This runs the full scrape + Qdrant ingest once, useful when Apify public actors are blocked.
- If Apify 403 persists, run `ultra_scraper.py` (local fallback) and then ingest via the same script.

# 🔄 Webhook
- Set `APIFY_WEBHOOK_URL` in Apify task settings to receive release/fix notifications.
- Payload should include source URL, run ID, status, and document count; handle idempotently on receiver.

# 🗄️ Qdrant ingest
- Target collection: `tech_docs_vectors`
- Embedding model: use Apify actor default or local embedding in `supabase_apify_agent.py`
- Upsert strategy: idempotent by document URL + checksum to avoid duplicates.

# 📂 Manifest
- Latest backfill manifest path (local example): `/Users/premiumgastro/Projects/Mem0/supabase_manifest.json`
- Store run metadata (timestamp, sources, counts) for auditability.

# 🛠️ Troubleshooting
- **HTTP 403 public-actor-disabled**: Switch to private actor or run locally with token.
- **Slow ingest**: Stagger cron, batch upserts (e.g., 100 vectors/batch).
- **Webhook silence**: Verify `APIFY_WEBHOOK_URL` reachable and HTTPS.
