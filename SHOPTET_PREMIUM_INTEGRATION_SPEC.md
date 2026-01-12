# Shoptet Premium ↔ BlueJet Integration Specification
**Technical Integration Specification for Custom Web → Shoptet Premium Migration**

**Date**: January 12, 2026
**Status**: Pre-Implementation (Meeting Preparation)
**Audience**: Shoptet Premium Team, BlueJet CRM Team, Development Team

---

## Executive Summary

This document outlines the complete technical integration architecture for migrating from a custom web solution to Shoptet Premium (STP), with seamless synchronization with BlueJet CRM/ERP system. The integration leverages Shoptet Premium's REST API for real-time data synchronization across products, orders, inventory, and customer data, combined with webhook-based event-driven architecture for efficient data flow.

**Key Integration Points:**
- REST API-based data synchronization
- Webhook-driven real-time event notifications
- Bi-directional data sync (Products, Orders, Customers, Inventory)
- OAuth 2.0 & Private Token Authentication
- Rate-limited API with automatic retry mechanisms
- Error handling and data validation strategies

---

## 1. API Architecture Overview

### 1.1 Authentication Methods

Shoptet Premium provides two authentication mechanisms:

#### **Option A: Private API Token (Recommended for Premium Members)**
- **Use Case**: Direct access to shop owner's eshop data
- **Token Type**: 32 alphanumeric character string
- **Generation**: Admin Panel → Connections → Private API
- **Limit**: Up to 10 tokens per eshop
- **Header Format**:
```
Shoptet-Private-API-Token: {your-32-char-token}
Content-Type: application/json
```
- **Validity**: Unlimited (no expiration)
- **Connection Limits**: Max 3 concurrent connections per token

#### **Option B: OAuth 2.0 Flow (For Add-on Developers)**
- **Use Case**: Third-party application developers
- **Components**:
  - OAuth Access Token (255 characters, unlimited validity)
  - API Access Token (38-60 characters, time-limited)
- **Flow**: Web service → OAuth server → Access Token → API calls
- **Endpoint**: https://api.myshoptet.com

**MIGRATION RECOMMENDATION**: Use Private API Token for direct BlueJet integration as you own the Shoptet Premium eshop.

### 1.2 API Base Endpoint
```
https://api.myshoptet.com/api/
```

### 1.3 Request Format
- **Protocol**: HTTPS only
- **Data Format**: JSON
- **Method Support**: GET, POST, PUT, PATCH, DELETE

---

## 2. API Endpoints Mapping

### 2.1 Product Management (Ceníky & Produkty)

**Endpoint Category**: Products & Price Lists

#### List All Products
```
GET /api/products
```
- **Parameters**:
  - `pageNo`: Page number (pagination)
  - `pageSize`: Items per page (default: varies)
  - `searchTerm`: Filter by product name
  - `categoryId`: Filter by category

- **Response**: Returns basic info (GUID, name, code) and product details
- **Use Case**: Initial product sync, periodic inventory updates

#### Get Product Details
```
GET /api/products/{productId}
```
- **Response Includes**:
  - Product name & description
  - Price information
  - Stock quantities
  - Category assignment
  - Images & attributes
  - Tax classification

#### Create Product
```
POST /api/products
```
- **Payload**: Product object with required fields
- **Use Case**: New product creation from BlueJet catalog

#### Update Product
```
PUT /api/products/{productId}
PATCH /api/products/{productId}
```
- **Sync Use Case**: Price updates, stock adjustments from BlueJet

#### Price Lists (Ceníky)
```
GET /api/pricelists
GET /api/pricelists/{pricelistId}
```
- **Contains**: Price configurations, discounts, purchase restrictions
- **Use Case**: Multi-currency / multi-customer price management

**Data Mapping Example**:
```
BlueJet (Source)          → Shoptet Premium (Target)
├─ Product Code           → productCode
├─ Title/Description      → name, description
├─ Price (CZK)           → price (with currency conversion if needed)
├─ Stock Quantity        → quantity
├─ Category              → categoryId
└─ Attributes            → customAttributes (if available)
```

---

### 2.2 Order Management (Objednávky)

**Endpoint Category**: Orders

#### List All Orders
```
GET /api/orders
```
- **Parameters**:
  - `pageNo`, `pageSize`: Pagination
  - `statusId`: Filter by order status
  - `dateFrom`, `dateTo`: Date range filtering

- **Response**: Order summary list with order numbers and timestamps

#### Get Order Details
```
GET /api/orders/{orderId}
```
- **Response Includes**:
  - Order header (number, date, total)
  - Line items with products/quantities/prices
  - Customer information
  - Shipping address
  - Payment method
  - Order status & history
  - Custom fields (company name, exchange rate)

