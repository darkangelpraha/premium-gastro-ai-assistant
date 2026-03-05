# Multi-Agent Runtime

Lightweight orchestrator for running specialized jobs in prioritized profiles.

## Goal

1. Client-impact first: data quality and KPI visibility (`client_impact` profile).
2. Internal operations second: internal process snapshots (`internal_ops` profile).

## Jobs

- `bluejet_kpi_digest`: BlueJet orders/invoices snapshot (7d/long-window counts + amounts in CZK), with Qdrant mirror fallback.
- `ga4_audit`: checks GA4 stream availability and basic event health.
- `gtm_audit`: checks GTM workspace/tag/trigger hygiene.
- `kpi_daily_digest`: builds daily KPI digest from GA4 metrics.
- `internal_ops_snapshot`: scaffold for internal process checks.

## Configuration

`tools/agents/config.json` defines profiles and ordered jobs.

## Required Environment

- `GA4_PROPERTY_IDS`: comma-separated GA4 property IDs (e.g. `123456789,987654321`).
- `GTM_CONTAINER_IDS`: comma-separated GTM container identifiers.
  - accepted format: `accounts/<account_id>/containers/<container_id>` or `<account_id>/<container_id>`.
- `BLUEJET_API_TOKEN_ID` and `BLUEJET_API_TOKEN_HASH` for BlueJet jobs.
- Optional `BLUEJET_BASE_URL` (default `https://czeco.bluejet.cz`).
- Optional `BLUEJET_KPI_MAX_ROWS` (default `1000`).
- Optional `BLUEJET_KPI_LOOKBACK_DAYS` (default `180`).
- Optional `QDRANT_URL`/`QDRANT_API_KEY` for mirror fallback.
- Optional `GOOGLE_API_SCOPES`: override OAuth scopes used for ADC token retrieval.

## One-time Auth Bootstrap

Before first run, configure ADC scopes for GA4/GTM APIs:

```bash
./tools/agents/bootstrap_google_scopes.sh
```

The jobs use Application Default Credentials via:

- `gcloud auth application-default print-access-token`

The orchestrator also auto-loads local `.env` (without overriding already exported vars).

## Usage

```bash
python3 -m tools.agents.orchestrator list-profiles
python3 -m tools.agents.orchestrator list-jobs
python3 -m tools.agents.orchestrator run --profile client_impact
python3 -m tools.agents.orchestrator run --profile client_impact_google
python3 -m tools.agents.orchestrator run --profile internal_ops
python3 -m tools.agents.orchestrator run --profile full
```

## BlueJet -> Looker (No GA4/GTM OAuth)

One-command sync of BlueJet orders/invoices into BigQuery tables for Looker Studio:

```bash
./scripts/run_bluejet_looker_sync.sh
```

Defaults:

- Project: `premium-gastro-35094`
- Dataset: `bluejet_reporting`
- Tables: `orders_out`, `invoices_out`

Override example:

```bash
./scripts/run_bluejet_looker_sync.sh --project premium-gastro-35094 --dataset bluejet_reporting --max-rows 50000
```

Run artifacts are written under:

- `reports/agent_runs/<utc_run_id>_<profile>/summary.json`
- `reports/agent_runs/<utc_run_id>_<profile>/summary.md`
- job-specific JSON/MD artifacts.

## Recommended Schedule

- `client_impact`: hourly or every 4 hours during business hours.
- `client_impact_google`: daily (optional, when OAuth scopes are available).
- `internal_ops`: daily.
- `full`: nightly.
