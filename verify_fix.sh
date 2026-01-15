#!/bin/bash
# Verification Script - Run after consolidation to confirm fix

echo "=== CLAUDE CONFIG VERIFICATION ==="
echo "Date: $(date)"
echo ""

PRIMARY="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

# Count total config files
echo "Searching for all Claude config files..."
ALL_CONFIGS=$(mdfind -name "claude*config*.json" 2>/dev/null | grep -v "/node_modules/" | grep -v "/.git/" | grep -v "/backup" || true)
COUNT=$(echo "$ALL_CONFIGS" | grep -v "^$" | wc -l | tr -d ' ')

echo ""
echo "=== RESULTS ==="
echo ""

if [ -z "$ALL_CONFIGS" ] || [ "$COUNT" -eq 0 ]; then
  COUNT=0
fi

echo "Total config files found: $COUNT"
echo ""

if [ $COUNT -gt 0 ]; then
  echo "Config file locations:"
  echo "$ALL_CONFIGS" | nl
  echo ""
fi

echo "Primary config location: $PRIMARY"
if [ -f "$PRIMARY" ]; then
  echo "  Status: EXISTS ✓"
  echo "  Size: $(stat -f%z "$PRIMARY") bytes"
  echo "  Modified: $(stat -f%Sm "$PRIMARY")"
  echo "  Hash: $(md5 -q "$PRIMARY")"
else
  echo "  Status: MISSING ✗"
fi

echo ""
echo "=== ASSESSMENT ==="
echo ""

if [ $COUNT -eq 1 ] && [ -f "$PRIMARY" ]; then
  echo "✅ PERFECT - Configuration is clean"
  echo "   • Only one config file exists"
  echo "   • Located at correct primary location"
  echo "   • All edits will now go to the same file"
  echo "   • Claude Desktop will read from this file"
  echo ""
  echo "Your issue should be RESOLVED."

elif [ $COUNT -eq 0 ]; then
  echo "❌ NO CONFIG FILES FOUND"
  echo "   Create one at: $PRIMARY"

elif [ $COUNT -gt 1 ]; then
  echo "⚠️  MULTIPLE FILES STILL EXIST ($COUNT files)"
  echo "   The consolidation may not have completed successfully"
  echo "   Recommended: Run ./fix_claude_configs.sh again"

elif [ ! -f "$PRIMARY" ]; then
  echo "⚠️  CONFIG EXISTS BUT NOT AT PRIMARY LOCATION"
  echo "   Found at:"
  echo "$ALL_CONFIGS"
  echo "   Recommended: Move to $PRIMARY"
fi

echo ""
echo "=== NEXT ACTIONS ==="
echo ""

if [ $COUNT -eq 1 ] && [ -f "$PRIMARY" ]; then
  echo "1. Restart Claude Desktop (if running)"
  echo "2. Test your MCP servers and configuration"
  echo "3. Any changes you make should now persist"
else
  echo "1. Run the fix script: ./fix_claude_configs.sh"
  echo "2. Verify again with: ./verify_fix.sh"
fi

echo ""

# Check for running Claude processes
CLAUDE_RUNNING=$(ps aux | grep -i "[C]laude" || true)
if [ ! -z "$CLAUDE_RUNNING" ]; then
  echo "⚠️  Claude is currently running. Restart it to apply changes:"
  echo "   killall Claude && open -a Claude"
  echo ""
fi

# Show content preview if primary exists
if [ -f "$PRIMARY" ]; then
  echo "=== CURRENT CONFIG CONTENT ==="
  cat "$PRIMARY"
  echo ""
fi
