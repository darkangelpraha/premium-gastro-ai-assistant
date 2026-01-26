#!/bin/bash
# ONE-COMMAND Lucy Setup & Start
# This script does EVERYTHING needed to get Lucy running

set -e

LUCY_DIR="/Users/premiumgastro/Projects/Mem0/lucy_system"

echo "🚀 Lucy One-Command Startup"
echo "============================"
echo ""

# 1. Navigate to Lucy
cd "$LUCY_DIR" || { echo "❌ Lucy directory not found"; exit 1; }
echo "✅ Found Lucy"

# 2. Setup Python venv if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "✅ Virtual environment ready"

# 3. Install/update dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ Dependencies installed"

# 4. Setup environment variables from 1Password
if [ ! -f ".env" ] || grep -q "↓ Anthropic" .env; then
    echo "🔑 Setting up credentials from 1Password..."
    if [ -x "./setup-from-1password.sh" ]; then
        ./setup-from-1password.sh
        echo "✅ Credentials configured"
    else
        echo "⚠️  Couldn't auto-setup credentials"
        echo "💡 You may need to manually edit .env file"
    fi
else
    echo "✅ Credentials already configured"
fi

# 5. Test Qdrant connection
echo "🗄️  Testing Qdrant connection..."
if curl -s http://192.168.1.129:6333/collections > /dev/null 2>&1; then
    echo "✅ Qdrant is accessible"
else
    echo "⚠️  Qdrant not accessible (Lucy will still start, but won't have knowledge base)"
fi

# 6. Stop any existing Lucy instance
if pgrep -f "lucy_orchestrator.py" > /dev/null; then
    echo "🛑 Stopping existing Lucy instance..."
    ./stop-lucy.sh 2>/dev/null || pkill -f "lucy_orchestrator.py"
    sleep 2
fi

# 7. Start Lucy
echo "🤖 Starting Lucy..."
if [ -x "./start-lucy.sh" ]; then
    ./start-lucy.sh
else
    # Fallback: start Lucy directly
    nohup python3 lucy_orchestrator.py > lucy.log 2>&1 &
    echo $! > lucy.pid
fi

sleep 3

# 8. Verify Lucy is running
if pgrep -f "lucy_orchestrator.py" > /dev/null; then
    PID=$(pgrep -f "lucy_orchestrator.py")
    echo ""
    echo "✅ ✅ ✅ LUCY IS RUNNING! ✅ ✅ ✅"
    echo ""
    echo "📊 Status:"
    echo "   PID: $PID"
    echo "   Log: tail -f $LUCY_DIR/lucy.log"
    echo "   Stop: cd $LUCY_DIR && ./stop-lucy.sh"
    echo ""
    echo "💬 Test Lucy:"
    echo "   ./lucy query \"How do I use Qdrant?\""
    echo ""

    # Show recent log
    echo "📝 Recent activity:"
    tail -5 lucy.log
else
    echo ""
    echo "❌ Lucy failed to start"
    echo "📝 Check logs:"
    echo "   tail -20 lucy.log"
    exit 1
fi