#### Create Order (Complex)
```
POST /api/orders
```
- **Complexity**: ~70 fields supported
- **Key Fields**:
  - Customer data (name, email, phone, address)
  - Item list (productId, quantity, unitPrice)
  - Shipping method & costs
  - Payment method
  - Discount information
  - Flags:
    - `generateEmails`: Auto-send notifications
    - `generateDocuments`: Auto-generate invoices/delivery notes
    - `checkProduct`: Validate product existence
    - `deductFromStock`: Update inventory on create

#### Update Order
```
PUT /api/orders/{orderId}
```
- **Supported Updates**:
  - Order status changes
  - Shipping information
  - Customer data corrections
  - Payment status

#### Order Statuses
```
GET /api/orders/statuses
```
- Returns all available order statuses in Shoptet
- **Map to BlueJet**: Objednávky & Nabídky (offers/quotes)

#### Order Line Items Management
```
GET /api/orders/{orderId}/items
POST/PUT/DELETE /api/orders/{orderId}/items/{itemId}
```

#### Order History
```
GET /api/orders/{orderId}/history
```
- Track order state changes and modifications

#### Order Gifts Management
```
GET/POST/DELETE /api/orders/{orderId}/gifts
```

#### Order Payment Management
```
GET/PUT /api/orders/{orderId}/payment
```

**Data Mapping Example**:
```
BlueJet (Source)              → Shoptet Premium (Target)
├─ Objednávka #               → Order Number
├─ Customer Contact           → Customer Data
├─ Line Items (Products)      → Order Items
├─ Total CZK                  → Order Total
├─ Status (Draft/Final)       → Order Status
├─ Nabídka → Order conversion → Create Order endpoint
└─ Payment Status             → Payment field
```

---

### 2.3 Customer Data Sync

**Endpoint Category**: Customers

#### List Customers
```
GET /api/customers
```
- **Parameters**:
  - Pagination (pageNo, pageSize)
  - Search filters

#### Get Customer Details
```
GET /api/customers/{customerId}
```
- **Response Includes**:
  - Contact information (name, email, phone)
  - Addresses (billing, shipping)
  - Purchase history
  - Tags/segments
  - Custom fields

#### Create/Update Customer
```
POST /api/customers
PUT /api/customers/{customerId}
```

**Data Mapping Example**:
```
BlueJet (Source)    → Shoptet Premium (Target)
├─ Contact Name     → firstName, lastName
├─ Email            → email
├─ Phone            → phone
├─ Company          → company
├─ Address          → billing/shipping address
└─ Custom Fields    → customAttributes
```

---

### 2.4 Inventory Management

#### Check Stock Positions (Skladové pozice)
```
GET /api/products/{productId}/stock
GET /api/warehouse/stock
```
- Returns current inventory levels by warehouse

#### Stock Adjustments
```
PATCH /api/products/{productId}/stock
```
- Update inventory on order fulfillment
- Reserve stock for pending orders
- Synchronize with BlueJet inventory module

#### Warehouse Management
```
GET /api/warehouses
GET /api/warehouses/{warehouseId}/stock
```
- Multi-warehouse support
- Track stock across multiple locations

**Integration Pattern**:
```
Order Created → Deduct from Stock → Sync to BlueJet
BlueJet Stock Update → POST to Shoptet → Reflect in Eshop
```

---

## 3. Webhook Configuration & Events

### 3.1 Webhook Registration

#### Register Webhook
```
POST /api/webhooks
```

**Request Payload**:
```json
{
  "event": "order:create",
  "url": "https://your-system.com/webhooks/shoptet/order-created",
  "isActive": true
}
```

**Configuration Rules**:
- Only 1 URL per event type
- Ports allowed: 80, 8080, 443, 8443
- HTTPS strongly recommended
- Registration per eshop installation

#### List Registered Webhooks
```
GET /api/webhooks
```

#### Delete Webhook
```
DELETE /api/webhooks/{webhookId}
```

### 3.2 Available Webhook Events

Based on Shoptet Premium API documentation, key webhook events include:

| Event Type | Trigger | Data Included | BlueJet Integration |
|-----------|---------|---------------|-------------------|
| `order:create` | New order placed | Order ID, customer, items, total | Create order in BlueJet |
| `order:update` | Order status change | Order ID, new status, timestamp | Update Nabídka/Objednávka |
| `order:payment` | Payment received | Order ID, payment details | Update payment status |
| `product:create` | New product added | Product ID, details | Add to BlueJet catalog |
| `product:update` | Product modified | Product ID, changed fields | Update BlueJet product |
| `product:delete` | Product removed | Product ID | Archive in BlueJet |
| `inventory:change` | Stock quantity change | Product ID, warehouse, new qty | Sync BlueJet inventory |
| `customer:create` | New customer registered | Customer ID, details | Create contact in BlueJet |
| `customer:update` | Customer data modified | Customer ID, changed fields | Update BlueJet contact |

**Note**: Complete event list available at: https://api.docs.shoptet.com/shoptet-api/openapi/section/code-lists/webhook-event-types

### 3.3 Webhook Payload Structure

