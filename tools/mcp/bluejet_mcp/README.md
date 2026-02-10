# BlueJet MCP (FastMCP)

Minimal MCP server for BlueJet CRM REST API, designed to run safely and stably in Docker.

## What This Is

- A small MCP server that:
  - Authenticates to BlueJet via `tokenID` + `tokenHash`
  - Caches the `X-Token` (refreshes once on 401)
  - Exposes one tool: `bluejet_request(...)`
- Safe by default:
  - `BLUEJET_READ_ONLY=1` blocks `POST/PUT/DELETE` to avoid accidental data changes.

## Required Environment Variables

- `BLUEJET_API_TOKEN_ID`
- `BLUEJET_API_TOKEN_HASH`

Optional:

- `BLUEJET_BASE_URL` (default: `https://czeco.bluejet.cz`)
- `BLUEJET_READ_ONLY` (default: `1`)
- `BLUEJET_TOKEN_TTL_SECONDS` (default: 23h)
- `LOG_LEVEL` (default: `INFO`)

## Running In Docker (HTTP MCP Endpoint)

This server supports a stable HTTP MCP endpoint:

- `MCP_TRANSPORT=http`
- `MCP_HOST=0.0.0.0`
- `MCP_PORT=8000`
- `MCP_PATH=/mcp/`

Example docker-compose (no secrets included):

```yaml
services:
  bluejet-mcp:
    build:
      context: .
    environment:
      MCP_TRANSPORT: http
      MCP_HOST: 0.0.0.0
      MCP_PORT: 8000
      MCP_PATH: /mcp/
      BLUEJET_BASE_URL: https://czeco.bluejet.cz
      BLUEJET_READ_ONLY: 1
      LOG_LEVEL: INFO
      BLUEJET_API_TOKEN_ID: ${BLUEJET_API_TOKEN_ID}
      BLUEJET_API_TOKEN_HASH: ${BLUEJET_API_TOKEN_HASH}
    ports:
      - "127.0.0.1:8741:8000"
    restart: unless-stopped
```

## Continue (VS Code) MCP Config

Continue supports URL-based MCP servers. Point it to:

- `http://127.0.0.1:8741/mcp/`

## Notes

- Logs are written to stderr to avoid breaking stdio MCP transport.
- HTTP endpoint may return `406` to a plain browser/curl GET; MCP clients use the correct headers/transport.

