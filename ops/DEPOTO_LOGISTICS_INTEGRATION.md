# Depoto Logistics Integration (BlueJet now, STP later)

## Scope

Premium Gastro currently runs BlueJet (BJ) plus a custom web stack. Shoptet Premium (STP) is being built to replace the custom web and a large part of BJ. Depoto is the warehouse/fulfillment system.

This document is a grounded, source-backed integration spec that can be implemented incrementally, with auditability and minimal operational risk.

## Verified Facts (2026-02-10)

Public sources:
- Depoto PHP client: `TomAtomCZ/depotoPhpClient`
- Depoto PHP client wiki pages:
  - "Napojeni / Import objednavek"
  - "Objednavky" (process statuses + paid gating)
  - "Udalosti" (webhooks)
  - "Dopravci" (carrier IDs)

Depoto API:
- Depoto communicates via GraphQL API.
- Authentication is OAuth2.
- Token endpoint: `POST /oauth/v2/token`.
- GraphQL endpoint: `POST /graphql` with `Authorization: Bearer <access_token>`.

Depoto can deliver webhooks:
- Webhooks are configured per checkout (sales point) via `updateCheckout(id, eventUrl)`.
- Webhook calls are expected to return in milliseconds.
- Best practice from Depoto: accept fast and process asynchronously from a queue; repeated 5XX can lead to webhook removal.

Order progression correctness:
- `paymentItems.isPaid` defaults to `true` when omitted.
- Depoto wiki explicitly warns: omitting `isPaid` for card or bank transfer orders can mark them as paid and push them into picking and shipping.
- Always send `isPaid` explicitly.

Carriers:
- Depoto uses stable carrier IDs (examples: `ppl`, `zasilkovna`, `dpd`, `gls`, `paletovka`, `personally`). Depoto expects carrier ID in `order.carrier`.

Tracking:
- Tracking codes are available on `order.packages.code` after process status becomes `dispatched`.
- Depoto fetches carrier tracking statuses daily (22:30) for packages sent up to 31 days back.

## Working Model (Lean and Safe)

Principle: pick one authority per domain.

Recommended transitional authority:
- Orders and customer communication: BJ (today), STP (later)
- Warehouse execution and availability: Depoto

This maps to Depoto wiki: `product.availability` is a primary event and they describe how to compute available quantity for an e-shop.

## Core Integration Flows

### Flow A: BJ -> Depoto (Order import for fulfillment)

Goal: Depoto receives fulfillment orders early enough for capacity planning, while avoiding premature picking.

1) Ensure Depoto prerequisites exist:
- Checkout configured with assigned depot(s) and payment methods
- Products created in Depoto (or created on-demand with a stable mapping)
- Supplier records created (if using Depoto purchase price tracking)

2) Idempotence strategy:
- Use `externalId` on Depoto order as the stable BJ order identifier.
- Before create, search in Depoto by `externalId` (via GraphQL query filters) and then either create or update.

3) Create order:
- Create customer and addresses (`createCustomer`, `createAddress`) when needed.
- Create Depoto order via `createOrder`.
- Always send:
  - `checkout` (Depoto checkout ID)
  - `carrier` (Depoto carrier ID)
  - `currency`
  - `items` with correct types (`product`, `shipping`, `payment`)
  - `paymentItems` with explicit `isPaid`
  - `externalId`

4) Prevent premature warehouse progression:
- Create order early for planning with `isPaid=false`.
- Later, after prerequisites are satisfied, update the order (`updateOrder`) and set `isPaid=true`.

5) Cancellation:
- Depoto wiki states reservations can be canceled only while order is in reservation state (`deleteReservation`).

### Flow B: Depoto -> BJ (Events: availability, status, tracking)

Goal: BJ stays consistent, customer updates are correct, and availability reflects Depoto.

1) Register Depoto event webhook URL:
- Configure per checkout in Depoto.
- Use `updateCheckout(id, eventUrl)`.

2) Event handling pattern:
- Receive webhook.
- Immediately store event in a local durable queue (type, entity id, created).
- Return `200` fast.
- A worker processes the queue with retries.

3) Events to enable:
- `product.availability`:
  - Fetch product details including `quantities`.
  - Compute quantities only for depots assigned to the checkout.
  - Update BJ product availability.
- `order.processStatus`:
  - On `dispatched`, fetch `order.packages.code` and write tracking into BJ.
  - Update BJ order state for internal visibility.
- `order.delete`:
  - Mark BJ order as canceled or revert planned logistics.

### Flow C: Stock receipts and procurement planning

Depoto assumes correct inventory. There are two viable models:

Model 1 (recommended): Depoto is inventory authority
- Goods receipts happen in Depoto.
- BJ reads availability from Depoto (via events or periodic sync).

Model 2: BJ is inventory authority
- Goods receipts happen in BJ.
- Depoto inventory is kept consistent by pushing inbound movements.

Depoto wiki shows a supported inbound movement operation:
- `createProductMovePack(type=in, moves=[...])`

Capacity planning requirement:
- Creating orders early (with `isPaid=false`) gives Depoto visibility of upcoming work without triggering picking.

## Implementation Plan (Incremental)

1) Establish Depoto credentials and IDs
- Base URL
- Username/password
- Checkout ID(s)
- Payment method IDs
- Depot IDs assigned to each checkout

2) Build a minimal Depoto Sync service
- HTTP endpoint for Depoto events
- Queue + worker
- Depoto GraphQL client
- BJ client (via BlueJet MCP or direct REST)
- Audit log (append-only)

3) Add BJ trigger
- Add a BJ UI action/button that calls the Depoto Sync service for the selected order.
- Add an automated trigger when the prerequisite step is satisfied.

4) Verify correctness in production-like staging
- Use Depoto GraphQL explorer to confirm schema and field semantics.
- Confirm how `isPaid` interacts with process statuses for each payment type.

## Depoto Questions (Draft for Depoto support/dev)

This is the checklist to confirm with Depoto before production rollout:
- Confirm field semantics for `vat` in `createOrder.items`.
- Confirm whether `createOrder` is accepted when stock is insufficient and how Depoto represents this.
- Confirm best practice for pre-announcement of future orders (planning visibility) without triggering picking.
- Confirm recommended event set for:
  - availability sync
  - order status sync
  - tracking
- Confirm rate limits, webhook retry behavior, and expected timeout.
- Confirm if STP integration exists and what it syncs compared to direct API integration.