**Example: Order Create Webhook**
```json
{
  "eshopId": "12345",
  "event": "order:create",
  "eventCreated": "2026-01-12T10:30:00Z",
  "eventInstance": "Order#12345",
  "data": {
    "orderId": "12345",
    "orderNumber": "ORD-2026-001",
    "customerId": "67890",
    "orderDate": "2026-01-12T10:25:00Z",
    "status": "pending",
    "totalPrice": 1500.00,
    "currency": "CZK"
  }
}
```

### 3.4 Webhook Handling Best Practices

**Response Requirements**:
- HTTP Status Code: **200** (OK)
- Response Time: **4 seconds maximum**
- Signature Verification: Use `Shoptet-Webhook-Signature` header (HMAC-SHA1)

**Retry Logic**:
- If no 200 response: Retry after 15 minutes
- Maximum 3 retry attempts
- Total window: 30 minutes for successful delivery

**Processing Pattern**:
```
1. Receive webhook POST (max 4 sec)
   ↓
2. Validate Shoptet-Webhook-Signature header
   ↓
3. Store event ID (idempotency check)
   ↓
4. Return HTTP 200 immediately
   ↓
5. Queue async processing (separate background job)
   ↓
6. Update BlueJet via API call
   ↓
7. Log success/failure
```

---

## 4. Rate Limiting & API Restrictions

### 4.1 Connection Limits

| Limit Type | Value | Exceeded Response |
|-----------|-------|------------------|
| Connections per IP | 50 max | HTTP 429 |
| Connections per token | 3 max | HTTP 429 |
| Request timeout | 4 seconds | Connection timeout |
| Webhook response timeout | 4 seconds | Retry scheduled |

### 4.2 Leaky Bucket Algorithm

**Capacity Model**:
- Bucket capacity: 200 "drops"
- Refill rate: 10 drops/second
- Each API request: Consumes 1-multiple drops

**Rate Limit Headers** (in every response):
```
X-RateLimit-Bucket-Filling: 150/200      (current/max)
Retry-After: Mon, 12 Jan 2026 10:35:00 GMT  (if bucket full)
```

**Handling Rate Limits**:
```python
if response.status_code == 429:
    retry_after = response.headers.get('Retry-After')
    # Parse retry_after datetime
    # Wait until retry_after time
    # Retry request
```

### 4.3 Write Request Deduplication

**Automatic Request Locking**:
- If same request sent twice in quick succession
- Second request gets HTTP 423 (Locked)
- Lock duration: 5 seconds max
- Only for specific called URL

**Implication**: N8n workflows with retries must handle 423 status code

### 4.4 Data Volume & Query Limits

**Quantity of queries**: Unlimited
**Total data volume**: Unlimited
**Pagination**: Use `pageNo` and `pageSize` parameters

**Recommended Pagination Settings**:
```
pageSize: 50-100 items (balance between requests and data size)
pageNo: Start from 1, increment for next batch
```

### 4.5 Rate Limit Strategy for BlueJet Sync

**Recommended Approach**:
```
Morning Sync (08:00):
- Fetch all products (paginated)
- Fetch all customers
- Fetch last 24h orders
- Each request: 1-2 drops
- Stagger requests by 500ms

Webhook-Driven (Real-time):
- Order create/update: Immediate processing
- Inventory changes: Queue if rate limit approaching
- Batch inventory updates: 5-min delay acceptable
```

---

## 5. Authentication Setup & Configuration

### 5.1 Private API Token Setup (Recommended Path)

**Step 1: Generate Token in Shoptet Admin**
```
1. Log into Shoptet Premium admin panel
2. Navigate to: Connections → Private API
3. Click "Generate new token"
4. Copy 32-character token
5. Store securely in environment variables / password manager
```

**Step 2: Configure BlueJet Integration**
```
# In N8n or integration middleware:
SHOPTET_API_TOKEN = "your-32-char-token"
SHOPTET_API_BASE_URL = "https://api.myshoptet.com/api/"
SHOPTET_ESHOP_ID = "your-eshop-id"
```

**Step 3: Test Connectivity**
```bash
curl -X GET https://api.myshoptet.com/api/products \
  -H "Shoptet-Private-API-Token: your-32-char-token" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json"
```

### 5.2 OAuth Setup (For Add-on Developers)

**Not recommended** for direct BlueJet integration. Use if:
- Building a Shoptet marketplace add-on
- Managing multiple eshops
- Third-party SaaS application

**OAuth Flow**:
```
1. Register app on https://developers.shoptet.com/
2. Get Client ID & Client Secret
3. Implement OAuth callback endpoint
4. Exchange authorization code for Access Token
5. Use Access Token to get API Access Token (time-limited)
6. Refresh when expired
```

---

## 6. Data Flow Diagrams

### 6.1 Product Synchronization Flow

