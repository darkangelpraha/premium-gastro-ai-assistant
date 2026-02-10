# Logistics Automation Architecture (BlueJet -> TopTrans)

## Goal
Generate TopTrans shipping labels (PDF) from a BlueJet offer with minimal manual work.

## Components
- BlueJet API
  - Auth: POST /api/v1/users/authenticate -> returns { token, succeeded, message }
  - Data: GET /api/v1/Data?no=...&limit=...&offset=...&condition=... -> returns { no, recordsCount, rows }
- TopTrans ZP API (JSON)
  - Base: https://zp.toptrans.cz/api/json/.../
  - Used endpoints:
    - register/pack (read-only check + pack id/name mapping)
    - order/save (creates a draft order)
    - order/send (submits and returns label PDF payload)

## Local Tools (this repo)
- tools/logistics/bluejet_export_toptrans.py
  - Input: BlueJet offer code (e.g. 52/2026)
  - Reads:
    - Offer evidence no=293 by condition kodnabidky|=|<offer_code>
    - Shipping address evidence no=243 by condition addressid|=|<guid> (from prijemcezboziadsupl)
    - Customer/company evidence no=225 by condition customerid|=|<guid> (for phone/email/ICO/DIC)
  - Output: a TopTrans-compatible JSON file with shipments[]

- tools/logistics/toptrans_labels.py
  - Input: the JSON file produced by the exporter
  - Behavior:
    - --dry-run validates and prints what would be sent
    - live run:
      - calls order/save for each shipment
      - calls order/send for the batch
      - decodes returned base64 PDFs into ops/_local/toptrans/out/*.pdf
  - Idempotence:
    - Writes ops/_local/toptrans/toptrans_audit.jsonl
    - Skips shipments whose external_id already has an event=sent entry

## Secrets and Hygiene
- BlueJet API creds
  - Source: a local .env file (not committed)
- TopTrans creds
  - Source: 1Password
  - Materialized locally into ops/_local/toptrans/toptrans.env (gitignored, chmod 600)
- All generated artifacts live under ops/_local/ (gitignored)

## Operational Notes
- This is API-first (no browser automation). It is faster and more reliable than UI clicking.
- First live run should be done on a known safe offer code, to avoid creating unintended shipping orders.
