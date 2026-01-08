# Bluejet API Complete Reference

**Official Documentation**: https://public.bluejet.cz/public/api/bluejet-api.html
**API Base URL**: `https://czeco.bluejet.cz/api/v1`
**Protocol**: HTTPS only (HTTP returns 400 BadRequest)

---

## Authentication

### Get Authentication Token

**Endpoint**: `POST /api/v1/users/authenticate`

**Request**:
```json
{
  "tokenID": "your_token_id",
  "tokenHash": "your_token_hash"
}
```

**Response**:
```json
{
  "succeeded": true,
  "token": "24-hour-session-token",
  "message": ""
}
```

**Token Usage**: Include in all subsequent requests via `X-Token` header

**Token Lifetime**: 24 hours

---

## Core Operations

### 1. Search/Read Records

**Method**: `GET /api/v1/data`

**Required Parameters**:
- `no` - Evidence type number (e.g., 222 for Contacts, 225 for Companies)
- `offset` - Starting record (pagination)
- `limit` - Number of records to return

**Optional Parameters**:
- `sort` - Sort order (e.g., `Name ASC`, `CreatedDate DESC`)
- `fields` - Comma-separated field names to return
- `condition` - Filter condition (see operators below)

**Example**:
```
GET /api/v1/data?no=225&offset=0&limit=50&condition=Name contains "Gastro"&sort=Name ASC
```

**Response**:
```json
{
  "dataObjectResult": {
    "dataObjectRows": [
      {
        "id": "unique-guid",
        "no": 225,
        "fields": {
          "Name": "Premium Gastro s.r.o.",
          "ICO": "12345678",
          "Email": "info@premium-gastro.com"
        }
      }
    ],
    "recordsCount": 150
  }
}
```

**Response Headers**:
- `X-Total-Count` - Total number of matching records

### Supported Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Equals | `Status = "Active"` |
| `<>` or `!=` | Not equals | `Status != "Deleted"` |
| `contains` | Contains substring | `Name contains "Gastro"` |
| `!contains` | Does not contain | `Email !contains "@gmail"` |
| `starts` | Starts with | `Code starts "PG-"` |
| `!starts` | Does not start with | `Code !starts "OLD-"` |
| `<` | Less than | `Price < 1000` |
| `>` | Greater than | `Price > 500` |
| `<=` | Less than or equal | `Quantity <= 10` |
| `>=` | Greater than or equal | `Quantity >= 1` |

**Complex Conditions**: Combine with `AND` and `OR`
```
Status = "Active" AND (Category = "VIP" OR TotalOrders > 10)
```

---

### 2. Create Records

**Method**: `POST /api/v1/data`

**Max Objects**: 10 per request

**Request**:
```json
{
  "dataObjectRows": [
    {
      "no": 225,
      "fields": {
        "Name": "New Customer s.r.o.",
        "ICO": "87654321",
        "Email": "contact@newcustomer.cz",
        "Phone": "+420 123 456 789"
      }
    }
  ]
}
```

**Response**:
```json
{
  "dataObjectResult": {
    "dataObjectRows": [
      {
        "action": "inserted",
        "id": "new-guid-here",
        "no": 225,
        "reference": "$1$"
      }
    ]
  }
}
```

**Cross-Referencing**: Use `$1$`, `$2$`, etc. to reference previously created objects in the same request

**Example - Create Company with Contact**:
```json
{
  "dataObjectRows": [
    {
      "no": 225,
      "reference": "$1$",
      "fields": {
        "Name": "ABC s.r.o."
      }
    },
    {
      "no": 222,
      "fields": {
        "FirstName": "Jan",
        "LastName": "Novák",
        "CompanyID": "$1$"
      }
    }
  ]
}
```

---

### 3. Update Records

**Method**: `PUT /api/v1/data`

**Requirement**: Must include primary key field (usually `ID`)

**Request**:
```json
{
  "dataObjectRows": [
    {
      "no": 225,
      "fields": {
        "ID": "existing-guid",
        "Email": "newemail@company.cz",
        "Phone": "+420 999 888 777"
      }
    }
  ]
}
```

**Response**:
```json
{
  "dataObjectResult": {
    "dataObjectRows": [
      {
        "action": "updated",
        "id": "existing-guid",
        "no": 225
      }
    ]
  }
}
```

---

### 4. Insert or Update (Upsert)

**Method**: `POST /api/v1/data/insertorupdate`

**Feature**: Uses `condition` to determine if record exists

**Request**:
```json
{
  "dataObjectRows": [
    {
      "no": 225,
      "condition": "ICO = '12345678'",
      "fields": {
        "ICO": "12345678",
        "Name": "Updated Company Name",
        "Email": "updated@company.cz"
      }
    }
  ]
}
```

**Behavior**:
- If `condition` matches existing record → **UPDATE**
- If no match found → **INSERT**

---

### 5. Delete Records

**Method 1**: `DELETE /api/v1/data?no={no}&id={id}`

**Example**:
```
DELETE /api/v1/data?no=225&id=guid-to-delete
```

**Method 2** (for bulk deletion): `POST /api/v1/data/remove`

**Request**:
```json
{
  "dataObjectRows": [
    {
      "no": 225,
      "id": "guid-1"
    },
    {
      "no": 222,
      "id": "guid-2"
    }
  ]
}
```

---

## Evidence Types (Object Numbers)

### CRM - Customer Relationship Management

| No | Evidence Type | Czech Name |
|----|---------------|------------|
| 222 | Contacts | Kontakty |
| 225 | Companies | Firmy |
| 227 | Activities | Aktivity |
| 276 | Contracts | Smlouvy |
| 277 | Contract Types | Typy smluv |

### Sales & Commerce

