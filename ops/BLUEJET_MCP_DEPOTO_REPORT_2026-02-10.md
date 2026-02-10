# BlueJet MCP + Depoto Integration - Status & Report (2026-02-10)

## 1) What Was Found Locally

- `~/Projects/02-MCP-Servers/bluejet_mcp`
  - This is a real MCP server implemented with **FastMCP**.
  - It already contained a `Dockerfile`, `requirements.txt`, and `server.py`.
- No existing Docker container for BlueJet MCP was running prior to this work (only unrelated MCP containers were present).

## 2) What Was Fixed/Improved (Core Reliability)

The original `server.py` had issues that could break real usage:

- `POST/PUT` requests were broken due to a variable bug (payload variable mismatch).
- It printed to stdout, which can break MCP stdio transport (protocol expects stdout clean).
- Token refresh required manual retry.
- No concurrency guard for token refresh.

Fixes applied:

- `POST/PUT` payload is now correct.
- Logging goes to `stderr`.
- Token refresh on `401` is automatic and retries once.
- Auth token is cached with a TTL (default 23h; BlueJet token validity is documented as 24h).
- Safe-by-default: write methods (`POST/PUT/DELETE`) are blocked unless `BLUEJET_READ_ONLY=0`.

## 3) Stable Docker Deployment (Mac / Docker Desktop)

### Compose file created

- `/Users/premiumgastro/Projects/03-Business-Tools/Docker_Configs/docker-compose-bluejet-mcp.yml`

### Secrets handling (no repo leakage)

Secrets are stored in a local env file (permissions `600`):

- `/Users/premiumgastro/Projects/03-Business-Tools/Docker_Configs/env/bluejet-mcp.env`

It is generated from 1Password item:

- `BlueJet API FULL` (fields `BLUEJET_API_TOKEN_ID`, `BLUEJET_API_TOKEN_HASH`)

### Runtime status

- Container name: `docker_configs-bluejet-mcp-1`
- Bound locally: `http://127.0.0.1:8741/mcp/`
- Healthcheck: socket open on port 8000 inside container

## 4) Continue (VS Code) Integration

Continue supports URL MCP servers. The following was added to:

- `.continue/agents/new-config.yaml`

Server:

- `bluejet-mcp`
- `http://127.0.0.1:8741/mcp/`

## 5) Depoto - What We Know (So Far)

Local docs exist:

- `/Users/premiumgastro/Projects/00-Premium-Gastro/DEPOTO_LOGISTICS_INTEGRATION.md`

Key facts:

- Depoto clearly offers integrations and references an "open API", but public API docs are not reliably discoverable.
- Best practical path is to obtain Depoto API docs directly from Depoto support/sales (or use Shoptet Premium ready-made integration if available).

## 6) BlueJet - What We Know (API Surface)

Public documentation for BlueJet REST exists and matches the current auth approach:

- Token auth: `tokenID` + `tokenHash` → returns `X-Token` valid for ~24h.

This supports the “send delivery notes to Depoto / get receipts back” integration concept:

- BlueJet has evidence entities referencing delivery-note-related records and purchase/receipt-related fields.

## 7) Recommended Next Steps (Depoto Integration)

1. Obtain Depoto’s official integration method:
   - API docs (preferred)
   - Alternative import/export formats (CSV/XML/EDI) if API is not available
2. Define the two concrete flows:
   - BlueJet → Depoto: “dodaci list” (outbound / fulfillment order payload)
   - Depoto → BlueJet: “prijemka” (goods receipt / warehouse receipt payload)
3. Only after official docs exist:
   - Implement a small “Depoto Sync” service (Docker) that:
     - reads BlueJet records
     - pushes to Depoto
     - receives Depoto webhooks
     - writes tracking/receipts back to BlueJet

## 8) Where This Was Saved For Long-Term Reference

The improved BlueJet MCP code and documentation were copied into the GH “assistant” repo under:

- `tools/mcp/bluejet_mcp/`

No secrets were committed.

