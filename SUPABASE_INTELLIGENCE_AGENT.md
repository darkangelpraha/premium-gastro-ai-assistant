#!/usr/bin/env python3
"""
SUPABASE INTELLIGENCE AGENT - APIFY SCRAPE + QDRANT INGEST

Scope
- Dedicated Supabase agent to crawl docs + GitHub + YouTube via Apify website-content-crawler
- Ingest embeddings into Qdrant collection tech_docs_vectors
- Staggered cron schedules per tool; webhook for release/fix updates
- Backfill via local run (`python3 supabase_apify_agent.py --run-now`)

Constraints / lessons learned
- Apify plan may block public actors (HTTP 403 public-actor-disabled). Use a private actor or local run.
- Apify task names must be lowercase with hyphen separators.
- Prefer launchctl/cron with exported env for non-interactive runs.

Environment variables (see env.example)
- APIFY_API_TOKEN
- APIFY_TASK_ID (lowercase-hyphen)
- QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION (default tech_docs_vectors)
- APIFY_WEBHOOK_URL (optional, for release/fix updates)
- SUPABASE_URL, SUPABASE_KEY (for future manifest storage)

Staggered cron (examples)
- Docs crawl:      5 */6 * * *
- GitHub crawl:   15 2 * * *
- YouTube crawl:  45 3 * * 1,4

Backfill
- Run locally while Apify public actors are blocked:
  python3 supabase_apify_agent.py --run-now
- Local manifest path is user-specific; pick any writable path (e.g., ./supabase_manifest.json)

Webhook
- Set APIFY_WEBHOOK_URL in Apify task settings to receive release/fix notifications.
- Keep payload handling idempotent (keyed by run_id + source URL).

Qdrant ingest
- Collection: tech_docs_vectors
- Upsert key: URL checksum to avoid duplicates
- Batch size: keep under 100 vectors per request to avoid timeouts
"""
