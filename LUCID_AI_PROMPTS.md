# Lucid AI Diagramming Prompts for BlueJet Architecture
**For Shoptet Premium Meeting - 2026-01-13, 10:00**

## INSTRUCTIONS FOR USING LUCID AI:

1. Open Lucidchart → New Document
2. Click **AI** button (top right or sidebar)
3. Copy ENTIRE prompt below (including structure details)
4. Paste into Lucid AI
5. Click **Generate**
6. Review and refine

**TIP:** Start with high-level diagrams first, then drill down into details.

---

## 📋 PROMPT 1: Customer Journey Overview (Main Presentation)

```
Create a comprehensive customer journey flowchart for a B2B gastro equipment e-commerce business showing the complete order lifecycle from initial inquiry to payment closure.

STRUCTURE:
- Start: Customer inquiry (email OR webshop)
- Process stages: Quote → Order Confirmation → Consolidation → Supplier Order → Warehouse → Delivery → Invoice → Payment
- Decision points: Human approval (learning phase vs auto mode), MOQ threshold, warehouse selection, payment matching
- End: Order closed and exported to accounting

KEY COMPONENTS TO SHOW:
1. Email Classifier Agent (Missive + AI) receives customer inquiries
2. Quote Agent creates "Vydaná nabídka" in BlueJet CRM
3. Human approval checkpoint (learning phase) with reasoning display
4. Order Consolidation Agent (CRITICAL - highlight this):
   - Groups orders by supplier
   - Checks MOQ/MOV requirements
   - 30-day maximum wait window
   - Force order if deadline reached
5. Warehouse logic (3 types):
   - Hlavní (main) - reserved for customers, hidden from web
   - Showroom - available for loans/demos
   - E-shop - publicly visible on website
6. Document Generation Agent creates:
   - Příjemka (goods receipt)
   - Výdejka (goods dispatch) + stock validation
   - Dodací list (delivery note)
   - Faktura (invoice) with deposit handling
7. Payment Matching Agent:
   - GoPay API integration
   - RB/Citfin email parsing
   - Auto-match by variabilní symbol
   - Automated reminders (Day 7, 14, 30)

VISUAL STYLE:
- Use swim lanes for different agents
- Color code decision points (yellow) and critical agents (orange)
- Show data flow with labeled arrows
- Include timing annotations (e.g., "Max 30 days", "Every 5 minutes")
- Add icons for email, database, warehouse, payment

INTEGRATION POINTS:
- BlueJet CRM API (czeco.bluejet.cz)
- Shoptet Premium webhooks (order:create, inventory:change)
- N8n workflow orchestration
- Supabase for state management

Make the diagram executive-ready for presenting to Shoptet Premium technical team.
```

---

## 📦 PROMPT 2: Order Consolidation Agent Logic (CRITICAL DETAIL)

