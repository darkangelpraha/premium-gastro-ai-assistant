# BlueJet MCP + Depoto Integration - Status & Report (2026-02-10)

## 1) What Was Found Locally

- `~/Projects/02-MCP-Servers/bluejet_mcp`
  - Real MCP server implemented with FastMCP.
  - Contains `Dockerfile`, `requirements.txt`, and `server.py`.
- No existing Docker container for BlueJet MCP was running prior to this work.

## 2) What Was Fixed/Improved (Core Reliability)

The original BlueJet MCP `server.py` had issues that could break real usage:

- POST/PUT requests were broken due to a payload variable bug.
- It printed to stdout, which can break MCP stdio transport.
- Token refresh required manual retry.
- No concurrency guard for token refresh.

Fixes applied:

- POST/PUT payload is now correct.
- Logging goes to stderr.
- Token refresh on 401 is automatic and retries once.
- Auth token is cached with a TTL (default 23h).
- Safe-by-default: write methods (POST/PUT/DELETE) are blocked unless `BLUEJET_READ_ONLY=0`.

## 3) Stable Docker Deployment (Mac / Docker Desktop)

### Compose file

- `/Users/premiumgastro/Projects/03-Business-Tools/Docker_Configs/docker-compose-bluejet-mcp.yml`

### Secrets handling

Secrets are stored in a local env file (permissions 600):

- `/Users/premiumgastro/Projects/03-Business-Tools/Docker_Configs/env/bluejet-mcp.env`

Generated from 1Password item:

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

## 5) Depoto - Verified Integration Facts

Grounded sources:

- Depoto PHP client: `TomAtomCZ/depotoPhpClient`
- Depoto PHP client wiki pages: "Napojeni / Import objednavek", "Udalosti", "Dopravci", "Objednavky"

Verified facts:

- Depoto exposes a GraphQL API.
- Auth is OAuth2. Token endpoint is `POST /oauth/v2/token`.
- GraphQL endpoint is `POST /graphql` with `Authorization: Bearer <token>`.
- Depoto supports per-checkout webhook delivery via `updateCheckout(id, eventUrl)`.
- Depoto expects webhooks to be acknowledged quickly and processed asynchronously.
- `paymentItems.isPaid` defaults to true if omitted and can prematurely push orders into picking.
- Depoto uses stable carrier IDs (e.g. `ppl`, `zasilkovna`).

Spec saved in this repo:

- `ops/DEPOTO_LOGISTICS_INTEGRATION.md`

## 6) BlueJet - What We Know (API Surface)

Public documentation for BlueJet REST exists and matches the current auth approach:

- Token auth: `tokenID` + `tokenHash` returns `X-Token` valid for ~24h.

This supports a BJ to Depoto and Depoto to BJ sync service.

## 7) Recommended Next Steps

1) Decide authority boundaries (transition phase)
- Depoto as availability authority is the lowest-friction model for fulfillment.

2) Obtain Depoto credentials and IDs
- Base URL
- Username/password
- Checkout ID
- Payment method IDs
- Depots assigned to checkout

3) Implement a small `depoto-sync` service (Docker)
- Endpoint for Depoto webhooks that enqueues events and returns 200 quickly
- Worker that processes events with retries and audit log
- BJ writes via BlueJet MCP or direct REST

4) Add BJ trigger
- Add a BJ UI button that calls the `depoto-sync` endpoint for a selected order
- Add automated trigger when prerequisites are satisfied

## 8) Where This Was Saved For Long-Term Reference

In this repo:

- BlueJet MCP: `tools/mcp/bluejet_mcp/`
- Depoto MCP: `tools/mcp/depoto_mcp/`
- Depoto spec: `ops/DEPOTO_LOGISTICS_INTEGRATION.md`

No secrets are committed.
