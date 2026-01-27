#!/bin/bash

VAULT_ID="5zbrmieoqrroxon4eu6mwfu4li"

echo "Reading credentials from 1Password..."
echo ""

# Read all relevant fields
TOKEN_ID=$(op read "op://$VAULT_ID/BlueJet API FULL/BLUEJET_API_TOKEN_ID" 2>/dev/null)
TOKEN_HASH=$(op read "op://$VAULT_ID/BlueJet API FULL/BLUEJET_API_TOKEN_HASH" 2>/dev/null)
TOKENID_FIELD=$(op read "op://$VAULT_ID/BlueJet API FULL/tokenID" 2>/dev/null)

echo "BLUEJET_API_TOKEN_ID: ${TOKEN_ID:0:10}...${TOKEN_ID: -4}"
echo "BLUEJET_API_TOKEN_HASH: ${TOKEN_HASH:0:4}...${TOKEN_HASH: -4}"
echo "tokenID field: ${TOKENID_FIELD:0:10}...${TOKENID_FIELD: -4}"
echo ""
echo "Lengths:"
echo "  TOKEN_ID: ${#TOKEN_ID}"
echo "  TOKEN_HASH: ${#TOKEN_HASH}"
echo "  tokenID field: ${#TOKENID_FIELD}"
echo ""

# Try authentication with XML
AUTH_URL="https://czeco.bluejet.cz/api/v1/users/authenticate"

echo "Trying authentication with <User> (capital U)..."
curl -v -X POST "$AUTH_URL" \
  -H "Content-Type: application/xml; charset=utf-8" \
  -d "<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<User>
    <tokenID>$TOKEN_ID</tokenID>
    <tokenHash>$TOKEN_HASH</tokenHash>
</User>" 2>&1 | grep -A 5 -B 5 "401\|200\|token\|Error"

echo ""
echo "---"
echo ""

# Try with lowercase <user>
echo "Trying with <user> (lowercase u)..."
curl -v -X POST "$AUTH_URL" \
  -H "Content-Type: application/xml; charset=utf-8" \
  -d "<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<user>
    <tokenID>$TOKEN_ID</tokenID>
    <tokenHash>$TOKEN_HASH</tokenHash>
</user>" 2>&1 | grep -A 5 -B 5 "401\|200\|token\|Error"