```
Create a detailed decision flowchart for an Order Consolidation Agent that manages B2B orders for 40+ suppliers with MOQ/MOV requirements.

BUSINESS RULES:
1. Orders start as confirmed quotes ("Nabídka potvrzena")
2. Agent groups orders by supplier
3. Each supplier has unique MOQ/MOV value
4. Maximum wait time: 30 days from first confirmed quote
5. If MOQ reached before 30 days: Generate supplier order immediately
6. If 30 days reached without MOQ: Force order anyway (accept economic loss)
7. Days 21-29: Alert operator about approaching deadline

TECHNICAL FLOW:
START:
- Trigger: New quote confirmed (stav_potvrzení = "Ano")

STEP 1: Query Supabase
- Retrieve all confirmed quotes with status = "Čeká"
- Group by supplier_id

STEP 2: For each supplier
- Calculate total order value: Σ(all quotes for this supplier)
- Load supplier metadata (MOQ, lead time, contact)
- Check waiting queue: days_waiting field

STEP 3: Decision logic
- IF total_value >= MOQ AND days_waiting <= 30:
  → Generate "Sumární vydaná objednávka" (BlueJet obj 356)
  → Send email to supplier
  → Update waiting_queue status = "dispatched"
  → Notify all customers: "Order placed with supplier, ETA: {supplier_lead_time}"

- ELSE IF days_waiting >= 21 AND days_waiting < 30:
  → Alert operator: "Approaching deadline for {supplier_name}"
  → Continue waiting

- ELSE IF days_waiting >= 30:
  → Force generate order (flag: below_moq = true)
  → Alert operator: "Forced order below MOQ for {supplier_name}"
  → Send email to supplier
  → Update waiting_queue

- ELSE (days_waiting < 21 AND total_value < MOQ):
  → Add to waiting_queue OR update existing
  → Increment days_waiting counter
  → Schedule next check (N8n: daily 08:00)

STEP 4: Loop
- Process next supplier
- Repeat until all suppliers checked

END:
- Return summary: {orders_generated}, {orders_waiting}, {alerts_sent}

DATA STRUCTURES:
- waiting_queue table (Supabase):
  - supplier_id (FK)
  - customer_ids (array)
  - quote_ids (array)
  - total_value (decimal)
  - days_waiting (integer)
  - first_quote_date (timestamp)
  - status (pending|dispatched|forced)

- BlueJet API endpoints:
  - POST /api/v1/data?no=356 (create order)
  - PUT /api/v1/data (update quote status)
  - GET /api/v1/data?no=217 (product lookup for deduplication)

VISUAL REQUIREMENTS:
- Show decision tree clearly
- Highlight critical paths (MOQ reached, 30-day deadline)
- Use color coding: Green (OK), Yellow (warning), Red (forced)
- Include timing annotations
- Show database interactions
- Display email/notification triggers

Make this diagram technical enough for developers but understandable for business stakeholders.
```

---

## 🏭 PROMPT 3: Warehouse Logic & Visibility Control

```
Create a flowchart showing warehouse selection logic and inventory visibility control for a 3-warehouse system in a B2B gastro e-commerce platform.

WAREHOUSE TYPES:
1. **SKLAD HLAVNÍ** (Main Warehouse)
   - Purpose: In/Out only for customer orders
   - Visibility: MUST NOT appear on public website
   - Reason: Reserved for specific customers, prevent accidental public orders
   - Stock sync: BlueJet only (no Shoptet sync)

2. **SKLAD SHOWROOM** (Showroom Warehouse)
   - Purpose: Demo equipment available for customer loans
   - Visibility: Special "Available for loan" catalog
   - Tracking: Loan conditions, return dates, deposit requirements
   - Stock sync: Both BlueJet and Shoptet (separate loan catalog)

3. **SKLAD E-SHOP** (E-shop Warehouse)
   - Purpose: Publicly available products for immediate sale
   - Visibility: Fully visible on Shoptet Premium website
   - Stock sync: Real-time sync via inventory:change webhook
   - Automatic publish: Yes (as soon as stocked)

PROCESS FLOW:
START: Goods arrived from supplier

STEP 1: Determine destination
- Check order source:
  - IF order_type = "customer_specific" → Route to HLAVNÍ
  - IF order_type = "showroom_demo" → Route to SHOWROOM
  - IF order_type = "general_stock" → Route to E-SHOP

STEP 2: Generate příjemka (goods receipt)
- Select warehouse from dropdown
- IF multi-warehouse split needed:
  - Generate separate příjemka for each warehouse
  - Delete items not belonging to that warehouse
  - Confirm each příjemka separately
- ELSE:
  - Confirm single příjemka

STEP 3: Update skladová karta (stock card)
- Increment quantity in selected warehouse
- Set visibility flags:
  - HLAVNÍ: {visible_on_web: false, reserved: true, customer_id: {id}}
  - SHOWROOM: {visible_on_web: true, loan_available: true}
  - E-SHOP: {visible_on_web: true, published: true}

STEP 4: Sync to Shoptet Premium
- IF warehouse = E-SHOP:
  - PATCH /api/products/{id}/stock (update quantity)
  - POST inventory:change webhook triggers
  - Product becomes visible on website immediately
- IF warehouse = SHOWROOM:
  - Sync to special loan catalog (custom implementation)
- IF warehouse = HLAVNÍ:
  - NO sync to Shoptet (keep hidden)

STEP 5: Stock validation (before dispatch)
- Calculate: available = (quantity_on_hand - reserved_quantity)
- IF available < requested:
  - BLOCK výdejka generation
  - Alert operator: "Insufficient stock in {warehouse}"
  - Suggest alternatives or restock
- ELSE:
  - Allow výdejka generation

CRITICAL SCENARIOS:
1. **Customer tries to order from Hlavní:** BLOCKED by visibility=false
2. **Stock split across warehouses:** Generate multiple příjemky
3. **Insufficient stock:** Alert before dispatch, not at order time
4. **Showroom item returned:** Update stock, notify if now available

VISUAL REQUIREMENTS:
- Use 3 distinct swim lanes for warehouses
- Color code: Orange (Hlavní), Green (Showroom), Blue (E-shop)
- Show visibility toggle prominently
- Include Shoptet sync flows
- Display error handling paths
- Add icons for warehouse, web visibility, reserved items

Include decision diamonds for warehouse selection and stock validation.
```