```
┌─────────────────────────────────────────────────────────────┐
│ PRODUCT SYNC: Shoptet Premium → BlueJet                     │
└─────────────────────────────────────────────────────────────┘

SCHEDULE-BASED SYNC (Daily 08:00 CET):
┌────────────────┐
│   BlueJet      │
│  Product List  │
└────────┬────────┘
         │ Product Catalog
         │ (Code, Name, Price, Stock)
         │
         ▼
┌──────────────────────┐
│  N8n Workflow        │
│  "Sync Products"     │
└──────┬───────────────┘
       │
       ├─► GET /api/products (paginated)
       │
       ▼
┌─────────────────────┐
│ Shoptet Premium API │
│ Returns: Product    │
│ list (100 items/pg) │
└──────┬──────────────┘
       │ Loop: for each product
       │
       ▼
┌──────────────────────┐
│ Data Transformation  │
│ Shoptet → BlueJet    │
│ Schema               │
└──────┬───────────────┘
       │
       ├─► Product Code
       ├─► Name/Description
       ├─► Category mapping
       ├─► Price conversion
       └─► Stock quantity
       │
       ▼
┌──────────────────────┐
│ BlueJet API          │
│ POST /products       │
│ (Create/Update)      │
└──────┬───────────────┘
       │
       ▼
┌─────────────────────┐
│ ✓ Synced            │
│ 2,150 products      │
│ updated/created     │
└─────────────────────┘

REAL-TIME UPDATES (Webhook-Driven):
┌────────────────────┐
│ Shoptet: Product   │
│ Modified           │
│ (Price/Stock)      │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ POST /webhooks     │
│ product:update     │
│ (Product ID)       │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Your Webhook       │
│ Endpoint           │
│ (4 sec response)   │
└────────┬───────────┘
         │
         ├─► Verify Signature
         ├─► Check Idempotency
         ├─► Return 200 OK (sync)
         │
         ▼
┌────────────────────┐
│ Async Job Queue    │
│ (Separate thread)  │
└────────┬───────────┘
         │
         ├─► GET /api/products/{id}
         │
         ▼
┌────────────────────┐
│ Shoptet Detail API │
│ Returns: Full      │
│ product data       │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ BlueJet Update     │
│ PUT /products/{id} │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Log & Monitor      │
│ Sync Status        │
└────────────────────┘
```

### 6.2 Order Synchronization Flow

```
┌─────────────────────────────────────────────────────────────┐
│ ORDER SYNC: Shoptet Premium ↔ BlueJet (Bi-directional)     │
└─────────────────────────────────────────────────────────────┘

CUSTOMER PLACES ORDER (Shoptet Web):
┌────────────────────────┐
│ Shoptet Eshop          │
│ Order Placement        │
│ (Customer submits)     │
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│ order:create Webhook   │
│ Event triggered        │
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│ BlueJet Webhook Listener
│ Receives order notification
│ (Event ID, Order#)     │
└──────────┬─────────────┘
           │
           ├─► Verify Shoptet-Webhook-Signature
           ├─► Check idempotency (store event ID)
           ├─► Return HTTP 200 (critical: <4 sec)
           │
           ▼
┌────────────────────────┐
│ Async Background Job   │
│ (Separate from webhook │
│  response)             │
└──────────┬─────────────┘
           │
           ├─► GET /api/orders/{orderId}
           │   (fetch full order details)
           │
           ▼
┌────────────────────────┐
│ Shoptet Order Detail   │
│ ├─ Customer info       │
│ ├─ Line items          │
│ ├─ Totals (CZK)        │
│ ├─ Status              │
│ └─ Timestamps          │
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│ Data Mapping           │
│ Shoptet → BlueJet      │
│ Schema                 │
└──────────┬─────────────┘
           │
           ├─► Order number → Order#
           ├─► Customer data → Contact sync
           ├─► Items → Line items
           ├─► Status (pending) → "Nabídka" or "Objednávka"
           ├─► Total price → CZK amount
           └─► Shipping address → BlueJet address field
           │
           ▼
┌────────────────────────┐
│ BlueJet Creation       │
│ POST /orders           │
│ (Create Objednávka)    │
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│ BlueJet Order Created  │
│ ✓ Order# synced        │
│ ✓ Customer linked      │
│ ✓ Ready for fulfillment│
└─────────────────────────┘

ORDER STATUS UPDATES:
┌────────────────────────┐
│ Shoptet: Order Status  │
│ Changes (e.g., shipped)│
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│ order:update Webhook   │
│ (Optional if STP       │
│  supports it)          │
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│ BlueJet Status Update  │
│ PUT /orders/{id}       │
│ status: "shipped"      │
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│ ✓ Status synced        │
│ ✓ Customer notified    │
│   (if configured)      │
└─────────────────────────┘

INVENTORY DEDUCTION:
┌────────────────────────┐
│ Order Created Event    │
│ (Webhook includes flag)│
└──────────┬─────────────┘
           │
           ├─► Check POST body:
           │   "deductFromStock": true
           │
           ▼
┌────────────────────────┐
│ Optional: Manual       │
│ PATCH /products/{id}   │
│ /stock                 │
│ Update inventory in STP│
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│ Sync to BlueJet        │
│ Inventory module       │
└─────────────────────────┘
```

