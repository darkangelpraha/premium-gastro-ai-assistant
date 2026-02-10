# TopTrans MCP Server (ZP API)

MCP server that wraps the TopTrans ZP API.

Why this exists: TopTrans has a documented HTTP API, so we can avoid fragile browser automation for most workflows.

## Verified API Docs

- `https://zp.toptrans.cz/docs/api.html`
- `https://zp.toptrans.cz/docs/data.html`

Key points:
- Authentication: HTTP Basic auth (same credentials as the ZP portal).
- Base: `https://zp.toptrans.cz/api/{json|xml}/...`
- POST requests with JSON payload.

## Environment

Required:
- `TOPTRANS_USERNAME`
- `TOPTRANS_PASSWORD`

Optional:
- `TOPTRANS_BASE_URL` (default `https://zp.toptrans.cz`)
- `TOPTRANS_FORMAT` (`json` default)
- `TOPTRANS_READ_ONLY` (`1` default)
- `MCP_TRANSPORT` (`http` or `stdio`)
- `MCP_HOST` (`0.0.0.0`)
- `MCP_PORT` (`8000`)
- `MCP_PATH` (`/mcp/`)

## Tool

- `toptrans_call(path, payload?, fmt?)`

Examples:

- Price estimate:
  - `path="order/price"`
- Save an order (mutating):
  - `path="order/save"` with `TOPTRANS_READ_ONLY=0`
- Send an order (mutating):
  - `path="order/send"` with `TOPTRANS_READ_ONLY=0`

## Safety

- Mutating methods are blocked by default (`TOPTRANS_READ_ONLY=1`).
- Prefer API over browser automation. Keep Playwright only as a fallback if API access is not available.