---

## 💳 PROMPT 4: Payment Matching Agent

```
Create a flowchart for an automated Payment Matching Agent that processes payments from 3 sources (GoPay API, Raiffeisenbank email, Citfin email) and automatically matches them to invoices.

PAYMENT SOURCES:
1. **GoPay API** (Online payments)
   - Method: GET /payments endpoint (poll daily)
   - Match field: Transaction ID → Variabilní symbol (VS)
   - Confidence: 100% (API data)

2. **Raiffeisenbank Email** (Bank transfer confirmations)
   - Method: Email parsing (IMAP + regex)
   - Extract: VS, amount, date, sender
   - Confidence: 85-95% (depends on email format)

3. **Citfin Email** (Bank transfer confirmations)
   - Method: Email parsing (IMAP + regex)
   - Extract: VS, amount, date, sender
   - Confidence: 85-95% (depends on email format)

MATCHING LOGIC:
STEP 1: Collect payments (daily 08:00 + real-time for GoPay)
- GoPay: API call
- RB/Citfin: Parse unread emails in inbox

STEP 2: For each payment:
- Extract variabilní symbol (VS)
- Extract amount (CZK)
- Extract payment date

STEP 3: Match to invoice
- Query BlueJet: faktury with číslo_faktury = VS
- IF match found:
  - Check amount:
    - IF amount == invoice_total: FULL PAYMENT
    - IF amount < invoice_total: PARTIAL PAYMENT (deposit)
    - IF amount > invoice_total: OVERPAYMENT (human review)
  - IF confidence >= 90%: Auto-process
  - IF confidence < 90%: Flag for human review
- IF no match found:
  - UNMATCHED PAYMENT (human review)
  - Store in unmatched_payments table
  - Email operator with payment details

STEP 4: Process matched payments
- FULL PAYMENT:
  - Generate "Doklad o přijaté platbě" (payment receipt)
  - Update faktura: stav = "Uhrazena"
  - Email customer: Payment confirmation
  - Stop monitoring this invoice

- PARTIAL PAYMENT:
  - Record as záloha (deposit)
  - Update faktura: stav = "Částečně uhrazena", částka_uhrazena += amount
  - Email customer: Deposit confirmation
  - Continue monitoring for remaining amount

- OVERPAYMENT:
  - Flag for human review
  - Options: Refund OR apply to next invoice
  - Operator decides

- UNMATCHED:
  - Email operator with details
  - Operator manually matches or contacts customer

STEP 5: Overdue logic (if no payment received)
- Check invoice due date (datum_splatnosti)
- IF today > due_date + 7 days:
  - Send 1st reminder (auto email)
- IF today > due_date + 14 days:
  - Send 2nd reminder (auto email)
- IF today > due_date + 30 days:
  - Escalate to collection (inkasní řízení)
  - Notify management
  - Human takes over

ERROR HANDLING:
- Email parsing fails: Retry 3x, then human review
- API timeout: Exponential backoff (2s, 4s, 8s)
- Duplicate payment: Check event_id (idempotency)
- Wrong amount: Always flag for review

VISUAL REQUIREMENTS:
- Show 3 payment source lanes
- Display matching algorithm (VS lookup)
- Color code outcomes: Green (matched), Yellow (partial), Red (unmatched)
- Include timing (daily schedule, real-time triggers)
- Show email/notification flows
- Display human review escalation points

Add sequence numbers to show execution order.
```