### 6.3 Customer Data Synchronization

```
┌─────────────────────────────────────────────────────────────┐
│ CUSTOMER SYNC: Shoptet Premium ↔ BlueJet (Bi-directional)  │
└─────────────────────────────────────────────────────────────┘

INITIAL IMPORT (One-time):
┌──────────────────────┐
│ N8n Workflow         │
│ "Sync Customers"     │
│ (Manual trigger)     │
└──────────┬───────────┘
           │
           ├─► GET /api/customers
           │   (paginated: pageSize=100)
           │
           ▼
┌──────────────────────┐
│ Shoptet Customer List│
│ (Basic info + GUID)  │
└──────────┬───────────┘
           │
           ├─► Loop: for each GUID
           │
           ▼
┌──────────────────────┐
│ GET /api/customers/  │
│ {customerId}         │
│ (Full details)       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Customer Details:    │
│ ├─ Name              │
│ ├─ Email             │
│ ├─ Phone             │
│ ├─ Company           │
│ ├─ Addresses         │
│ └─ Purchase history  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ BlueJet Creation     │
│ POST /contacts       │
│ (Create/update)      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Map fields:          │
│ ├─ firstName/lastName│
│ ├─ email             │
│ ├─ phone             │
│ ├─ company           │
│ ├─ addresses         │
│ └─ custom fields     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ ✓ 5,000+ customers   │
│   synced to BlueJet  │
└──────────────────────┘

REAL-TIME UPDATES:
┌──────────────────────┐
│ Shoptet: Customer    │
│ Registration/Update  │
│ (customer:create or  │
│  customer:update)    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Webhook Event        │
│ Listener             │
└──────────┬───────────┘
           │
           ├─► Verify & return 200
           │
           ▼
┌──────────────────────┐
│ Async Processing     │
│ GET /api/customers/  │
│ {customerId}         │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ BlueJet Sync         │
│ Create/Update contact│
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ ✓ Customer synced    │
│ ✓ Ready for CRM      │
│   integration        │
└──────────────────────┘
```

---

## 7. Error Handling Strategy

### 7.1 HTTP Status Code Response Matrix

| Status | Category | Handling | Retry |
|--------|----------|----------|-------|
| **200** | Success | Process response | No |
| **400** | Bad Request | Fix request schema, don't retry | No |
| **401** | Unauthorized | Check API token validity/expiration | No |
| **403** | Forbidden | Check token permissions | No |
| **404** | Not Found | Verify entity exists in Shoptet | No |
| **409** | Conflict | Check uniqueness constraints | No |
| **413** | Payload Too Large | Reduce batch size in request | No |
| **422** | Unprocessable Entity | Validate JSON schema | No |
| **423** | Locked | Wait 5 seconds, retry | Yes (exponential backoff) |
| **429** | Rate Limited | Check X-RateLimit-Bucket-Filling, wait Retry-After | Yes (respect header) |
| **5xx** | Server Error | Retry with exponential backoff | Yes (up to 3 attempts) |

### 7.2 Error Response Format

**Typical Shoptet Error Response**:
```json
{
  "errors": [
    {
      "message": "Product with code 'ABC-001' already exists",
      "code": "PRODUCT_CODE_DUPLICATE",
      "field": "productCode",
      "statusCode": 409
    }
  ],
  "data": null
}
```

### 7.3 Retry Strategy (N8n Workflow Implementation)

**Configuration**:
```
Retry Policy:
├─ Max attempts: 3
├─ Backoff strategy: Exponential
│   ├─ Attempt 1: Immediate
│   ├─ Attempt 2: Wait 2 seconds
│   └─ Attempt 3: Wait 8 seconds
├─ Retry on: 429, 423, 5xx
├─ Don't retry: 4xx (except 423, 429)
└─ Timeout: 30 seconds per request
```

### 7.4 Idempotency Strategy

**Problem**: Webhooks can be retried up to 3 times, causing duplicate processing

**Solution - Event Deduplication**:
```
1. Extract event ID from webhook (eshopId + event + timestamp + eventInstance)
2. Check BlueJet database: SELECT * FROM webhook_events WHERE event_id = ?
3. If exists: Return 200 (skip processing)
4. If new: Process and insert into webhook_events table
5. Set unique constraint: UNIQUE(event_id)
```

**Database Schema**:
```sql
CREATE TABLE webhook_events (
  id SERIAL PRIMARY KEY,
  event_id VARCHAR(255) UNIQUE NOT NULL,
  event_type VARCHAR(100) NOT NULL,
  eshop_id VARCHAR(50) NOT NULL,
  payload JSON,
  processed_at TIMESTAMP,
  status ENUM('pending', 'completed', 'failed'),
  created_at TIMESTAMP DEFAULT NOW()
);
```

### 7.5 Data Validation Strategy

