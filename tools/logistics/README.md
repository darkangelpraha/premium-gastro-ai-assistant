# Logistics Tools

## TopTrans: Create Labels From JSON

This tool calls the official TopTrans ZP API and generates label PDFs.

Input format (JSON):

- Root object with key `shipments` (list)
- Each shipment requires:
  - `external_id` (string)
  - `discharge` (partner object)
  - `kg` (number)

Optional:
- `pack_id` (int) and `pack_quantity` (int)
- `term_id` (int)
- `discharge_aviso` (bool)
- `note_discharge` (string)
- `label` (string)

Partner schema (discharge):

- `name` (required)
- `address.city` (required)
- `address.street`, `address.zip`, `email`, `phone` (recommended)

Run:

- Script: `python3 tools/logistics/toptrans_labels.py --input <file.json>`

Environment:

- `TOPTRANS_USERNAME`
- `TOPTRANS_PASSWORD`
- Optional: `TOPTRANS_BASE_URL` (default `https://zp.toptrans.cz`)

Safety:

- Idempotent by `external_id` via `ops/_local/toptrans/toptrans_audit.jsonl`.
- No secrets are written to disk.