---

## 🎓 PROMPT 5: Learning Loop Mechanism (Human → Auto)

```
Create a state diagram showing the progressive autonomy mechanism where an AI agent learns from human decisions and gradually transitions from supervised to autonomous operation.

PHASES:
1. **LEARNING PHASE** (Weeks 1-4)
   - ALL actions require human approval
   - Agent proposes action + reasoning
   - Human reviews and decides (approve/reject/modify)
   - System logs: decision, reasoning, outcome
   - Confidence model trains on decisions

2. **TRANSITION PHASE** (Weeks 5-8)
   - Mixed mode: High confidence → auto, Low confidence → human
   - Confidence threshold: 80%
   - Agent calculates confidence score for each action
   - IF score >= 80%: Execute automatically
   - IF score < 80%: Request human approval
   - Continue learning from both auto and manual decisions

3. **AUTONOMOUS MODE** (Week 9+)
   - 95%+ decisions fully autonomous
   - Only escalate edge cases or critical actions
   - Continuous monitoring for anomalies
   - IF error rate > 5%: Revert to Transition Phase
   - IF error rate > 10%: Revert to Learning Phase

CONFIDENCE SCORING FACTORS:
- Historical accuracy: (correct_decisions / total_decisions)
- Pattern similarity: Cosine similarity to known good decisions
- Context complexity: Simple scenarios score higher
- Data completeness: Missing fields reduce confidence
- Time-based decay: Recent decisions weighted more

TRANSITION CRITERIA:
- Learning → Transition:
  - Minimum 50 human-approved decisions
  - Accuracy >= 60%
  - At least 10 unique scenario types

- Transition → Autonomous:
  - Minimum 200 total decisions
  - Accuracy >= 90%
  - Auto-execution success rate >= 95%
  - No critical errors in last 30 days

EXAMPLE SCENARIOS:
- Quote pricing: Start at 40% confidence → reach 95% after 100 decisions
- Order consolidation: Start at 60% confidence → reach 92% after 150 decisions
- Payment matching: Start at 85% confidence → reach 98% after 50 decisions

VISUAL REQUIREMENTS:
- Use state diagram format with clear phase boundaries
- Show transition arrows with criteria labels
- Display confidence score calculation
- Include rollback paths (error detection → previous phase)
- Color code phases: Blue (learning), Yellow (transition), Green (autonomous)
- Add annotations for timing (weeks) and decision counts

Include feedback loops showing how errors trigger phase regression.
```

---

## 🔗 PROMPT 6: System Integration Architecture (Technical)

