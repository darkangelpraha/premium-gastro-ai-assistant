# Bluejet API Integration Setup

## Current Status

✅ Bluejet API client created
✅ 1Password CLI installed in container
✅ Scripts ready to connect
❌ **BLOCKED**: Container needs 1Password authentication

## The Problem

The container environment needs access to 1Password credentials but cannot use desktop app integration. We need **automated, secure** access to 1Password items.

## Solution: 1Password Service Account

### Step 1: Create Service Account (One-time setup on your Mac)

```bash
# Sign in to 1Password on your Mac
op account add

# Create a service account token with access to the AI vault
# Go to: https://my.1password.com/settings/developer
# Click "Create Service Account"
# Grant access to "AI" vault
# Copy the OP_SERVICE_ACCOUNT_TOKEN
```

### Step 2: Add Token to Environment

Once you have the service account token:

```bash
# Option A: Add to your shell profile (Mac)
echo 'export OP_SERVICE_ACCOUNT_TOKEN="ops_xxxxx..."' >> ~/.zshrc
source ~/.zshrc

# Option B: Set for this session only
export OP_SERVICE_ACCOUNT_TOKEN="ops_xxxxx..."
```

### Step 3: Pass to Container

When starting the container, ensure the token is passed:

```bash
docker run -e OP_SERVICE_ACCOUNT_TOKEN="$OP_SERVICE_ACCOUNT_TOKEN" ...
```

## Alternative: 1Password Connect (Enterprise)

If you have 1Password Business/Enterprise:

### Step 1: Deploy 1Password Connect

```bash
# Create Connect server credentials file
# Download from: https://my.1password.com/integrations/connect

# Run Connect server
docker run -d \
  -p 8080:8080 \
  -v /path/to/1password-credentials.json:/home/opuser/.op/1password-credentials.json \
  -v /path/to/data:/home/opuser/.op/data \
  1password/connect-api:latest
```

### Step 2: Configure Environment

```bash
export OP_CONNECT_HOST="http://localhost:8080"
export OP_CONNECT_TOKEN="your_connect_token_here"
```

## Testing the Connection

Once configured, test with:

```bash
# From container
python3 /home/user/premium-gastro-ai-assistant/bluejet_connect.py
```

Expected output:
```
🔐 Fetching credentials from 1Password...
✅ Credentials retrieved from 1Password
   Token ID: xxxxx...
   Token Hash: xxxxx...
📤 Authenticating with https://czeco.bluejet.cz/api/v1/users/authenticate...
✅ Authentication SUCCESSFUL!
🎫 Session token received: xxxxx...
```

## Security Notes

✅ **Service account tokens** are secure for automation
✅ **Tokens grant limited, auditable access**
✅ **No credentials stored in files or code**
✅ **All access logged in 1Password**

## Current Files

- `bluejet_connect.py` - Main connector (uses op CLI)
- `bluejet_api_client.py` - Alternative implementation
- `test_bluejet_connection.py` - Manual test with env vars

## Next Steps

1. Create 1Password service account token
2. Add OP_SERVICE_ACCOUNT_TOKEN to environment
3. Run `python3 bluejet_connect.py`
4. Explore Bluejet API endpoints
5. Update skills/bluejet-expert/SKILL.md with findings
