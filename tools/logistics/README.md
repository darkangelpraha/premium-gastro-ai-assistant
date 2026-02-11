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
  - Default is **safe**: `--mode draft` creates *unsent* orders and prints labels.
  - Use `--mode send` only when ready to actually send orders to Toptrans (TOPIS).
  - Tip: add `--dry-run` to validate inputs without calling TopTrans at all.
  - Useful options:
    - `--position 0..13` (start label position on A4)
    - `--limit 5` (process only first N shipments from input)
    - `--skip-price` (skip cost calculation, not recommended)

Environment:

- `TOPTRANS_USERNAME`
- `TOPTRANS_PASSWORD`
- Optional: `TOPTRANS_BASE_URL` (default `https://zp.toptrans.cz`)
- Recommended (needed for `order/price` unless `--skip-price`):
  - `TOPTRANS_LOADING_CITY`
  - `TOPTRANS_LOADING_ZIP`

Safety:

- Idempotent by `external_id` via `ops/_local/toptrans/toptrans_audit.jsonl` (avoids duplicates).
- Secrets are **not committed**. Store them locally (example): `ops/_local/toptrans/toptrans.env` with chmod 600.
- `--mode draft` stays inside ZP (unsent orders).

## BlueJet: Export Offer Recipient To TopTrans JSON

This tool reads a BlueJet offer (evidence `no=293`) and its shipping address (evidence `no=243`) and writes a TopTrans-compatible `shipments.json`.

Run:

- Script: `python3 tools/logistics/bluejet_export_toptrans.py --offer-code <code>`

Environment (BlueJet):

- `BLUEJET_BASE_URL`
- `BLUEJET_API_TOKEN_ID`
- `BLUEJET_API_TOKEN_HASH`

Optional:

- `--bluejet-env-file <path>` can be used to load the three values from a local `.env` file.
