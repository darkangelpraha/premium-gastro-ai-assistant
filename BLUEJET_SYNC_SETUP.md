# BlueJet → Qdrant Product Sync

**Automatically syncs your 40k products from BlueJet CRM to Qdrant for semantic search.**

---

## 🚀 QUICK START (5 minutes)

### Step 1: Install Dependencies
```bash
cd /Users/premiumgastro  # Or wherever your code is
pip3 install -r requirements-bluejet-sync.txt
```

### Step 2: Setup Credentials from 1Password
```bash
chmod +x setup-bluejet-sync.sh
./setup-bluejet-sync.sh
```

This will retrieve credentials from your 1Password AI vault:
- `op://AI/BlueJet API/url`
- `op://AI/BlueJet API/tokenID`
- `op://AI/BlueJet API/tokenHash`

### Step 3: First Sync (Manual)
```bash
# Load environment variables
source .env.bluejet

# Run sync
python3 bluejet_qdrant_sync.py
```

**Expected output:**
```
============================================================
BlueJet → Qdrant Product Sync Service
============================================================
✅ BlueJet authentication successful
📥 Fetching products from BlueJet CRM...
Progress: 1000 products fetched...
Progress: 2000 products fetched...
...
✅ Total products fetched: 40123
📤 Syncing 40123 products to Qdrant...
Uploaded batch: 100/40123 products
...
✅ Sync complete: 40123 products uploaded to Qdrant
============================================================
✅ SYNC COMPLETE
   Products fetched: 40123
   Products uploaded: 40123
   Collection: bluejet_products
   Qdrant: 192.168.1.129:6333
============================================================
```

---

## ⚙️ 1PASSWORD SETUP

### If Credentials Path is Different:

1. **Find your BlueJet credentials in 1Password:**
   ```bash
   op item list --vault AI | grep -i bluejet
   ```

2. **Check credential structure:**
   ```bash
   op item get "BlueJet API" --vault AI
   ```

3. **Update paths in `setup-bluejet-sync.sh`** if needed

### If BlueJet Credentials Don't Exist in 1Password:

**Add them manually:**

1. **Get credentials from BlueJet:**
   - Login to your BlueJet instance
   - Go to Admin → API Settings
   - Generate new API token
   - Copy Token ID and Token Hash

2. **Add to 1Password:**
   ```bash
   op item create \
     --vault AI \
     --category "API Credential" \
     --title "BlueJet API" \
     url="https://your-instance.bluejet.cz" \
     tokenID="your_token_id" \
     tokenHash="your_token_hash"
   ```

3. **Run setup again:**
   ```bash
   ./setup-bluejet-sync.sh
   ```

---

## 🔄 AUTOMATIC SYNC (Runs Every 6 Hours)

### Option A: Cron Job (Mac/Linux)
```bash
# Edit crontab
crontab -e

# Add this line (runs every 6 hours)
0 */6 * * * cd /Users/premiumgastro && source .env.bluejet && python3 bluejet_qdrant_sync.py >> /tmp/bluejet-sync.log 2>&1
```

### Option B: Docker Container (Recommended for NAS)
```bash
# Build Docker image
docker build -t bluejet-sync -f- . <<EOF
FROM python:3.11-slim
WORKDIR /app
COPY requirements-bluejet-sync.txt .
RUN pip install -r requirements-bluejet-sync.txt
COPY bluejet_qdrant_sync.py .
CMD ["python3", "bluejet_qdrant_sync.py"]
EOF

# Run on NAS (every 6 hours)
docker run -d \
  --name bluejet-sync \
  --restart unless-stopped \
  --env-file .env.bluejet \
  -v /path/to/logs:/app/logs \
  bluejet-sync \
  sh -c "while true; do python3 bluejet_qdrant_sync.py; sleep 21600; done"
```

### Option C: n8n Workflow
1. Open http://localhost:5678
2. Create new workflow: "BlueJet Sync Schedule"
3. Trigger: Every 6 hours
4. Action: Execute Command
   ```bash
   cd /Users/premiumgastro && source .env.bluejet && python3 bluejet_qdrant_sync.py
   ```

---

## 🔍 TESTING PRODUCT SEARCH

### Test in Python:
```python
from qdrant_client import QdrantClient

# Connect to Qdrant
client = QdrantClient(host="192.168.1.129", port=6333)

# Search for products
results = client.search(
    collection_name="bluejet_products",
    query_text="porcelánové talíře pro restaurace",
    limit=10
)

# Display results
for result in results:
    print(f"{result.payload['name']} - {result.payload['supplier']}")
    print(f"  Cena: {result.payload['price']} {result.payload['currency']}")
    print(f"  Dostupnost: {result.payload['availability']}")
    print()
```

### Test with Lucy:
```bash
# Once Lucy is deployed
curl -X POST http://localhost:8080/query -d '{
  "query": "Najdi mi porcelánové talíře vhodné pro italskou restauraci",
  "search_products": true
}'
```

---

## 🐛 TROUBLESHOOTING

### Error: "Missing BlueJet credentials"
```bash
# Check 1Password vault
op item list --vault AI

# Verify paths
op read "op://AI/BlueJet API/url"
```

### Error: "Failed to connect to Qdrant"
```bash
# Test Qdrant connection
curl http://192.168.1.129:6333/collections

# Check if Qdrant is running on NAS
ssh user@192.168.1.129
docker ps | grep qdrant
```

### Error: "Authentication failed"
```bash
# Verify BlueJet credentials are correct
# Login to BlueJet web interface manually
# Generate new API token if needed
```

### Products Not Updating
```bash
# Check last sync time
curl http://192.168.1.129:6333/collections/bluejet_products | jq

# Manual sync
python3 bluejet_qdrant_sync.py

# Check logs
tail -f /tmp/bluejet-sync.log
```

---

## 📊 MONITORING

### Check Sync Status:
```bash
# Check Qdrant collection
curl http://192.168.1.129:6333/collections/bluejet_products

# Check last sync time
curl http://192.168.1.129:6333/collections/bluejet_products/points/scroll | jq '.result.points[0].payload.last_updated'
```

### View Sync Logs:
```bash
# If using cron
tail -f /tmp/bluejet-sync.log

# If using Docker
docker logs -f bluejet-sync
```

---

## 🎯 NEXT STEPS

Once products are syncing:

1. **Connect Lucy to product search**
2. **Build meeting → offer workflow**
3. **Test semantic product search** ("Italian restaurant plates" finds relevant items)
4. **Add availability checking** (real-time from suppliers)

---

## 📚 BlueJet API Documentation

- Official API Docs: https://public.bluejet.cz/public/api/bluejet-api.html
- Authentication: XML-based POST requests
- Rate Limits: Unknown (monitor your usage)
- Support: COMPEKON support if issues

---

## 🔐 SECURITY NOTES

✅ **DO:**
- Keep `.env.bluejet` in `.gitignore`
- Use 1Password for credential management
- Rotate API tokens periodically
- Monitor sync logs for unauthorized access

❌ **DON'T:**
- Commit `.env.bluejet` to git
- Share API tokens in Slack/email
- Use production tokens in development
- Hardcode credentials in code

---

**Questions? Check the sync works first, then we build the meeting workflow on top of it.**
