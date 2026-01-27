#!/bin/bash
# Run BlueJet → Qdrant Full Sync
# This syncs ALL products from BlueJet to Qdrant
# Can be run from anywhere - handles venv automatically

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 BlueJet → Qdrant Full Sync"
echo "=============================="
echo "Working directory: $SCRIPT_DIR"
echo ""

# Check if venv exists, create if not
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📥 Installing dependencies..."
    pip install -q -r requirements-bluejet-sync.txt
else
    source venv/bin/activate
fi

echo "✅ Virtual environment activated"
echo ""

# Check which sync to run
if [ "$1" == "--full" ]; then
    echo "📊 Starting FULL sync (all entities: products, contacts, companies, etc.)..."
    echo "⏱️  This will take 2-3 hours for all data..."
    echo ""
    python3 bluejet_full_sync.py
else
    echo "📊 Starting products sync..."
    echo "⏱️  Expected time: 40-60 minutes for 109k products..."
    echo ""
    python3 bluejet_qdrant_sync.py
fi

echo ""
echo "✅ Sync complete!"
echo ""
echo "📊 Check results:"
echo "   curl http://192.168.1.129:6333/collections/bluejet_products"
echo ""
echo "💡 Run with --full flag to sync ALL BlueJet entities (not just products)"
