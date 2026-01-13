# Premium Gastro - Customer Journey & BlueJet Workflow
**Prepared for: Shoptet Premium Integration Meeting**
**Date:** 2026-01-13, 10:00
**Purpose:** Technical integration specification for Custom Web → Shoptet Premium migration

---

## 🎯 EXECUTIVE SUMMARY

Premium Gastro operates a **project-based B2B gastro equipment business** with 40+ suppliers and 40,000+ product portfolio. The business model focuses on:

- **Minimal inventory** (only showroom + e-shop items stocked)
- **Project consolidation** for economic viability (MOQ/MOV requirements)
- **Multi-supplier orders** per customer (consolidated delivery within 30 days)
- **BlueJet CRM/ERP** as source of truth for all business logic

### Key Business Constraints:
✅ **Order starts as "Vydaná nabídka" (Quote)** - NOT direct purchase
✅ **Consolidation window:** Max 30 days from first confirmed quote
✅ **3 Warehouses:** Main (in/out), Showroom (loans), E-shop (public sales)
✅ **Payment methods:** GoPay, Raiffeisenbank, Citfin (email confirmations)

---

## 🛒 COMPLETE CUSTOMER JOURNEY

### **Stage 1: Initial Inquiry**

```
Customer Action          System Response                    BlueJet State
─────────────────────────────────────────────────────────────────────────
📧 Email inquiry         → Email Classifier Agent          Missive: Routed
   OR                      (Missive + AI analysis)
🌐 Webshop browse        → Product catalog visible         N/A

🔍 Product selection     → Real-time price calculation     N/A
   (10-50 items typical)   (Ceníky + objemové zvýhodnění)

📤 Request quote         → Auto-generate nabídka           📋 VYDANÁ NABÍDKA
   (webshop form)          (BlueJet API: obj 232)            └─ stav: "Rozpracovaná"
```

**Critical Integration Point:**
- **Shoptet → BlueJet:** Webshop quote request creates "Vydaná nabídka" automatically
- **Human approval (learning phase):** Agent proposes quote → Human reviews → Sends
- **Auto mode (future):** Learned confidence thresholds = auto-send

---

### **Stage 2: Quote Generation & Approval**

```
System Process              Decision Logic                   BlueJet Update
───────────────────────────────────────────────────────────────────────────
📋 Quote Agent              Check conditions:               Update stav:
   receives request         ├─ Customer segment (VIP?)       "Rozpracovaná"
                           ├─ Volume discount applicable?
                           ├─ Supplier availability
                           └─ Delivery time estimate

🤖 AI drafts quote          Calculate pricing:              Generate items
                           ├─ Base price (Ceník)
                           ├─ Volume discount (5-15%)
                           ├─ Supplier MOQ penalties
                           └─ Delivery cost allocation

👤 Human review             Learning phase:                 Update stav:
   (approval point)         ├─ Review AI reasoning           "Odeslána"
                           ├─ Adjust if needed
                           └─ Approve or reject

📧 Send to customer         Email w/ PDF attachment         stav_potvrzení:
                           + link to confirm online         "Čeká"
```

**Shoptet Integration:**
- Quote sent via **Shoptet email templates** (branded)
- Customer confirms via **Shoptet order confirmation page**
- Status update: `stav_potvrzení: "Ano"` → Triggers consolidation

---

### **Stage 3: Order Consolidation (CRITICAL AGENT)**

```
Trigger Event              Consolidation Logic              Action Taken
─────────────────────────────────────────────────────────────────────────
✅ Quote confirmed         Consolidation Agent starts:      Query Supabase:
   (stav_potvrzení: "Ano")  ├─ Group by dodavatel (supplier)  waiting_orders
                           ├─ Calculate total value
                           ├─ Check MOQ/MOV per supplier
                           └─ Evaluate delivery economics

🔢 Aggregation              For each supplier:              Decision tree:
   (multiple customers)     Total Value ≥ MOQ?
                           ├─ YES → Generate order
                           └─ NO  → Add to queue (30-day max)

⏰ Daily check              Waiting queue monitor:          If in queue:
   (N8n scheduled)          Days waiting: 1-30?             ├─ Day 1-20: Wait
                           ├─ Approaching 30 days?          ├─ Day 21-29: Alert
                           └─ Deadline passed?              └─ Day 30: Force order

📦 Generate sumární         Create consolidated order:      📄 SUMÁRNÍ VYDANÁ
   objednávka dodavateli    ├─ Multiple customers             OBJEDNÁVKA
                           ├─ Single supplier                └─ stav: "Vytvořena"
                           └─ Combined items (deduplicated)
```

