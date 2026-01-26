#!/bin/bash
# Lucy Health Check & Startup Script
# Run this on your Mac to diagnose and start Lucy

LUCY_DIR="/Users/premiumgastro/Projects/Mem0/lucy_system"

echo "🔍 Lucy Health Check"
echo "===================="
echo ""

# Check if Lucy exists
if [ ! -d "$LUCY_DIR" ]; then
    echo "❌ Lucy not found at $LUCY_DIR"
    exit 1
fi

cd "$LUCY_DIR"
echo "✅ Found Lucy at $LUCY_DIR"
echo ""

# Check Python
echo "🐍 Python Check:"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ $PYTHON_VERSION"
else
    echo "❌ Python3 not found"
    exit 1
fi
echo ""

# Check virtual environment
echo "📦 Virtual Environment:"
if [ -d "venv" ]; then
    echo "✅ venv exists"
    source venv/bin/activate 2>/dev/null || echo "⚠️  venv activation failed (might be OK)"
else
    echo "⚠️  No venv found - creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -q -r requirements.txt
    echo "✅ venv created and dependencies installed"
fi
echo ""

# Check .env file
echo "🔑 Environment Variables:"
if [ -f ".env" ]; then
    echo "✅ .env file exists"

    # Check critical variables
    MISSING_VARS=()

    if ! grep -q "ANTHROPIC_API_KEY=.*[A-Za-z0-9]" .env; then
        MISSING_VARS+=("ANTHROPIC_API_KEY")
    fi

    if ! grep -q "QDRANT_HOST=192.168.1.129" .env; then
        MISSING_VARS+=("QDRANT_HOST")
    fi

    if [ ${#MISSING_VARS[@]} -gt 0 ]; then
        echo "⚠️  Missing variables:"
        for var in "${MISSING_VARS[@]}"; do
            echo "   - $var"
        done
        echo ""
        echo "💡 Run: ./setup-from-1password.sh to auto-populate from 1Password"
    else
        echo "✅ Core variables configured"
    fi
else
    echo "❌ No .env file found"
    echo "💡 Run: ./setup-from-1password.sh"
    exit 1
fi
echo ""

# Check Qdrant connectivity
echo "🗄️  Qdrant Database:"
if curl -s http://192.168.1.129:6333/collections > /dev/null 2>&1; then
    COLLECTIONS=$(curl -s http://192.168.1.129:6333/collections | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('result', {}).get('collections', [])))" 2>/dev/null || echo "0")
    echo "✅ Qdrant accessible at 192.168.1.129:6333"
    echo "   Collections: $COLLECTIONS"
else
    echo "❌ Qdrant not accessible at 192.168.1.129:6333"
    echo "💡 Make sure your NAS is on and VPN is connected (if needed)"
fi
echo ""

# Check if Lucy is already running
echo "🤖 Lucy Status:"
if [ -f "lucy.log" ]; then
    LAST_LOG=$(tail -1 lucy.log 2>/dev/null)
    LOG_SIZE=$(du -h lucy.log | cut -f1)
    echo "📝 Log file: $LOG_SIZE"
fi

if pgrep -f "lucy_orchestrator.py" > /dev/null; then
    PID=$(pgrep -f "lucy_orchestrator.py")
    echo "✅ Lucy is RUNNING (PID: $PID)"
    echo ""
    echo "To stop: ./stop-lucy.sh"
    echo "To check status: ./status-lucy.sh"
    echo "To view logs: tail -f lucy.log"
else
    echo "⏸️  Lucy is NOT running"
    echo ""
    echo "To start: ./start-lucy.sh"
fi
echo ""

# Summary
echo "📊 Summary:"
echo "==========="

READY=true

if [ ! -f ".env" ]; then
    echo "❌ Missing .env file"
    READY=false
fi

if ! curl -s http://192.168.1.129:6333/collections > /dev/null 2>&1; then
    echo "❌ Qdrant not accessible"
    READY=false
fi

if [ "$READY" = true ]; then
    echo "✅ Lucy is READY to run"
    echo ""
    echo "🚀 Next step:"
    echo "   ./start-lucy.sh"
else
    echo "⚠️  Lucy needs configuration"
    echo ""
    echo "🔧 Fix steps:"
    echo "   1. Run: ./setup-from-1password.sh"
    echo "   2. Check Qdrant: ping 192.168.1.129"
    echo "   3. Try health check again"
fi
