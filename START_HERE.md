# ⚡ START HERE - BlueJet Sync

## Run these commands:

```bash
# Go to the repo (wherever you have it on your Mac)
cd ~/premium-gastro-ai-assistant  # or wherever you cloned it

# Install dependencies
pip3 install -r requirements-bluejet-sync.txt

# Setup from 1Password (automatic)
./setup-bluejet-sync.sh

# Run the sync
source .env.bluejet
python3 bluejet_qdrant_sync.py
```

**That's it.**

---

## What this does:

1. Installs Python packages
2. Reads your BlueJet credentials from 1Password automatically
3. Syncs all products from BlueJet → Qdrant
4. Makes them searchable for Lucy

---

## If it works:

You'll see:
```
✅ BlueJet authentication successful
📥 Fetching products from BlueJet CRM...
✅ Total products fetched: 40123
✅ Sync complete: 40123 products uploaded to Qdrant
```

Then products are ready for meeting → offer automation.

---

## If it fails:

Paste the error here and I'll fix it.