**Example Consolidation:**

| Customer | Items | Supplier | Value | Days Waiting | Action |
|----------|-------|----------|-------|--------------|--------|
| Restaurant A | 15 pcs | Dodavatel X | 45,000 CZK | Day 5 | ⏳ Queue |
| Hotel B | 8 pcs | Dodavatel X | 22,000 CZK | Day 12 | ⏳ Queue |
| Café C | 20 pcs | Dodavatel X | 58,000 CZK | Day 3 | ⏳ Queue |
| **TOTAL** | **43 pcs** | **Dodavatel X** | **125,000 CZK** | **Day 12** | ✅ **MOQ reached → ORDER** |

**Shoptet Integration:**
- Customer sees **estimated delivery: 1-30 days** on quote
- Real-time updates via **Shoptet order status tracking**
- Email notifications when order is **placed with supplier**

---

### **Stage 4: Supplier Order & Delivery**

```
Process Step               System Action                    BlueJet State
─────────────────────────────────────────────────────────────────────────
📧 Send to supplier        Supplier Comm Agent:            Update stav:
                          ├─ Generate PO email             "Odeslána"
                          ├─ Attach sumární objednávka
                          └─ Request delivery confirmation

📬 Supplier confirms       Email Parser Agent:             Update stav:
                          ├─ Extract delivery date         "Potvrzena"
                          ├─ Parse expected ETA            └─ Add ETA metadata
                          └─ Notify customers

🚚 Goods arrive            Warehouse notification:         🏭 PŘÍJEMKA
                          ├─ Generate příjemka             └─ sklad: [select]
                          ├─ Select warehouse:
                          │  ├─ Hlavní (customer orders)
                          │  ├─ Showroom (loans)
                          │  └─ E-shop (public sales)
                          └─ Confirm receipt

📦 Stock in                Document Agent:                 Confirm příjemka
                          ├─ Update skladová karta         └─ stav: "Naskladněno"
                          ├─ Validate quantities
                          └─ Check against objednávka
```

**Warehouse Selection Logic:**

| Destination | Warehouse | Visibility | BlueJet Flag |
|-------------|-----------|------------|--------------|
| Customer order (specific) | **Hlavní** | ❌ NOT on web | `reserved: true` |
| Showroom demos | **Showroom** | ✅ Loan catalog | `loan_available: true` |
| General sales | **E-shop** | ✅ Public web | `published: true` |

**Shoptet Integration:**
- Stock updates sync to **Shoptet inventory** (real-time webhook)
- E-shop items become **visible on Shoptet store**
- Customer-reserved items **hidden from web** (API flag)

---

### **Stage 5: Customer Delivery & Invoicing**

