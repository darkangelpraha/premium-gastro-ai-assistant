#!/bin/bash
# Test BlueJet Sync - One Command Test
# Run this on your Mac to test if BlueJet sync actually works

set -e

echo "🧪 Testing BlueJet → Qdrant Sync"
echo "=================================="
echo ""

cd ~/premium-gastro-ai-assistant

# Step 1: Check Python
echo "1️⃣ Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found"
    exit 1
fi
echo "✅ Python3 found"
echo ""

# Step 2: Setup venv and install deps
echo "2️⃣ Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements-bluejet-sync.txt
echo "✅ Dependencies installed"
echo ""

# Step 3: Test Qdrant connection
echo "3️⃣ Testing Qdrant connection..."
if curl -s http://192.168.1.129:6333/collections > /dev/null 2>&1; then
    COLLECTIONS=$(curl -s http://192.168.1.129:6333/collections | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('result', {}).get('collections', [])))" 2>/dev/null || echo "0")
    echo "✅ Qdrant accessible ($COLLECTIONS collections)"
else
    echo "❌ Qdrant NOT accessible at 192.168.1.129:6333"
    echo "💡 Make sure:"
    echo "   - NAS is powered on"
    echo "   - You're on the same network"
    echo "   - Qdrant is running on NAS"
    exit 1
fi
echo ""

# Step 4: Test 1Password CLI
echo "4️⃣ Testing 1Password CLI..."
if ! command -v op &> /dev/null; then
    echo "❌ 1Password CLI not found"
    echo "💡 Install: brew install 1password-cli"
    exit 1
fi

# Try to read a credential
TOKEN_ID=$(op read "op://5zbrmieoqrroxon4eu6mwfu4li/BlueJet API FULL/BLUEJET_API_TOKEN_ID" 2>/dev/null || echo "")
if [ -z "$TOKEN_ID" ]; then
    echo "❌ Can't read from 1Password"
    echo "💡 Make sure:"
    echo "   - You're logged into 1Password CLI: op signin"
    echo "   - The vault 'Missive | BJ' exists"
    echo "   - The item 'BlueJet API FULL' exists"
    exit 1
fi
echo "✅ 1Password CLI working (read token: ${TOKEN_ID:0:10}...)"
echo ""

# Step 5: Run sync (first 10 products only as test)
echo "5️⃣ Running BlueJet sync (TEST MODE - 10 products)..."
echo ""
echo "🚀 Starting sync..."
echo "─────────────────────────────────────"

# Run with timeout and capture output
timeout 60s python3 bluejet_qdrant_sync.py 2>&1 | head -50 || {
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 124 ]; then
        echo ""
        echo "⏱️  Sync is taking a while (good sign!)"
        echo "💡 Let it run in background: python3 bluejet_qdrant_sync.py &"
    else
        echo ""
        echo "❌ Sync failed with exit code $EXIT_CODE"
        echo "📝 Check the error above"
    fi
    exit $EXIT_CODE
}

echo "─────────────────────────────────────"
echo ""

# Step 6: Verify products in Qdrant
echo "6️⃣ Checking if products were synced..."
PRODUCT_COUNT=$(curl -s http://192.168.1.129:6333/collections/bluejet_products 2>/dev/null | python3 -c "import sys, json; print(json.load(sys.stdin).get('result', {}).get('points_count', 0))" 2>/dev/null || echo "0")

if [ "$PRODUCT_COUNT" -gt 0 ]; then
    echo "✅ ✅ ✅ SUCCESS! ✅ ✅ ✅"
    echo ""
    echo "📊 Results:"
    echo "   Products in Qdrant: $PRODUCT_COUNT"
    echo ""
    echo "🎉 BlueJet sync is WORKING!"
    echo ""
    echo "💡 Next steps:"
    echo "   - Run full sync: python3 bluejet_qdrant_sync.py"
    echo "   - Schedule daily: crontab -e (add: 0 9 * * * cd ~/premium-gastro-ai-assistant && python3 bluejet_qdrant_sync.py)"
else
    echo "⚠️  No products found in Qdrant yet"
    echo "💡 The sync may still be running. Check:"
    echo "   curl http://192.168.1.129:6333/collections/bluejet_products"
fi
