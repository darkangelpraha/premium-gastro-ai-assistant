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

# Create .env file with proper escaping for special characters
{
    echo "# Auto-generated from 1Password - $(date)"
    echo "# DO NOT commit this file to git!"
    echo ""
    echo "# BlueJet CRM API Authentication"
    echo "BLUEJET_USERNAME=$(op read "op://$VAULT_ID/BlueJet API FULL/username" 2>/dev/null || echo "svejkovsky")"
    echo "BLUEJET_API_TOKEN_ID=$(op read "op://$VAULT_ID/BlueJet API FULL/BLUEJET_API_TOKEN_ID" 2>/dev/null || echo "MISSING")"
    echo "BLUEJET_API_TOKEN_HASH=$(op read "op://$VAULT_ID/BlueJet API FULL/BLUEJET_API_TOKEN_HASH" 2>/dev/null || echo "MISSING")"
    echo ""
    echo "# BlueJet API Endpoints (from 1Password)"
    echo "BLUEJET_BASE_URL=$(op read "op://$VAULT_ID/BlueJet API FULL/w4wjna5zoxuysfdsfdxsyrasmu" 2>/dev/null || echo "https://czeco.bluejet.cz")"
    echo "BLUEJET_REST_AUTH_URL=$(op read "op://$VAULT_ID/BlueJet API FULL/BLUEJET_REST_AUTH_URL" 2>/dev/null || echo "https://czeco.bluejet.cz/api/v1/users/authenticate")"
    echo "BLUEJET_REST_DATA_URL=$(op read "op://$VAULT_ID/BlueJet API FULL/BLUEJET_REST_DATA_URL" 2>/dev/null || echo "https://czeco.bluejet.cz/api/v1/data")"
    echo ""
    echo "# API Environment"
    echo "BLUEJET_API_ENVIRONMENT=$(op read "op://$VAULT_ID/BlueJet API FULL/BLUEJET_API_ENVIRONMENT" 2>/dev/null || echo "production")"
    echo ""
    echo "# Qdrant Vector Database"
    echo "QDRANT_HOST=192.168.1.129"
    echo "QDRANT_PORT=6333"
    echo ""
    echo "# OpenAI for embeddings (optional)"
    echo "OPENAI_API_KEY=$(op read "op://AI Vault/OpenAI API/credential" 2>/dev/null || echo "")"
} > .env.bluejet

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
echo "🚀 Ready to sync! Run:"
echo "python3 bluejet_qdrant_sync.py"
echo ""