```
Create a C4-style context diagram showing how the BlueJet Multi-Agent System integrates with existing infrastructure and external services.

CORE SYSTEM (Center):
- BlueJet Agent Network (6 specialized agents)

INTERNAL COMPONENTS:
1. **Email Classifier Agent**
   - Receives: Missive emails
   - Processes: Urgency detection, VIP identification
   - Outputs: Routed conversations

2. **Quote Agent**
   - Receives: Customer inquiries
   - Processes: Price calculation, volume discounts
   - Outputs: Vydaná nabídka (BlueJet obj 232)

3. **Order Consolidation Agent** (CRITICAL)
   - Receives: Confirmed quotes
   - Processes: MOQ checking, 30-day window, grouping
   - Outputs: Sumární objednávka (BlueJet obj 356)

4. **Document Generation Agent**
   - Receives: Workflow triggers
   - Processes: Příjemka, Výdejka, Dodací list, Faktura
   - Outputs: BlueJet documents + PDFs

5. **Payment Matching Agent**
   - Receives: GoPay webhooks, bank emails
   - Processes: VS matching, amount validation
   - Outputs: Payment confirmations, reminders

6. **Supplier Communication Agent**
   - Receives: Generated orders
   - Processes: Email templates, delivery tracking
   - Outputs: Supplier emails, ETA updates

EXTERNAL SYSTEMS:
1. **BlueJet CRM/ERP** (czeco.bluejet.cz)
   - Connection: REST API (TokenID + TokenHash)
   - Operations: CRUD on all objects (220+)
   - Rate limits: No official limit documented

2. **Shoptet Premium** (E-commerce)
   - Connection: Private API Token (32-char)
   - Operations: Products, Orders, Inventory
   - Webhooks: order:create, inventory:change, customer:*
   - Rate limits: 200 drops/cycle, 10/sec refill

3. **Missive Hub** (Email orchestration)
   - Connection: API Token
   - Operations: Conversation routing, auto-responses
   - Real-time: Webhook on new emails

4. **Supabase** (PostgreSQL + Real-time)
   - Connection: API Key + JWT
   - Operations: State management, waiting queues
   - Tables: waiting_orders, payment_events, agent_logs

5. **N8n** (Workflow orchestration)
   - Connection: Local (http://127.0.0.1:5678)
   - Operations: Schedule triggers, webhook listeners
   - Workflows: 11 total (4 Phase 6 + 7 BlueJet)

6. **GoPay** (Payment gateway)
   - Connection: Merchant ID + API Secret
   - Operations: GET /payments, webhook callbacks
   - Real-time: Payment confirmations

7. **RB + Citfin** (Banking)
   - Connection: Email parsing (IMAP)
   - Operations: Read confirmations, extract data
   - Frequency: Hourly email check

8. **Helios/Pohoda** (Accounting)
   - Connection: CSV export (future: API)
   - Operations: One-way export from BlueJet
   - Frequency: End of day/month

ACTORS:
- Customer (B2B gastro businesses)
- Operator (Human supervisor during learning phase)
- Supplier (40+ vendors)
- Accountant (Uses Helios/Pohoda)

DATA FLOWS (Show with labeled arrows):
- Customer → Shoptet → Webhook → Quote Agent → BlueJet
- BlueJet → Consolidation Agent → Supabase → N8n → Email
- GoPay → Payment Agent → BlueJet → Customer notification
- BlueJet → Shoptet → Product sync (daily + webhooks)
- BlueJet → Helios → Accounting export (daily)

VISUAL REQUIREMENTS:
- Use C4 notation (rectangles for systems, stick figures for people)
- Show system boundaries clearly
- Use different colors for internal vs external systems
- Label all connections with protocol (REST, Webhook, Email, etc.)
- Include authentication methods in labels
- Display data flow direction with arrows
- Add annotations for critical integration points

Make this diagram suitable for technical stakeholders and integration planning.
```

---

## 🎯 PROMPT 7: Shoptet ↔ BlueJet Data Sync (For Meeting)

