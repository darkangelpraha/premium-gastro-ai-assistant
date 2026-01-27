#!/bin/bash
# Run BlueJet → Qdrant Full Sync
# This syncs ALL products from BlueJet to Qdrant

set -e

echo "🚀 BlueJet → Qdrant Full Sync"
echo "=============================="
echo ""

cd ~/premium-gastro-ai-assistant

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "⚠️  No venv found. Run TEST_BLUEJET_SYNC.sh first."
    exit 1
fi

# Run sync
echo "📊 Starting full sync (this may take several minutes)..."
echo ""

python3 bluejet_qdrant_sync.py

echo ""
echo "✅ Sync complete!"
echo ""
echo "📊 Check results:"
echo "   curl http://192.168.1.129:6333/collections/bluejet_products"
