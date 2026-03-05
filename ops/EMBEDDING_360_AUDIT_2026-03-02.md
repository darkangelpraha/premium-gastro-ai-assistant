# Embedding 360 Audit (2026-03-02)

## Executive Summary

- Current failures are caused by dimension mismatch (`384` vs `768`) between selected collection and active embedding provider.
- BlueJet business collections are already in production and should be mirrored safely with hourly updates.
- To avoid repeated reindex incidents, standardize via:
  - strict embedding contract
  - alias-based cutovers
  - shadow index validation before production switch

## Current Qdrant State (NAS)

Observed key collections:

- `dropbox_backup_2026_02_07_semantic_v2` -> dim `768` (~340k points)
- `dropbox_backup_2026_02_07_semantic` -> dim `768`
- `supplier_apify_semantic_v2` -> dim `768`
- `tech_docs_vectors` -> dim `384` (~22k points)
- `unified_memory` -> dim `384` (~3.3k points)

BlueJet collections:

- `bluejet_companies` -> dim `1536`
- `bluejet_contacts` -> dim `1536`
- `bluejet_products` -> dim `1536`
- `bluejet_offers_out` -> dim `1`
- `bluejet_orders_out` -> dim `1`
- `bluejet_invoices_out` -> dim `1`

## Existing Job Dependencies

- Dropbox hourly/daily mirror:
  - `ops/launchagents/com.premiumgastro.qdrant.dropbox.delta.plist`
  - targets `dropbox_backup_2026_02_07_semantic_v2`
  - provider `ollama`, model `nomic-embed-text`

- BlueJet ingest:
  - no robust hourly mirror script was present in repo before this phase
  - read/query/export tooling existed (`bluejet_mcp`, `bluejet_query.sh`, logistics exports)

## Risks Found

1. Runtime drift:
   - scripts pointed to one collection while scheduler/jobs filled another.
2. Embedding contract missing at infrastructure level:
   - collections with mixed dimensions without explicit environment gate.
3. No formal cutover pattern:
   - migration risk if switching providers/models directly on active collections.

## Phase 1 (Implemented in repo)

- Added BlueJet hourly-safe mirror script:
  - `tools/indexing/index_bluejet_qdrant.py`
- Added runbook:
  - `ops/BLUEJET_QDRANT_MIRROR_PHASE1.md`
- Added launchagent template:
  - `ops/launchagents/com.premiumgastro.qdrant.bluejet.hourly.plist`

### Phase 1 behavior

- GET-only BlueJet reads
- upserts to existing BlueJet collections
- preserves existing vectors where present
- non-destructive by default (no delete operations)
- writes mirror audit/state for traceability

## Recommended Target Architecture

1. Qdrant as single retrieval memory substrate.
2. One active alias per memory domain:
   - `memory_active_dropbox`
   - `memory_active_bluejet`
   - `memory_active_workspace`
3. Embedding contract (mandatory metadata):
   - `embedding_family`
   - `embedding_model`
   - `embedding_dim`
   - `chunk_policy_version`
4. Shadow index rollout:
   - dual-write / dual-read eval
   - alias cutover only after quality + latency gate pass

## Phase 2 Proposal

- Build unified memory ingestion registry (all sources: workstation, iCloud, Dropbox, Google Workspace, email, chats).
- Add named vectors or parallel collections for modern embedding trial.
- Benchmark candidate models on real B2B e-commerce/showroom queries.
- Promote winner via alias switch, keep rollback alias.

## Phase 3 Proposal

- Validate Supabase role:
  - metadata/control plane + app access
  - no direct coupling to vector schema evolution
- Ensure event-driven refresh pipeline:
  - BlueJet hourly
  - mailbox/chat near-real-time where possible
  - cloud drive incremental schedules
- Add SLO dashboard:
  - ingest freshness
  - error rate
  - search latency
  - recall proxy metrics
