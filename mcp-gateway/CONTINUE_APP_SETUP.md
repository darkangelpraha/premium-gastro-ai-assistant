# Continue App - MCP Gateway API Key Setup

## Overview

Continue app connects to the MCP Gateway at `http://localhost:3000` and requires authentication via the `x-api-key` header. The API key is stored securely in 1Password (AI vault) and retrieved using the 1Password CLI.

## Current Configuration

### MCP Gateway API Key Source

- **1Password Vault:** AI
- **Item:** platform.openai.com
- **Item ID:** 7odqtowknvbntkc3axvn5wpwui
- **Field:** credential (contains OpenAI API key)
- **Reference:** `op://AI/7odqtowknvbntkc3axvn5wpwui/credential`

### Environment File

Location: `/Users/premiumgastro/Missicw/mcp-gateway/.env.mcp-gateway.op`

```bash
MCP_GATEWAY_API_KEY=op://AI/7odqtowknvbntkc3axvn5wpwui/credential
```

## How It Works

1. **LaunchAgent** (`com.premiumgastro.mcp-gateway.plist`) uses `op run --env-file` to:

   - Read `.env.mcp-gateway.op`
   - Resolve 1Password references
   - Inject `MCP_GATEWAY_API_KEY` environment variable
   - Start the MCP Gateway server

2. **MCP Gateway** (`server.js`) reads `MCP_GATEWAY_API_KEY` from environment

3. **Continue App** must send requests with header: `x-api-key: <API_KEY_VALUE>`

## Using the API Key in Continue App

### Option 1: Environment Variable (Recommended)

Set the environment variable before starting Continue:

```bash
# Get API key from 1Password
export MCP_GATEWAY_API_KEY=$(op read 'op://AI/7odqtowknvbntkc3axvn5wpwui/credential')

# Or use op run for the entire session
op run --env-file /Users/premiumgastro/Missicw/mcp-gateway/.env.mcp-gateway.op -- <your-command>
```

### Option 2: Continue Config (if supported)

If Continue supports environment variable references in config, you can use:

```json
{
  "contextProviders": [
    {
      "name": "mcp-gateway",
      "params": {
        "serverUrl": "http://localhost:3000",
        "headers": {
          "x-api-key": "${MCP_GATEWAY_API_KEY}"
        }
      }
    }
  ]
}
```

### Option 3: Direct 1Password CLI Command

For one-off requests or scripts:

```bash
# Get the API key
API_KEY=$(op read 'op://AI/7odqtowknvbntkc3axvn5wpwui/credential')

# Use in curl request
curl -H "x-api-key: $API_KEY" http://localhost:3000/api/servers
```

## Verification Steps

### 1. Verify 1Password Access

```bash
op item get 7odqtowknvbntkc3axvn5wpwui --vault AI --fields "label=credential" --format json
```

### 2. Verify Environment Variable

```bash
cd /Users/premiumgastro/Missicw/mcp-gateway
op run --env-file .env.mcp-gateway.op -- sh -c 'echo "API Key: ${MCP_GATEWAY_API_KEY:0:20}..."'
```

### 3. Verify MCP Gateway is Running

```bash
curl http://localhost:3000/health
```

Expected response:

```json
{ "status": "ok", "servers": 38, "activeConnections": 0, "timestamp": "..." }
```

### 4. Test Authentication Without Key (Should Fail)

```bash
curl http://localhost:3000/api/servers
```

Expected response:

```json
{ "error": "Unauthorized - Invalid API key" }
```

### 5. Test Authentication With Key (Should Succeed)

```bash
cd /Users/premiumgastro/Missicw/mcp-gateway
API_KEY=$(op run --env-file .env.mcp-gateway.op -- sh -c 'echo $MCP_GATEWAY_API_KEY')
curl -H "x-api-key: $API_KEY" http://localhost:3000/api/servers
```

Expected response: JSON array of servers

### 6. Verify LaunchAgent Status

```bash
launchctl list | grep mcp-gateway
```

Should show the service is running (exit code 0).

## Troubleshooting

### Issue: "invalid x-api-key" error

**Possible causes:**

1. API key not set in environment
2. Wrong API key value
3. MCP Gateway not running
4. 1Password CLI not authenticated

**Solutions:**

1. Verify 1Password is signed in: `op account list`
2. Test API key retrieval: `op read 'op://AI/7odqtowknvbntkc3axvn5wpwui/credential'`
3. Check MCP Gateway logs: `tail -f /Users/premiumgastro/Missicw/logs/mcp-gateway.log`
4. Restart LaunchAgent: `launchctl unload ~/Library/LaunchAgents/com.premiumgastro.mcp-gateway.plist && launchctl load ~/Library/LaunchAgents/com.premiumgastro.mcp-gateway.plist`

### Issue: MCP Gateway not starting

**Check:**

1. Port 3000 available: `lsof -i:3000`
2. LaunchAgent status: `launchctl list | grep mcp-gateway`
3. Error logs: `tail -20 /Users/premiumgastro/Missicw/logs/mcp-gateway-error.log`

## Security Notes

- ✅ API key stored in 1Password (AI vault)
- ✅ No hardcoded credentials in code
- ✅ Environment file uses 1Password references
- ✅ LaunchAgent uses `op run` for secure injection
- ✅ MCP Gateway binds to localhost only (127.0.0.1)
- ✅ CORS restricted to localhost origins

## Alternative: Using Different OpenAI API Key

If you want to use a different OpenAI API key from 1Password:

1. Find the item ID: `op item list --vault AI | grep -i openai`
2. Check available fields: `op item get <ITEM_ID> --vault AI --format json`
3. Update `.env.mcp-gateway.op`:
   ```bash
   MCP_GATEWAY_API_KEY=op://AI/<ITEM_ID>/<FIELD_NAME>
   ```
4. Reload LaunchAgent:
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.premiumgastro.mcp-gateway.plist
   launchctl load ~/Library/LaunchAgents/com.premiumgastro.mcp-gateway.plist
   ```