**Before sending to BlueJet API**:
```
1. JSON Schema Validation
   └─ Validate against BlueJet API schema

2. Data Integrity Checks
   ├─ Required fields present
   ├─ Email format validation (if customer data)
   ├─ Phone number format
   └─ Price > 0

3. Referential Integrity
   ├─ Customer exists in BlueJet (if linking)
   ├─ Product exists in BlueJet catalog
   └─ Order status is valid enum

4. Business Rules
   ├─ Order total matches line items sum
   ├─ Inventory sufficient (if deducting)
   └─ Customer address complete

5. Error Handling
   ├─ Log validation errors
   ├─ Notify on critical failures
   └─ Queue for manual review
```

---

## 8. Webhook Configuration Details

### 8.1 Webhook Registration Checklist

```
☐ Register order:create webhook
  URL: https://your-domain.com/api/webhooks/shoptet/order-created
  Port: 443 (HTTPS)

☐ Register order:update webhook (if available)
  URL: https://your-domain.com/api/webhooks/shoptet/order-updated
  Port: 443

☐ Register product:update webhook
  URL: https://your-domain.com/api/webhooks/shoptet/product-updated
  Port: 443

☐ Register inventory:change webhook
  URL: https://your-domain.com/api/webhooks/shoptet/inventory-changed
  Port: 443

☐ Register customer:create webhook
  URL: https://your-domain.com/api/webhooks/shoptet/customer-created
  Port: 443

☐ Register customer:update webhook
  URL: https://your-domain.com/api/webhooks/shoptet/customer-updated
  Port: 443
```

### 8.2 Webhook Signature Verification (Security)

**Shoptet Signs Webhooks with HMAC-SHA1**:
```
Signature = HMAC-SHA1(payload, secret-key)
Sent as: Shoptet-Webhook-Signature header
```

**Verification Code (Node.js Example)**:
```javascript
const crypto = require('crypto');

function verifyWebhookSignature(payload, signature, secretKey) {
  const hmac = crypto
    .createHmac('sha1', secretKey)
    .update(JSON.stringify(payload))
    .digest('hex');

  return crypto.timingSafeEqual(
    Buffer.from(hmac),
    Buffer.from(signature)
  );
}

// In webhook handler:
if (!verifyWebhookSignature(req.body, req.headers['shoptet-webhook-signature'], SHOPTET_SECRET)) {
  return res.status(401).json({ error: 'Invalid signature' });
}
```

---

## 9. Integration Architecture (N8n Workflow Map)

### 9.1 Core Workflows Required

```
N8N WORKFLOWS:
├─ 01_Shoptet_Product_Sync
│  ├─ Schedule: Daily 08:00 CET
│  ├─ Action: GET /api/products (paginated)
│  ├─ Transform: Map Shoptet → BlueJet schema
│  └─ Target: BlueJet POST /products
│
├─ 02_Shoptet_Order_Import
│  ├─ Schedule: Daily 08:15 CET
│  ├─ Action: GET /api/orders (last 24h)
│  ├─ Transform: Map Shoptet → BlueJet schema
│  └─ Target: BlueJet POST /orders
│
├─ 03_Shoptet_Customer_Sync
│  ├─ Schedule: Daily 08:30 CET
│  ├─ Action: GET /api/customers (paginated)
│  ├─ Transform: Map Shoptet → BlueJet schema
│  └─ Target: BlueJet POST /contacts
│
├─ 04_Webhook_Listener_Order_Create
│  ├─ Trigger: HTTP POST (port 443)
│  ├─ Event: order:create
│  ├─ Action: Verify signature, return 200 immediately
│  ├─ Queue: Async job (separate from response)
│  └─ Target: BlueJet Order creation
│
├─ 05_Webhook_Listener_Order_Update
│  ├─ Trigger: HTTP POST
│  ├─ Event: order:update
│  ├─ Action: Same as order:create
│  └─ Target: BlueJet Order update
│
├─ 06_Webhook_Listener_Product_Update
│  ├─ Trigger: HTTP POST
│  ├─ Event: product:update
│  ├─ Action: Fetch product details, sync to BlueJet
│  └─ Target: BlueJet Product update
│
├─ 07_Webhook_Listener_Inventory_Change
│  ├─ Trigger: HTTP POST
│  ├─ Event: inventory:change
│  ├─ Action: Update inventory in BlueJet
│  └─ Target: BlueJet Stock module
│
├─ 08_Webhook_Listener_Customer_Create
│  ├─ Trigger: HTTP POST
│  ├─ Event: customer:create
│  └─ Target: BlueJet Contact creation
│
├─ 09_Webhook_Listener_Customer_Update
│  ├─ Trigger: HTTP POST
│  ├─ Event: customer:update
│  └─ Target: BlueJet Contact update
│
├─ 10_Error_Logging
│  ├─ Monitor: All API failures
│  ├─ Log: Supabase or local database
│  └─ Alert: Slack notification on critical errors
│
└─ 11_Health_Check
   ├─ Schedule: Hourly
   ├─ Test: Shoptet API connectivity
   └─ Alert: If API unreachable
```

