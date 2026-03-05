# Phases 1-3 Continuity Checklist (BlueJet + Memory)

Owner: Premium Gastro AI Ops
Last update: 2026-03-02
Mode: safety-first, NAS-safe, read-only-first validation

## Phase 1: BlueJet -> Qdrant Mirror (Priority)

Objective:
- Keep BlueJet entities mirrored in Qdrant with status changes.

Status:
- In progress, core implementation done.

Implemented:
- `tools/indexing/index_bluejet_qdrant.py`
- `tools/indexing/bluejet_mirror_preflight.sh`
- LaunchAgent templates:
  - `ops/launchagents/com.premiumgastro.qdrant.bluejet.hourly.plist`
  - `ops/launchagents/com.premiumgastro.qdrant.bluejet.nightly-full.plist`
- API safety controls:
  - throttling, retry/backoff, retry-after handling
  - batch size caps and pauses
  - run caps for low-resource NAS
  - `--dry-run` (no Qdrant writes)

Remaining tasks:
1. Deploy LaunchAgents to `~/Library/LaunchAgents` and load them.
2. Run 24h pilot:
   - 2h lite schedule (293/356/323)
   - nightly full schedule
3. Validate logs + freshness SLA.

ETA:
- Deploy + smoke validation: 30-45 min
- 24h pilot validation: 1 day

Dependencies:
- Valid BlueJet credentials (now verified via 1Password vault `Missive BJ`)
- Reachable NAS Qdrant endpoint

## Phase 2: Embedding Modernization (No Reindex Chaos)

Objective:
- Prevent repeated reindex cycles; move to contract-based rollout.

Status:
- Audit done, migration architecture ready, execution pending.

Implemented:
- `ops/EMBEDDING_360_AUDIT_2026-03-02.md`
- Runtime policy enforcement:
  - `tools/indexing/llm_runtime_policy.py`
  - integrated into indexing/search/eval scripts

Remaining tasks:
1. Define final embedding contract:
   - model, dimension, chunk policy, metadata schema
2. Create shadow collection(s) for candidate model.
3. Run quality/latency benchmark set.
4. Alias cutover with rollback alias.

ETA:
- Contract + shadow setup: 0.5 day
- Benchmark + decision: 1-2 days
- Cutover + rollback validation: 0.5 day

Dependencies:
- Final candidate model decision
- Stable evaluation query set from business use-cases

## Phase 3: Unified Memory Ingestion + Refresh Automation

Objective:
- One operational memory surface (Qdrant as SSoT), continuously refreshed.

Status:
- Architecture direction clear, automation integration pending.

Remaining tasks:
1. Source registry:
   - workstation, iCloud, Dropbox, Google Workspace, email/chat systems
2. Trigger strategy:
   - event-driven where possible
   - scheduled deltas otherwise
3. Observability:
   - freshness, failures, ingestion lag, retry counters
4. Supabase role hardening:
   - app/control-plane usage only, no vector schema coupling

ETA:
- Source/triggers matrix: 1 day
- Implement first full set of connectors/triggers: 2-4 days
- Stabilization + alerting: 1-2 days

Dependencies:
- Connector credentials and API scopes per source
- Confirmed webhook endpoints for each provider

## Missing Inputs For Full Automatic Setup

Required to reach full unattended mode:
1. Confirm which scheduler host is authoritative:
   - Mac LaunchAgents vs NAS cron/container
2. Final webhook URLs + secrets for:
   - email/chat providers
   - Google Workspace push where available
3. Alert routing destination:
   - Slack/Missive/email target
4. Approval for production write enable window:
   - initial pilot cutoff/rollback policy

## Cutover Definition of Done

1. BlueJet mirror freshness <= 2h for status entities.
2. Nightly full sync completed without fatal errors for 3 consecutive runs.
3. Embedding alias cutover completed with rollback tested.
4. Unified trigger map documented and running.
5. Dashboards/log-based checks available for handover.