```
Process Step               System Action                    BlueJet State
─────────────────────────────────────────────────────────────────────────
📲 Notify customers        Document Agent:                 Update each customer:
   (goods ready)           ├─ Generate per-customer list    "Připraveno k výdeji"
                          ├─ Email: "Your order ready"
                          └─ Request delivery address

📤 Generate výdejka        Document Agent:                 📤 VÝDEJKA
                          ├─ Per customer (split order)    └─ sklad: Hlavní
                          ├─ Validate stock availability
                          └─ Check skladová karta

⚠️ Stock validation        Pre-dispatch check:             Error handling:
                          If (množství < objednávka):      ├─ Alert operator
                          ├─ BLOCK výdejka                 ├─ Suggest alternatives
                          └─ Require restock               └─ Partial dispatch?

✅ Confirm výdejka         Stock out process:              Confirm výdejka
                          ├─ Deduct from skladová karta    └─ stav: "Vyskladněno"
                          └─ Update real-time to Shoptet

📋 Generate dodací list    Print delivery note:            📋 DODACÍ LIST
                          ├─ Print above výdejka           └─ Associated w/ výdejka
                          ├─ Include customer signature
                          └─ Tracking number (if courier)

🚚 Ship goods              Logistics:                      Update stav:
                          ├─ Courier integration           "Odesláno"
                          ├─ Tracking link to customer
                          └─ Delivery confirmation

💰 Generate faktura        Invoice Agent:                  💰 FAKTURA
                          ├─ Generate from nabídka         └─ Based on nabídka
                          ├─ Deduct záloha (if paid)
                          └─ Email customer

📧 Send invoice            Email w/ PDF:                   Update stav:
                          ├─ Invoice + dodací list         "Odeslána"
                          ├─ Payment instructions
                          └─ Due date (14-30 days)
```

**Shoptet Integration:**
- **Tracking link** displayed in Shoptet order dashboard
- **Invoice PDF** accessible via Shoptet customer account
- **Payment status** updated real-time (GoPay webhook)

---

### **Stage 6: Payment Processing & Closure**

```
Payment Channel            Matching Process                 BlueJet Update
─────────────────────────────────────────────────────────────────────────
💳 GoPay API               Payment Agent:                  Check API:
                          ├─ Poll GoPay /payments          ├─ GET /payments
                          ├─ Match variabilní symbol       ├─ Match VS to invoice
                          └─ Confirm amount                └─ Validate amount

📧 RB/Citfin email         Email Parser Agent:             Parse email:
                          ├─ Extract VS, amount, date      ├─ Regex: VS pattern
                          ├─ Match to faktura              ├─ Fuzzy match customer
                          └─ Confidence scoring            └─ If > 90%: auto-match

✅ Full payment            Payment confirmed:              🧾 DOKLAD O PŘIJATÉ
                          ├─ Generate payment receipt       PLATBĚ
                          ├─ Update accounting export      └─ stav: "Uhrazena"
                          └─ Email confirmation

⚡ Partial payment         Záloha received:                Update částečně:
   (deposit)              ├─ Record deposit amount         └─ stav: "Částečně uhrazena"
                          ├─ Generate FA na 0,- w/ deduct
                          └─ Continue monitoring

❌ No payment              Overdue logic:                  Automated reminders:
                          Days overdue?                    ├─ Day 7: 1. upomínka
                          ├─ 0-6: Wait                     ├─ Day 14: 2. upomínka
                          ├─ 7+: 1st reminder              └─ Day 30: Inkaso
                          ├─ 14+: 2nd reminder
                          └─ 30+: Collection process

💰 Payment matched         Final reconciliation:           Update BlueJet:
                          ├─ Update účetnictví             └─ stav: "Uzavřena"
                          ├─ Export to Helios/Pohoda
                          └─ Close order in BlueJet

✅ Order complete          Archive & analytics:            📊 PROCESS COMPLETE
                          ├─ Customer satisfaction         └─ Ready for analytics
                          ├─ Supplier performance
                          └─ Profitability analysis
```

**Payment Matching Logic:**

| Scenario | Auto-Match? | Human Review? | Action |
|----------|-------------|---------------|--------|
| VS match + amount exact | ✅ YES | ❌ NO | Auto-confirm |
| VS match + amount partial | ⚡ YES (deposit) | ❌ NO | Record záloha |
| VS match + amount over | ⚠️ NO | ✅ YES | Review overpayment |
| VS no match | ❌ NO | ✅ YES | Manual matching |
| No VS in payment | ❌ NO | ✅ YES | Contact customer |

**Shoptet Integration:**
- **Payment status** synced to Shoptet order dashboard
- **Customer portal** shows payment history + pending invoices
- **Automated reminders** sent via Shoptet email system