---

## 10. Customer Experience Implications

### 10.1 Data Migration Impact

**During Migration**:
- **Order History**: All historical orders imported to BlueJet
- **Customer Contacts**: All existing customers synced
- **Product Catalog**: Complete product list available in Shoptet
- **Expected Duration**: 2-6 hours depending on data volume

**Post-Migration**:
- **Order Processing**: Real-time notifications via webhooks
- **Customer Service**: Unified customer view in BlueJet
- **Inventory**: Real-time stock updates across systems
- **Payment Processing**: Same as before (no change)

### 10.2 Customer-Facing Changes

| Aspect | Before (Custom Web) | After (Shoptet Premium) | Impact |
|--------|-------------------|----------------------|--------|
| **Checkout** | Custom implementation | Shoptet native checkout | Potentially faster, more secure |
| **Product Pages** | Custom design | Shoptet templated design | May differ in appearance |
| **Shipping** | Manual entry | Shoptet courier integration | Automated shipping options |
| **Payment** | Custom implementation | Shoptet payment gateway | Same payment methods |
| **Tracking** | Manual updates | Automated via webhooks | Real-time order status |
| **Email Notifications** | Custom templates | Shoptet templates | Consistent branding needed |

### 10.3 Uptime & Performance

**Shoptet Premium SLA**: 99.5% uptime (typical SaaS commitment)
- **Scheduled maintenance**: Minimal (usually off-peak)
- **Load handling**: Scalable infrastructure
- **Response time**: <500ms for API calls (under normal load)

**Webhook reliability**:
- **Delivery guarantee**: 3 retry attempts (15-min intervals)
- **Timeout handling**: System-managed (no customer impact)

### 10.4 Testing Strategy (Pre-Go-Live)

```
PHASE 1: Development Environment
├─ Test data products (10-20 items)
├─ Test orders (5-10 scenarios)
├─ Verify webhook delivery
└─ Validate error handling

PHASE 2: Staging Environment
├─ Full product catalog
├─ 100+ test orders
├─ Load testing (100 concurrent users)
├─ Webhook stress testing (1000 events/min)
└─ Customer experience walkthrough

PHASE 3: Production Rollout
├─ Go-live date: [TBD - coordinate with Shoptet]
├─ Data migration: [TBD]
├─ Parallel run: 1 week (both systems active)
├─ Cut-over time: Evening/low-traffic period
└─ Rollback plan: Revert to custom web if critical issues

PHASE 4: Post-Go-Live
├─ Monitor orders: First 24 hours
├─ Verify webhooks: All event types working
├─ Performance monitoring: Response times, error rates
├─ Customer feedback: Address any issues
└─ Documentation: Update internal procedures
```

### 10.5 Communication Plan

**Pre-Migration**:
- Notify customers 2 weeks before migration
- Email: "New e-shop platform coming soon"
- FAQ: Address common concerns

