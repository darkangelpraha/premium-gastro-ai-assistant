#!/usr/bin/env python3
"""
Load BlueJet API documentation into Qdrant for semantic search
"""

import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import hashlib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# BlueJet API documentation sections
BLUEJET_API_DOCS = """
# BlueJet API V1.1-V1.3 Complete Documentation

## Authentication

**Endpoint:** POST https://VaseBluejetAplikace.cz/api/v1/users/authenticate

**Request:**
```json
{
  "tokenID": "string",
  "tokenHash": "string"
}
```

**Response:**
```json
{
  "succeeded": true,
  "token": "string (valid 24 hours)",
  "message": null
}
```

**Headers:** Content-Type: application/json, Accept: application/json
**Token Usage:** Include in X-Token header for all subsequent requests
**CRITICAL:** HTTPS required (HTTP returns 400 BadRequest)

---

## Get Products (Data Endpoint)

**Endpoint:** GET https://VaseBluejetAplikace.cz/api/v1/data

**Parameters:**
- no=217 (REQUIRED - object number for products)
- offset=0 (REQUIRED - starting row, 0-based)
- limit=200 (REQUIRED - max 200 records per request)
- fields=all (optional - get all columns)
- sort=+name or -name (optional - ascending/descending)
- condition=field|operator|value (optional - filters)

**Headers:**
- X-Token: [token from authentication]
- Accept: application/json

**Response Structure:**
```json
{
  "no": 217,
  "recordsCount": 40000,
  "rows": [
    {
      "offset": 0,
      "columns": [
        {"name": "ID", "value": "123"},
        {"name": "Nazev", "value": "Product Name"},
        {"name": "Kod", "value": "PROD-001"}
      ]
    }
  ]
}
```

**X-Total-Count Header:** Contains total matching records

---

## Product Fields (Czech/English)

Common field mappings:
- ID / id / productid - Product ID (GUID)
- Nazev / Name / name - Product name
- Kod / Code / code - Product code/SKU
- Popis / Description / description - Description
- Kategorie / Category / category - Category
- Dodavatel / Supplier / supplier - Supplier name
- Cena / Price / price - Price (Decimal)
- Mena / Currency / currency - Currency code (default: CZK)
- Dostupnost / Availability / availability - Availability status
- Jednotka / Unit / unit - Unit of measure (default: ks)

---

## Object Numbers (Entity Types)

- 217: Products (Produkty)
- 222: Contacts (Kontakty)
- 225: Companies (Společnosti)
- 227: Activities (Aktivity)
- 243: Addresses (Adresy)
- 250: Price Lists (Ceníky)
- 293: Issued Offers (Nabídky)
- 321: Received Orders (Přijaté objednávky)
- 323: Issued Invoices (Vydané faktury)
- 328: Received Invoices (Přijaté faktury)

---

## Error Handling

- 200 OK: Success
- 400 BadRequest: HTTPS required or invalid parameters
- 401 Unauthorized: Token expired or invalid - re-authenticate
- 403 Forbidden: Invalid credentials
- 429 Too Many Requests: Rate limited - retry with backoff

---

## Best Practices

1. Always use HTTPS (not HTTP)
2. Token valid for exactly 24 hours - track expiry
3. Max 200 records per request for pagination
4. Max 10 objects per batch for insert/update
5. Use X-Total-Count header for total record count
6. Include X-Token in all data requests
7. Re-authenticate automatically on 401 responses

---

## Rate Limiting

- Not explicitly documented
- Recommended: 2 second delay between requests
- Handle 429 responses with exponential backoff

---

## Pagination Strategy

```python
offset = 0
limit = 200
while True:
    products = fetch(no=217, offset=offset, limit=limit)
    if not products or len(products) < limit:
        break
    offset += limit
    time.sleep(2)  # Rate limiting
```

---

## Common Issues

1. **401 "Musí být vyplněny přihlašovací údaje"**
   - Solution: Use JSON format with tokenID and tokenHash

2. **405 Method Not Allowed**
   - Solution: Check HTTP method (GET for data, POST for auth)
   - Solution: Include required parameters (no, offset, limit)

3. **400 BadRequest**
   - Solution: Ensure using HTTPS not HTTP
   - Solution: Validate all required parameters present

4. **Empty products array**
   - Solution: Check no=217 for products
   - Solution: Parse DataSet.rows[].columns[] structure
   - Solution: Map Czech field names (Nazev, Kod, etc)

---

## Complete Working Example

```python
# 1. Authenticate
response = requests.post(
    'https://czeco.bluejet.cz/api/v1/users/authenticate',
    json={'tokenID': 'xxx', 'tokenHash': 'yyy'},
    headers={'Content-Type': 'application/json', 'Accept': 'application/json'}
)
token = response.json()['token']

# 2. Fetch products
response = requests.get(
    'https://czeco.bluejet.cz/api/v1/data',
    params={'no': 217, 'offset': 0, 'limit': 200, 'fields': 'all'},
    headers={'X-Token': token, 'Accept': 'application/json'}
)

# 3. Parse response
data = response.json()
total_count = response.headers['X-Total-Count']
for row in data['rows']:
    product = {col['name']: col['value'] for col in row['columns']}
    print(product['Nazev'], product['Kod'])
```
"""


def generate_embedding(text: str) -> list[float]:
    """Generate simple hash-based embedding"""
    hash_obj = hashlib.sha256(text.encode())
    hash_bytes = hash_obj.digest()

    embedding = []
    for i in range(0, len(hash_bytes), 2):
        value = int.from_bytes(hash_bytes[i:i+2], 'big')
        embedding.append(float(value) / 65535.0)

    while len(embedding) < 1536:
        embedding.append(0.0)

    return embedding[:1536]


def load_docs_to_qdrant():
    """Load BlueJet API docs into Qdrant"""
    logger.info("Connecting to Qdrant...")
    client = QdrantClient(host="192.168.1.129", port=6333)

    collection_name = "bluejet_api_docs"

    # Create collection if doesn't exist
    try:
        collections = client.get_collections().collections
        if collection_name not in [c.name for c in collections]:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )
            logger.info(f"✅ Created collection: {collection_name}")
    except Exception as e:
        logger.error(f"Error creating collection: {e}")
        return

    # Split docs into sections
    sections = BLUEJET_API_DOCS.split('---')

    points = []
    for idx, section in enumerate(sections):
        section = section.strip()
        if not section:
            continue

        # Extract title from first line
        lines = section.split('\n')
        title = lines[0].replace('#', '').strip() if lines else f"Section {idx}"

        embedding = generate_embedding(section)

        point = PointStruct(
            id=idx,
            vector=embedding,
            payload={
                'title': title,
                'content': section,
                'type': 'bluejet_api_documentation',
                'source': 'https://public.bluejet.cz/public/api/bluejet-api.html'
            }
        )
        points.append(point)

    # Upload to Qdrant
    try:
        client.upsert(collection_name=collection_name, points=points)
        logger.info(f"✅ Loaded {len(points)} documentation sections to Qdrant")

        # Verify
        collection_info = client.get_collection(collection_name)
        logger.info(f"Collection now has {collection_info.points_count} points")

    except Exception as e:
        logger.error(f"❌ Failed to load docs: {e}")


if __name__ == "__main__":
    load_docs_to_qdrant()