```
Create a sequence diagram showing real-time bidirectional data synchronization between Shoptet Premium e-commerce platform and BlueJet CRM/ERP system.

PARTICIPANTS:
1. Customer (B2B buyer)
2. Shoptet Premium (E-commerce storefront)
3. Webhook Listener (N8n endpoint)
4. N8n Orchestrator (Workflow engine)
5. BlueJet Agent (Business logic)
6. BlueJet API (czeco.bluejet.cz)
7. Supabase (State storage)

PRIMARY FLOW: Customer Places Order
STEP 1: Customer → Shoptet
- Action: Place order on website
- Shoptet creates order internally
- Shoptet sends confirmation email to customer

STEP 2: Shoptet → Webhook Listener
- Trigger: order:create webhook
- Payload: {orderId, customerId, items[], total, status}
- Critical: Response < 4 seconds (Shoptet requirement)

STEP 3: Webhook Listener
- Verify HMAC-SHA1 signature
- Store event_id in Supabase (idempotency)
- Return HTTP 200 to Shoptet (FAST)
- Queue async job for processing

STEP 4: Webhook → N8n → BlueJet Agent
- N8n retrieves full order details: GET /api/orders/{orderId}
- Transform data: Shoptet schema → BlueJet schema
- Pass to BlueJet Agent for processing

STEP 5: BlueJet Agent
- Check if customer exists (query by email)
- IF not exists: Create customer (POST obj 222)
- Map products to BlueJet catalog
- Create "Vydaná nabídka" (POST obj 232)
- Set stav_potvrzení = "Ano" (auto-confirm from web)

STEP 6: BlueJet Agent → Consolidation Trigger
- Query Supabase: waiting_orders GROUP BY supplier
- Check MOQ thresholds
- IF MOQ reached: Generate sumární objednávka
- ELSE: Add to waiting queue

STEP 7: Order Processing
- BlueJet creates supplier order
- Agent sends email to supplier
- Customer receives status update (via Shoptet)

REVERSE FLOW: BlueJet Inventory Update
STEP 1: BlueJet → Stock Change
- Goods arrive and are stocked in E-shop warehouse
- Operator confirms příjemka
- Stock card updated: quantity += received_amount

STEP 2: BlueJet → N8n Trigger
- N8n workflow polls BlueJet: GET skladové karty (every 5 min)
- Detects quantity change since last check

STEP 3: N8n → Shoptet
- PATCH /api/products/{id}/stock
- Update inventory quantity
- Shoptet sends inventory:change webhook (acknowledgment)

STEP 4: Shoptet → Product Page
- Stock quantity updated on website
- Product becomes available for purchase (if was out of stock)
- Customer sees updated availability

ERROR SCENARIOS:
1. **Webhook timeout (>4 sec):**
   - Shoptet retries after 15 min
   - N8n detects duplicate via event_id (skip processing)

2. **Product not found in BlueJet:**
   - Agent flags for human review
   - Email operator with product details
   - Order paused until resolved

3. **Customer duplicate:**
   - Match by email (fuzzy matching)
   - IF confidence > 90%: Link to existing
   - ELSE: Human review

4. **Insufficient stock:**
   - BlueJet validates before výdejka generation
   - IF stock < order: Alert operator
   - Shoptet order status NOT updated until stock available

TIMING ANNOTATIONS:
- Webhook response: < 4 seconds (critical)
- Async processing: 5-30 seconds
- Stock sync: Every 5 minutes (scheduled)
- Full product sync: Daily 08:00
- Order status updates: Real-time (webhooks)

VISUAL REQUIREMENTS:
- Use sequence diagram format with numbered steps
- Show activation boxes for processing time
- Display timing constraints prominently (< 4 sec)
- Include alt/opt blocks for conditional flows
- Color code: Blue (sync), Green (async), Red (error)
- Add notes for critical requirements
- Show retry logic for failed requests

Include webhook signature verification step (security).
```

---

## 📝 USAGE TIPS:

### For Best Results:
1. **Start simple:** Use Prompt 1 first (customer journey overview)
2. **Then drill down:** Use Prompts 2-6 for detailed sub-processes
3. **Iterate:** Generate → Review → Refine prompt → Regenerate
4. **Combine:** Link diagrams together using page references

### Lucid AI Best Practices:
- Be specific about diagram type (flowchart, sequence, state, C4)
- Include exact data field names for accuracy
- Specify visual style (colors, icons, swim lanes)
- Mention if for executives vs developers
- Add timing/quantity annotations for context

### For Shoptet Meeting:
- **MUST SHOW:** Prompt 1 (overview) + Prompt 7 (Shoptet sync)
- **NICE TO HAVE:** Prompt 2 (consolidation logic) + Prompt 3 (warehouses)
- **PRINT:** Prompt 1 + 7 as handouts (11x17 paper for readability)

---

**All prompts tested for Lucid AI compatibility.**
**Adjust detail level based on audience technical expertise.**
**Use generated diagrams as starting point - manual refinement recommended.**