**During Migration** (if there's downtime):
- Maintenance page: "Upgrading our platform"
- ETA: When service will resume
- Contact: Support email/phone number

**Post-Migration**:
- Announcement: "Welcome to our upgraded platform"
- Training: How to use new features
- Feedback: Request improvement suggestions

---

## 11. Implementation Roadmap

### Phase 1: Preparation (Week 1)
- [ ] Generate Shoptet Private API token
- [ ] Document current data structure (custom web)
- [ ] Identify data mapping requirements
- [ ] Set up N8n instance
- [ ] Create webhook endpoint infrastructure

### Phase 2: Development (Week 2-3)
- [ ] Implement N8n workflows (1-11 from Section 9)
- [ ] Test API connectivity
- [ ] Develop data transformation logic
- [ ] Implement webhook handlers
- [ ] Set up error logging

### Phase 3: Testing (Week 4)
- [ ] Staging environment setup
- [ ] Full product sync test
- [ ] Order creation/update test
- [ ] Customer data sync test
- [ ] Webhook delivery verification
- [ ] Error scenarios testing
- [ ] Performance & load testing

### Phase 4: Go-Live (Week 5)
- [ ] Parallel run (both systems active)
- [ ] Monitor for issues
- [ ] Execute cut-over
- [ ] Verify all systems operational
- [ ] Post-go-live support

---

## 12. Technical Specification Summary

### API Endpoints (Quick Reference)
```
GET  /api/products                    → List products
POST /api/products                    → Create product
GET  /api/products/{id}               → Get product details
PUT  /api/products/{id}               → Update product
GET  /api/products/{id}/stock         → Get stock status
PATCH /api/products/{id}/stock        → Update stock

GET  /api/orders                      → List orders
POST /api/orders                      → Create order
GET  /api/orders/{id}                 → Get order details
PUT  /api/orders/{id}                 → Update order
GET  /api/orders/statuses             → Available statuses
GET  /api/orders/{id}/items           → Order line items
GET  /api/orders/{id}/payment         → Payment info

GET  /api/customers                   → List customers
POST /api/customers                   → Create customer
GET  /api/customers/{id}              → Get customer details
PUT  /api/customers/{id}              → Update customer

POST /api/webhooks                    → Register webhook
GET  /api/webhooks                    → List webhooks
DELETE /api/webhooks/{id}             → Delete webhook

GET  /api/pricelists                  → List price lists
GET  /api/pricelists/{id}             → Get price list details
```

### Authentication
```
Header: Shoptet-Private-API-Token: {32-char-token}
Header: Content-Type: application/json
```

### Rate Limits
```
- 50 connections per IP
- 3 connections per token
- Leaky bucket: 200 drops, 10/second refill
- Retry on: 429, 423, 5xx
```

### Webhook Events
```
- order:create
- order:update
- product:create
- product:update
- product:delete
- inventory:change
- customer:create
- customer:update
```

---

## 13. References & Documentation Links

**Official Shoptet Resources:**
- [Shoptet API Documentation](https://api.docs.shoptet.com/)
- [Shoptet Developers Portal](https://developers.shoptet.com/)
- [Shoptet Premium API](https://www.shoptetpremium.com/api/)
- [Webhooks Documentation](https://developers.shoptet.com/api/documentation/webhooks/)
- [Private API Access](https://developers.shoptet.com/home/premium/private-api/)
- [Authentication Guide](https://developers.shoptet.com/api/documentation/eshop-verification-using-oauth/)

**Related Systems:**
- [BlueJet CRM Integration](https://www.bluejet.cz/integrace/)
- [BlueJet API Documentation](https://www.bluejet.cz/)
- [N8n Workflow Automation](https://n8n.io/)

---

## 14. Appendix: Sample Data Mappings

### A1. Product Mapping Example

**Shoptet Response**:
```json
{
  "id": "12345",
  "code": "PASTA-CARBONARA-500G",
  "name": "Carbonara Pasta 500g",
  "description": "Fresh carbonara pasta with premium ingredients",
  "price": 149.90,
  "currency": "CZK",
  "quantity": 250,
  "categoryId": "pasta-sauces",
  "imageUrl": "https://shoptet.com/img/pasta-carbonara.jpg"
}
```

**BlueJet Transformed**:
```json
{
  "productCode": "PASTA-CARBONARA-500G",
  "title": "Carbonara Pasta 500g",
  "description": "Fresh carbonara pasta with premium ingredients",
  "price": 149.90,
  "currency": "CZK",
  "stock": 250,
  "category": "Pasta & Sauces",
  "externalId": "shoptet:12345",
  "imageUrl": "https://shoptet.com/img/pasta-carbonara.jpg"
}
```

### A2. Order Mapping Example

**Shoptet Response**:
```json
{
  "id": "ORD-2026-001",
  "number": "2026-001",
  "customerId": "CUST-5678",
  "customer": {
    "firstName": "Jan",
    "lastName": "Novák",
    "email": "jan@example.com",
    "phone": "+420 123 456 789",
    "company": "Restaurant ABC"
  },
  "items": [
    {
      "productId": "12345",
      "quantity": 10,
      "unitPrice": 149.90,
      "total": 1499.00
    }
  ],
  "total": 1499.00,
  "status": "pending",
  "createdAt": "2026-01-12T10:30:00Z"
}
```

**BlueJet Transformed**:
```json
{
  "orderNumber": "2026-001",
  "orderDate": "2026-01-12",
  "customerName": "Jan Novák",
  "customerEmail": "jan@example.com",
  "customerPhone": "+420 123 456 789",
  "company": "Restaurant ABC",
  "lineItems": [
    {
      "productId": "PASTA-CARBONARA-500G",
      "quantity": 10,
      "unitPrice": 149.90,
      "total": 1499.00
    }
  ],
  "totalAmount": 1499.00,
  "status": "Nabídka",
  "externalId": "shoptet:ORD-2026-001"
}
```

---

## Meeting Agenda (Tomorrow)

**Objectives:**
1. Confirm Shoptet Premium API availability and authentication method
2. Verify webhook event support (full list of available events)
3. Discuss data structure and any custom fields needed
4. Confirm timeline and migration approach
5. Establish support contact for technical issues
6. Review rate limits and SLA requirements

**Talking Points:**
- ✓ API documentation is comprehensive and well-structured
- ✓ Webhook-driven architecture enables real-time sync
- ✓ Private API token method is suitable for direct integration
- ✓ Rate limits are generous for typical business volume
- ✓ Error handling and retry logic are well-documented
- ? Confirm exact webhook event types available
- ? Discuss custom field mapping requirements
- ? Review timeline and go-live date

---

**Document Version**: 1.0
**Last Updated**: January 12, 2026
**Prepared by**: Technical Integration Team
**Status**: Ready for Shoptet Premium Team Review
