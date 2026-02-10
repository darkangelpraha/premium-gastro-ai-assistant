# Depoto MCP Server

MCP server that exposes Depoto GraphQL over FastMCP.

## Features

- OAuth2 token handling with caching and automatic refresh on 401.
- HTTP transport mode for stable localhost MCP (like BlueJet MCP).
- Safe-by-default: mutations are blocked unless `DEPOTO_READ_ONLY=0`.
- No secrets in git. Credentials are only via environment variables.

## Environment

Required:
- `DEPOTO_BASE_URL`
- `DEPOTO_USERNAME`
- `DEPOTO_PASSWORD`
- `DEPOTO_CLIENT_ID`
- `DEPOTO_CLIENT_SECRET`

Optional:
- `DEPOTO_READ_ONLY` (default `1`)
- `MCP_TRANSPORT` (`http` or `stdio`)
- `MCP_HOST` (default `0.0.0.0`)
- `MCP_PORT` (default `8000`)
- `MCP_PATH` (default `/mcp/`)

## Smoke Test (Read-Only)

This validates:
- OAuth works
- GraphQL endpoint works
- Minimal query works

```bash
cd tools/mcp/depoto_mcp
python3 smoke_test_readonly.py
```

## Run (local)

```bash
cd tools/mcp/depoto_mcp
python3 server.py
```

## Tool

- `depoto_graphql(query, variables?, operation_name?)`

Example query (read-only):

```graphql
query Ping {
  __typename
}
```
