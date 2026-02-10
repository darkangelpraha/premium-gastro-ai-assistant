# TopTrans Integration (avoid browser automation)

## Situation

TopTrans is currently used manually via web UI.

This can be automated safely without UI clicking, because TopTrans provides a documented HTTP API.

## Verified Facts (2026-02-10)

Public documentation:
- API reference: `https://zp.toptrans.cz/docs/api.html`
- Data entities: `https://zp.toptrans.cz/docs/data.html`

Auth:
- HTTP Basic auth.
- Uses the same username/password as the TopTrans ZP portal.

Base URL:
- `https://zp.toptrans.cz/api/{json|xml}/...`

Request:
- POST, with JSON body.

Useful endpoints (examples):
- `order/price` (pricing)
- `order/save` (create/update an order)
- `order/send` (submit an order)
- `order/search` (search)
- `order/print-list` (print docs)

## Why API beats Playwright

- More reliable (selectors and UI changes do not break it).
- Faster.
- Auditable (request/response logs).
- Safer to run automatically.

Playwright/Skyvern should be a fallback only if API access cannot be enabled.

## How this fits our stack

- This becomes one more connector next to BlueJet MCP and Depoto MCP.
- It can be triggered:
  - from BlueJet (button/action), or
  - from n8n, or
  - from the future STP integration layer.

## Next Steps

1) Locate TopTrans ZP credentials in 1Password and store them locally in a restricted env file.
2) Implement a minimal flow:
- BJ order -> map to TopTrans order payload -> `order/save` -> `order/send`.
3) Add a print/label step if needed:
- `order/print-unsent-labels` or `order/print-labels` depending on the workflow.

Implementation in this repo:
- `tools/mcp/toptrans_mcp/`
