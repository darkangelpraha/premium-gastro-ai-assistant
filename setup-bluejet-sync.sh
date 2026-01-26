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
# Using vault ID instead of name (pipe character | breaks op read)
VAULT_ID="5zbrmieoqrroxon4eu6mwfu4li"

cat > .env.bluejet << EOF
# Auto-generated from 1Password - $(date)
# DO NOT commit this file to git!

# BlueJet CRM API Authentication
BLUEJET_USERNAME=$(op read "op://$VAULT_ID/BlueJet API FULL/username" 2>/dev/null || echo "svejkovsky")
BLUEJET_API_TOKEN_ID=$(op read "op://$VAULT_ID/BlueJet API FULL/BLUEJET_API_TOKEN_ID" 2>/dev/null || echo "MISSING")
BLUEJET_API_TOKEN_HASH=$(op read "op://$VAULT_ID/BlueJet API FULL/BLUEJET_API_TOKEN_HASH" 2>/dev/null || echo "MISSING")

# BlueJet API Endpoints (from 1Password)
BLUEJET_BASE_URL=$(op read "op://$VAULT_ID/BlueJet API FULL/w4wjna5zoxuysfdsfdxsyrasmu" 2>/dev/null || echo "https://czeco.bluejet.cz")
BLUEJET_REST_AUTH_URL=$(op read "op://$VAULT_ID/BlueJet API FULL/BLUEJET_REST_AUTH_URL" 2>/dev/null || echo "https://czeco.bluejet.cz/api/v1/users/authenticate")
BLUEJET_REST_DATA_URL=$(op read "op://$VAULT_ID/BlueJet API FULL/BLUEJET_REST_DATA_URL" 2>/dev/null || echo "https://czeco.bluejet.cz/api/v1/data")

# API Environment
BLUEJET_API_ENVIRONMENT=$(op read "op://$VAULT_ID/BlueJet API FULL/BLUEJET_API_ENVIRONMENT" 2>/dev/null || echo "production")

# Qdrant Vector Database
QDRANT_HOST=192.168.1.129
QDRANT_PORT=6333

# OpenAI for embeddings (optional)
OPENAI_API_KEY=$(op read "op://AI Vault/OpenAI API/credential" 2>/dev/null || echo "")
EOF

echo "✅ Created .env.bluejet"
echo ""

# Verify credentials
if grep -q "MISSING" .env.bluejet; then
    echo "⚠️  WARNING: Some credentials are missing from 1Password"
    echo ""
    echo "Expected fields in 1Password 'Missive | BJ' vault → 'BlueJet API FULL':"
    echo "  - username (svejkovsky)"
    echo "  - BLUEJET_API_TOKEN_ID"
    echo "  - BLUEJET_API_TOKEN_HASH"
    echo ""
    echo "Please check your 1Password credential structure."
    echo "You can manually edit .env.bluejet file if needed."
    exit 1
fi

echo "✅ All credentials retrieved successfully"
echo ""
echo "Next steps:"
echo "1. Test sync: python3 bluejet_qdrant_sync.py"
echo "2. Schedule: Add to crontab for automatic sync"
echo ""
