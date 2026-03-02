#!/bin/bash
# BlueJet MCP Query Helper
# Spolehlivý přístup k BlueJet CRM přes MCP protocol (curl fallback)
# Funguje i v pokračujících Claude Code sessions kde MCP tool není dostupný
#
# Použití: ./bluejet_query.sh <method> <endpoint> [body]
# Příklady:
#   ./bluejet_query.sh GET "api/v1/Data?no=222&limit=5"
#   ./bluejet_query.sh GET "api/v1/Data?no=293&limit=10"
#   ./bluejet_query.sh POST "api/v1/Data?no=222" '{"columns":[{"name":"firma","value":"Test"}]}'

MCP_URL="http://127.0.0.1:8741/mcp/"
METHOD="${1:-GET}"
ENDPOINT="${2}"
BODY="${3}"

if [ -z "$ENDPOINT" ]; then
  echo "Použití: $0 <METHOD> <endpoint> [body]"
  echo "  METHOD: GET, POST, PUT, DELETE"
  echo "  endpoint: např. api/v1/Data?no=222&limit=5"
  echo "  body: JSON string (volitelné, pro POST/PUT)"
  exit 1
fi

# 1. MCP Handshake — initialize + capture session ID
# Response is SSE format (text/event-stream), headers go to temp file
curl -s -X POST "$MCP_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -D /tmp/bluejet_mcp_headers \
  -o /dev/null \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"claude-bash","version":"1.0"}}}'

SESSION_ID=$(grep -i 'mcp-session-id' /tmp/bluejet_mcp_headers 2>/dev/null | awk '{print $2}' | tr -d '\r\n')

if [ -z "$SESSION_ID" ]; then
  echo "CHYBA: Nepodařilo se získat MCP session ID" >&2
  echo "Je BlueJet MCP kontejner spuštěný? Zkus: docker ps --filter name=bluejet" >&2
  exit 2
fi

# 2. Build arguments JSON
ARGS="{\"method\":\"$METHOD\",\"endpoint\":\"$ENDPOINT\""
if [ -n "$BODY" ]; then
  ARGS="$ARGS,\"body\":$BODY"
fi
ARGS="$ARGS}"

# 3. Call bluejet_request — response is SSE, extract data: lines
RAW_RESULT=$(curl -s -X POST "$MCP_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"tools/call\",\"id\":3,\"params\":{\"name\":\"bluejet_request\",\"arguments\":$ARGS}}")

# 4. Parse SSE response — extract JSON from "data: " lines
echo "$RAW_RESULT" | python3 -c "
import sys, json

raw = sys.stdin.read()

# Extract JSON from SSE 'data:' lines
json_str = None
for line in raw.split('\n'):
    line = line.strip()
    if line.startswith('data:'):
        json_str = line[5:].strip()
        break

# Fallback: maybe it's already plain JSON
if json_str is None:
    json_str = raw.strip()

if not json_str:
    print('CHYBA: Prázdná odpověď z MCP', file=sys.stderr)
    sys.exit(3)

try:
    data = json.loads(json_str)
except json.JSONDecodeError as e:
    print(f'JSON parse error: {e}', file=sys.stderr)
    print(f'Raw: {json_str[:500]}', file=sys.stderr)
    sys.exit(4)

if 'error' in data:
    print(f\"MCP Error: {json.dumps(data['error'], ensure_ascii=False)}\", file=sys.stderr)
    sys.exit(3)

if 'result' in data and 'content' in data['result']:
    for item in data['result']['content']:
        if item.get('type') == 'text':
            try:
                parsed = json.loads(item['text'])
                print(json.dumps(parsed, indent=2, ensure_ascii=False))
            except (json.JSONDecodeError, TypeError):
                print(item['text'])
else:
    print(json.dumps(data, indent=2, ensure_ascii=False))
" 2>&1

# Cleanup
rm -f /tmp/bluejet_mcp_headers
