#!/bin/bash
#
# BlueJet → Qdrant Production Sync - Easy Runner
# ==============================================
#
# Features:
# - Auto venv setup and activation
# - Dependency installation
# - Credential validation
# - Production sync execution
#

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 BlueJet → Qdrant Production Sync"
echo "======================================"
echo ""

# 1. Check/create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
    echo ""
fi

# 2. Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# 3. Check/install dependencies
REQUIREMENTS="requirements-sync-pro.txt"
if [ -f "$REQUIREMENTS" ]; then
    echo "📥 Checking dependencies..."

    # Check if key packages are installed
    if ! python3 -c "import openai" 2>/dev/null; then
        echo "📦 Installing production dependencies (this may take a few minutes)..."
        pip install -q --upgrade pip
        pip install -q -r "$REQUIREMENTS"
        echo "✅ Dependencies installed"
    else
        echo "✅ Dependencies already installed"
    fi
    echo ""
fi

# 4. Check credentials
if [ ! -f ".env.bluejet" ]; then
    echo "❌ Credentials not found!"
    echo ""
    echo "Run setup first:"
    echo "  ./setup-bluejet-sync.sh"
    echo ""
    exit 1
fi

# 5. Validate OpenAI API key
if ! grep -q "OPENAI_API_KEY=sk-" .env.bluejet 2>/dev/null; then
    echo "⚠️  WARNING: OpenAI API key not found or invalid!"
    echo ""
    echo "OpenAI embeddings provide TRUE semantic search."
    echo "Without it, falling back to local/hash embeddings."
    echo ""
    echo "To fix, run:"
    echo "  ./setup-bluejet-sync.sh"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 6. Check config file
if [ ! -f "config.yaml" ]; then
    echo "⚠️  config.yaml not found, using defaults"
    echo ""
fi

# 7. Run production sync
echo "🔄 Starting production sync..."
echo ""
echo "Features enabled:"
echo "  ✅ Real OpenAI embeddings (semantic search)"
echo "  ✅ Incremental sync (fast daily updates)"
echo "  ✅ Resume capability (checkpoint/restore)"
echo "  ✅ Data validation (quality checks)"
echo "  ✅ Parallel processing (3x faster)"
echo "  ✅ Comprehensive monitoring"
echo ""
echo "────────────────────────────────────────────"
echo ""

# Pass arguments to production script
python3 bluejet_sync_pro.py "$@"

EXIT_CODE=$?

echo ""
echo "────────────────────────────────────────────"
echo ""

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Sync completed successfully!"
    echo ""
    echo "Check logs:"
    echo "  - bluejet_sync.log       (full sync log)"
    echo "  - sync_metrics.json      (performance metrics)"
    echo "  - invalid_records.jsonl  (data quality issues)"
else
    echo "❌ Sync failed with exit code: $EXIT_CODE"
    echo ""
    echo "Check logs for details:"
    echo "  tail -n 50 bluejet_sync.log"
fi

echo ""
exit $EXIT_CODE