---

## 🔗 SHOPTET PREMIUM INTEGRATION POINTS

### **1. Product Catalog Sync**

```
Direction: BlueJet → Shoptet
Frequency: Daily 08:00 + Real-time webhooks
Method: REST API + Webhooks

BlueJet Source          Shoptet Target         Notes
────────────────────────────────────────────────────────
Produkty (obj 217)   →  /api/products         40k+ items
Ceníky (obj 250)     →  /api/pricelists       Price lists
Skladové karty       →  /api/products/{id}/   E-shop sklad only
                        stock                  (NOT reserved)
```

**Key Requirements:**
- ✅ Hide **Hlavní sklad** items from web (reserved for customers)
- ✅ Show **E-shop sklad** items publicly
- ✅ Mark **Showroom** items as "Available for loan"
- ✅ Real-time stock updates via **inventory:change webhook**

---

### **2. Order Flow Integration**

```
Direction: Shoptet → BlueJet (Primary)
Trigger: order:create webhook
Method: Real-time webhook + async processing

Shoptet Event           BlueJet Action              Result
──────────────────────────────────────────────────────────────
order:create         →  POST /api/data (obj 232)   VYDANÁ NABÍDKA
                        └─ stav: "Potvrzena"        (skips human review)

order:update         →  PUT /api/data              Update stav
                        └─ Sync status changes

customer:create      →  POST /api/data (obj 222)   New KONTAKT
                        └─ Link to order
```

**Critical Decision:**
Should Shoptet orders:
- [ ] **Option A:** Create "Vydaná nabídka" → Human review → Send back quote?
- [ ] **Option B:** Auto-confirm as "Potvrzená nabídka" → Skip to consolidation?

**Recommendation:** **Option B** for e-commerce (instant confirmation), **Option A** for complex B2B inquiries.

---

### **3. Customer Data Sync**

```
Direction: Bi-directional
Frequency: Real-time (webhooks) + Daily backup sync
Method: REST API

BlueJet ↔ Shoptet         Sync Trigger           Data Fields
────────────────────────────────────────────────────────────────
Kontakty (obj 222)     ↔  /api/customers        Name, email, phone
Firmy (obj 225)        ↔  /api/customers        Company, VAT, address
Custom fields          ↔  customAttributes      VIP status, segment
```

---

### **4. Payment Integration**

```
Payment Flow: Shoptet → GoPay → BlueJet
Method: Shoptet native GoPay integration + BlueJet API polling

Customer pays (Shoptet) → GoPay processes → Webhook to BlueJet
                                          └─ Payment Agent matches
                                          └─ Updates faktura

Alternative: RB/Citfin email confirmations
             └─ Email Parser Agent
             └─ Extracts VS + amount
             └─ Matches to faktura
```

**Question for Shoptet Team:**
- Does Shoptet Premium support **direct GoPay webhook forwarding** to external systems?
- Or: Must we poll **GoPay API separately**?

---

## 📊 TECHNICAL REQUIREMENTS FOR SHOPTET TEAM

### **Must-Have Features:**

1. **Webhook Events Required:**
   - ✅ `order:create` (confirmed orders)
   - ✅ `order:update` (status changes)
   - ✅ `product:update` (price/stock changes)
   - ✅ `inventory:change` (stock quantity changes)
   - ✅ `customer:create` (new registrations)
   - ✅ `customer:update` (profile changes)

2. **API Endpoint Access:**
   - ✅ Private API Token authentication (32-char)
   - ✅ Full CRUD on products, orders, customers
   - ✅ Stock management (PATCH /products/{id}/stock)
   - ✅ Order status updates (PUT /orders/{id})

3. **Custom Fields Support:**
   - ✅ Product: `reserved`, `loan_available`, `customer_id`
   - ✅ Customer: `vip_status`, `segment`, `bluejet_id`
   - ✅ Order: `consolidation_group`, `supplier_eta`