| No | Evidence Type | Czech Name |
|----|---------------|------------|
| 217 | Products | Produkty |
| 230 | Offers | Nabídky |
| 293 | Offer Templates | Šablony nabídek |
| 321 | Orders | Objednávky |
| 356 | Purchase Orders | Příjemky |

### Invoicing & Finance

| No | Evidence Type | Czech Name |
|----|---------------|------------|
| 323 | Issued Invoices | Faktury vydané |
| 324 | Received Invoices | Faktury přijaté |
| 328 | Proforma Invoices | Zálohové faktury |
| 329 | Credit Notes | Dobropisy |

### Project Management

| No | Evidence Type | Czech Name |
|----|---------------|------------|
| 332 | Projects | Projekty |
| 383 | Plans | Plány |

**70+ additional evidence types** available - see full documentation for complete list

---

## Field Types

| Type | Description | Example |
|------|-------------|---------|
| NVarChar | Text string | `"Premium Gastro"` |
| Bit | Boolean | `true` / `false` |
| DateTime | Date and time | `"2026-01-08T10:30:00"` |
| Money / Decimal | Currency/numbers | `1250.50` |
| UniqueIdentifier | GUID | `"a1b2c3d4-e5f6-..."` |
| Int | Integer | `42` |
| NText(MAX) | Long text | `"Long description..."` |
| PickUp | Enumeration | Predefined values |

**Field Types**:
- **Standard Fields**: Stored in database, can be written
- **Virtual Fields**: Calculated/aggregated, read-only, searchable only

---

## Practical Examples

### Example 1: Find All VIP Customers

```bash
curl -X GET "https://czeco.bluejet.cz/api/v1/data?no=225&condition=Category='VIP'&offset=0&limit=100" \
  -H "X-Token: your-session-token" \
  -H "Content-Type: application/json"
```

### Example 2: Create New Contact for Existing Company

```bash
curl -X POST "https://czeco.bluejet.cz/api/v1/data" \
  -H "X-Token: your-session-token" \
  -H "Content-Type: application/json" \
  -d '{
    "dataObjectRows": [{
      "no": 222,
      "fields": {
        "FirstName": "Petr",
        "LastName": "Novotný",
        "Email": "petr@example.cz",
        "CompanyID": "existing-company-guid"
      }
    }]
  }'
```

### Example 3: Update Invoice Status

```bash
curl -X PUT "https://czeco.bluejet.cz/api/v1/data" \
  -H "X-Token: your-session-token" \
  -H "Content-Type: application/json" \
  -d '{
    "dataObjectRows": [{
      "no": 323,
      "fields": {
        "ID": "invoice-guid",
        "Status": "Paid",
        "PaymentDate": "2026-01-08T14:00:00"
      }
    }]
  }'
```

### Example 4: Search Products by Price Range

```bash
curl -X GET "https://czeco.bluejet.cz/api/v1/data?no=217&condition=Price>=500 AND Price<=2000&sort=Price ASC&offset=0&limit=50" \
  -H "X-Token: your-session-token"
```

---

## Error Handling

**HTTP Status Codes**:
- `200` - Success
- `400` - Bad Request (check HTTPS, parameters)
- `401` - Unauthorized (token expired or invalid)
- `404` - Not Found
- `500` - Server Error

**Error Response Format**:
```json
{
  "succeeded": false,
  "message": "Špatné přihlašovací údaje."
}
```

---

## Rate Limits & Best Practices

1. **Batch Operations**: Use up to 10 objects per request when creating/updating
2. **Pagination**: Use `offset` and `limit` for large datasets (recommended: 50-100 per page)
3. **Field Selection**: Use `fields` parameter to request only needed fields
4. **Token Management**: Cache 24-hour token, refresh before expiry
5. **Error Retry**: Implement exponential backoff for failed requests

---

## Integration with Premium Gastro

### Common Workflows

**Daily Customer Sync**:
1. GET companies (no=225) modified since last sync
2. Update local Supabase database
3. Flag VIP customers for priority handling

**Order Processing**:
1. GET new orders (no=321) from Bluejet
2. Create invoice (no=323) via POST
3. Update order status via PUT
4. Sync to fulfillment system

**Product Catalog Sync**:
1. GET all products (no=217)
2. Update Shopify/e-commerce catalog
3. Sync inventory levels

**Invoice Generation**:
1. Create invoice (no=323) from order data
2. Generate PDF via Bluejet
3. Send via email automation
4. Track payment status

---

## Python SDK Usage

Using `bluejet_connect.py`:

```python
from bluejet_connect import BluejetAPIClient

# Initialize and authenticate
client = BluejetAPIClient()
if client.authenticate():

    # Get VIP customers
    customers = client.get_data(
        no=225,
        condition="Category='VIP'",
        limit=100
    )

    # Create new contact
    new_contact = client.create_record(
        no=222,
        fields={
            "FirstName": "Jan",
            "LastName": "Dvořák",
            "Email": "jan@example.cz"
        }
    )

    # Update invoice
    client.update_record(
        no=323,
        id="invoice-guid",
        fields={"Status": "Paid"}
    )
```

---

## Security Notes

✅ **Always use HTTPS** - HTTP requests are rejected
✅ **Store credentials in 1Password** - Never commit to code
✅ **Rotate tokens** - Implement 24-hour token refresh
✅ **Validate input** - Sanitize all user input before API calls
✅ **Log access** - Track all API operations for audit trail

---

## Additional Resources

- **Official Documentation**: https://public.bluejet.cz/public/api/bluejet-api.html
- **Bluejet Website**: https://www.bluejet.cz/
- **Support**: Contact COMPEKON for API access enablement

---

**Last Updated**: 2026-01-08
**API Version**: v1
**Documentation Source**: Official Bluejet API Reference
