#!/bin/bash
# Setup BlueJet → Qdrant Sync Service
# Retrieves credentials from 1Password and configures environment

set -e

echo "🔐 BlueJet Sync Setup - Retrieving credentials from 1Password..."
echo ""

# Check if op CLI is available
if ! command -v op &> /dev/null; then
    echo "❌ 1Password CLI (op) not found"
    echo "Install: brew install 1password-cli"
    exit 1
fi

# Create .env file from 1Password
cat > .env.bluejet << EOF
# Auto-generated from 1Password - $(date)
# DO NOT commit this file to git!

# BlueJet CRM API
BLUEJET_URL=$(op read "op://AI/BlueJet API/url" 2>/dev/null || echo "https://your-instance.bluejet.cz")
BLUEJET_TOKEN_ID=$(op read "op://AI/BlueJet API/tokenID" 2>/dev/null || echo "MISSING")
BLUEJET_TOKEN_HASH=$(op read "op://AI/BlueJet API/tokenHash" 2>/dev/null || echo "MISSING")

# Qdrant Vector Database
QDRANT_HOST=192.168.1.129
QDRANT_PORT=6333

# OpenAI for embeddings (optional)
OPENAI_API_KEY=$(op read "op://AI/OpenAI API/credential" 2>/dev/null || echo "")
EOF

echo "✅ Created .env.bluejet"
echo ""

# Verify credentials
if grep -q "MISSING" .env.bluejet; then
    echo "⚠️  WARNING: Some credentials are missing from 1Password"
    echo ""
    echo "Expected paths in 1Password AI vault:"
    echo "  - op://AI/BlueJet API/url"
    echo "  - op://AI/BlueJet API/tokenID"
    echo "  - op://AI/BlueJet API/tokenHash"
    echo ""
    echo "Please check your 1Password vault and update the paths above if needed."
    echo ""
    echo "You can also manually edit .env.bluejet file."
    exit 1
fi

echo "✅ All credentials retrieved successfully"
echo ""
echo "Next steps:"
echo "1. Test sync: python3 bluejet_qdrant_sync.py"
echo "2. Schedule: Add to crontab for automatic sync"
echo ""