4. **Rate Limits:**
   - ✅ Confirmed: 200 drops/cycle, 10/second refill (leaky bucket)
   - ✅ Max 50 connections per IP, 3 per token
   - ✅ Webhook response: <4 seconds (handled async)

---

## ❓ QUESTIONS FOR SHOPTET PREMIUM TEAM

### **1. Webhook Delivery Guarantees:**
- What happens if our webhook endpoint is down?
- How long is retry window? (doc says 3 attempts, 15-min intervals = 30 min total)
- Can we get **DLQ (dead-letter queue)** for failed webhooks?

### **2. Custom Field Mapping:**
- Are there **product-level custom attributes** beyond standard fields?
- Can we add **order-level metadata** (e.g., `consolidation_group_id`)?
- Limit on custom field count/size?

### **3. Stock Visibility Control:**
- How to **hide specific products** from public web but keep in system?
- Can we use **warehouse-based visibility** (E-shop visible, Hlavní hidden)?
- Alternative: Use **categories** or **tags** for visibility control?

### **4. Payment Webhook Forwarding:**
- Does Shoptet forward **GoPay payment webhooks** to external systems?
- Or: Must we integrate **directly with GoPay API**?
- Same question for **other payment gateways** (bank transfers)?

### **5. Migration Timeline:**
- What's typical **migration duration** (data import + testing)?
- Can we do **parallel run** (old custom web + Shoptet live simultaneously)?
- Rollback plan if issues arise?

### **6. Data Migration Support:**
- Will Shoptet team assist with **initial data import** (40k products, 5k customers)?
- Or: DIY via API bulk import?
- Any **import limits** (batch size, rate limits during migration)?

---

## 🚀 SUCCESS CRITERIA

### **Phase 1: Technical Validation (Week 1-2)**
- ✅ API connectivity verified (Private Token working)
- ✅ Webhook endpoint deployed and tested
- ✅ Product sync (100 test items) successful
- ✅ Order flow (10 test orders) end-to-end validated

### **Phase 2: Data Migration (Week 3-4)**
- ✅ Full product catalog imported (40k+ items)
- ✅ Customer database synced (5k+ contacts)
- ✅ Historical order data migrated (if applicable)
- ✅ Price lists configured (Ceníky mapped)

### **Phase 3: Go-Live (Week 5)**
- ✅ Parallel run (1 week): Both systems active
- ✅ Real customer orders processed successfully
- ✅ Payment matching working (GoPay + email)
- ✅ No critical bugs, downtime < 1 hour total

### **Phase 4: Post-Launch Optimization (Ongoing)**
- ✅ Monitor webhook delivery success rate (target: >99%)
- ✅ Stock sync accuracy (target: 100% within 5 min)
- ✅ Order consolidation efficiency (reduced supplier orders by 30%+)
- ✅ Customer satisfaction maintained (NPS > 50)

---

## 📎 APPENDIX: KEY BLUEJET OBJECTS

| Object # | Name | Purpose | API Endpoint |
|----------|------|---------|--------------|
| 217 | Produkty | Product catalog | GET/POST /api/v1/data?no=217 |
| 222 | Kontakty | Contacts | GET/POST /api/v1/data?no=222 |
| 225 | Firmy | Companies | GET/POST /api/v1/data?no=225 |
| 232 | Vydané nabídky | Issued quotes | GET/POST /api/v1/data?no=232 |
| 250 | Ceníky | Price lists | GET/POST /api/v1/data?no=250 |
| 253 | Ceníky - položky | Price list items | GET/POST /api/v1/data?no=253 |
| 323 | Vydané faktury | Invoices | GET/POST /api/v1/data?no=323 |
| 356 | Vydané objednávky | Sales orders | GET/POST /api/v1/data?no=356 |

**Authentication:** BlueJet API uses token-based auth (TokenID + TokenHash)
**Base URL:** `https://czeco.bluejet.cz/api/v1/`

---

**Document prepared by:** Premium Gastro AI Assistant
**For meeting with:** Shoptet Premium Team
**Date:** 2026-01-13, 10:00
**Status:** ✅ Ready for presentation
