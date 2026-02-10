# Depoto MCP Server

MCP server that exposes Depoto GraphQL over FastMCP.

## Features

- OAuth2 token handling with caching and automatic refresh.
- HTTP transport mode for stable localhost MCP (like BlueJet MCP).
- Safe-by-default: mutations are blocked unless `DEPOTO_READ_ONLY=0`.

## Environment

Required:
- `DEPOTO_BASE_URL`
- `DEPOTO_USERNAME`
- `DEPOTO_PASSWORD`

Optional:
- `DEPOTO_CLIENT_ID`
- `DEPOTO_CLIENT_SECRET`
- `DEPOTO_READ_ONLY` (`1` default)
- `MCP_TRANSPORT` (`http` or `stdio`)
- `MCP_HOST` (`0.0.0.0`)
- `MCP_PORT` (`8000`)
- `MCP_PATH` (`/mcp/`)

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
