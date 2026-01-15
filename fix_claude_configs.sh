#!/bin/bash
# Claude Config Consolidation Script
# This script consolidates multiple config files into ONE primary location

set -e  # Exit on error

PRIMARY="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
BACKUP_DIR="$HOME/claude_config_backup_$(date +%Y%m%d_%H%M%S)"

echo "=== CLAUDE CONFIG CONSOLIDATION ==="
echo ""
echo "This script will:"
echo "  1. Find all Claude config files"
echo "  2. Backup all files"
echo "  3. Consolidate to ONE primary location"
echo "  4. Remove duplicates"
echo ""

# Safety check
read -p "Continue? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  echo "Aborted by user"
  exit 0
fi

echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"
echo "✓ Created backup directory: $BACKUP_DIR"
echo ""

# Find all config files
echo "Finding all config files..."
CONFIGS=""

# Known locations
KNOWN_LOCATIONS=(
  "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
  "$HOME/.config/claude/claude_config.json"
  "$HOME/.claude_config.json"
  "$HOME/Library/Preferences/claude_config.json"
  "$HOME/.claude/config.json"
  "$HOME/Documents/claude_config.json"
)

for loc in "${KNOWN_LOCATIONS[@]}"; do
  if [ -f "$loc" ]; then
    CONFIGS="$CONFIGS"$'\n'"$loc"
  fi
done

# Spotlight search
SPOTLIGHT=$(mdfind -name claude_config.json 2>/dev/null | grep -v "/node_modules/" | grep -v "/.git/" || true)
if [ ! -z "$SPOTLIGHT" ]; then
  CONFIGS="$CONFIGS"$'\n'"$SPOTLIGHT"
fi

SPOTLIGHT_DESKTOP=$(mdfind -name claude_desktop_config.json 2>/dev/null | grep -v "/node_modules/" | grep -v "/.git/" || true)
if [ ! -z "$SPOTLIGHT_DESKTOP" ]; then
  CONFIGS="$CONFIGS"$'\n'"$SPOTLIGHT_DESKTOP"
fi

# Remove duplicates and empty lines
CONFIGS=$(echo "$CONFIGS" | sort -u | grep -v "^$")

if [ -z "$CONFIGS" ]; then
  echo "❌ No config files found!"
  echo "Creating new config at primary location..."
  mkdir -p "$(dirname "$PRIMARY")"
  echo '{"mcpServers":{}}' > "$PRIMARY"
  echo "✓ Created: $PRIMARY"
  exit 0
fi

echo "Found config files:"
echo "$CONFIGS" | nl
echo ""

# Backup all configs
echo "Backing up all config files..."
echo "$CONFIGS" | while read -r config; do
  if [ -f "$config" ]; then
    FILENAME=$(basename "$config")
    DIRNAME=$(dirname "$config" | sed "s|$HOME|HOME|g" | tr '/' '_')
    BACKUP_NAME="${DIRNAME}_${FILENAME}"
    cp "$config" "$BACKUP_DIR/$BACKUP_NAME"
    echo "  ✓ Backed up: $config → $BACKUP_NAME"
  fi
done

echo ""
echo "Analyzing config files..."
echo ""

# Find the most recently modified config
LATEST=""
LATEST_TIME=0

echo "$CONFIGS" | while read -r config; do
  if [ -f "$config" ]; then
    MOD_TIME=$(stat -f%m "$config" 2>/dev/null || echo 0)
    HASH=$(md5 -q "$config")
    SIZE=$(stat -f%z "$config")
    echo "  $config"
    echo "    Modified: $(stat -f%Sm "$config")"
    echo "    Size: $SIZE bytes"
    echo "    Hash: $HASH"
    echo ""
  fi
done

# Determine which config to use as primary
echo "Selecting primary config..."

# Check if primary location already exists and has content
if [ -f "$PRIMARY" ] && [ $(stat -f%z "$PRIMARY") -gt 10 ]; then
  echo "  Using existing primary config (already at correct location)"
  SELECTED="$PRIMARY"
else
  # Find most recently modified
  SELECTED=$(echo "$CONFIGS" | while read -r config; do
    if [ -f "$config" ]; then
      echo "$(stat -f%m "$config") $config"
    fi
  done | sort -rn | head -1 | cut -d' ' -f2-)

  echo "  Selected most recently modified: $SELECTED"
fi

echo ""
echo "Creating primary config at: $PRIMARY"

# Ensure directory exists
mkdir -p "$(dirname "$PRIMARY")"

# Copy selected config to primary location
if [ "$SELECTED" != "$PRIMARY" ]; then
  cp "$SELECTED" "$PRIMARY"
  echo "  ✓ Copied from: $SELECTED"
else
  echo "  ✓ Already at primary location"
fi

echo ""
echo "Removing duplicate config files..."
REMOVED=0
echo "$CONFIGS" | while read -r config; do
  if [ -f "$config" ] && [ "$config" != "$PRIMARY" ]; then
    echo "  Removing: $config"
    rm "$config"
    REMOVED=$((REMOVED + 1))
  fi
done

if [ $REMOVED -eq 0 ]; then
  echo "  No duplicates to remove"
fi

echo ""
echo "=== CONSOLIDATION COMPLETE ==="
echo ""
echo "Primary config location: $PRIMARY"
echo "File exists: $([ -f "$PRIMARY" ] && echo "YES ✓" || echo "NO ✗")"
echo "File size: $(stat -f%z "$PRIMARY") bytes"
echo ""
echo "Content preview:"
head -20 "$PRIMARY"
echo ""

echo "=== VERIFICATION ==="
REMAINING=$(mdfind -name "claude*config*.json" 2>/dev/null | grep -v "/node_modules/" | grep -v "/.git/" | grep -v "$BACKUP_DIR" | wc -l)
echo "Config files remaining on system: $REMAINING"

if [ $REMAINING -eq 1 ]; then
  echo "✅ SUCCESS - Only one config file remains"
else
  echo "⚠️  Warning: Found $REMAINING config files (expected 1)"
fi

echo ""
echo "=== NEXT STEPS ==="
echo ""
echo "1. Quit Claude Desktop completely:"
echo "   • Press Cmd+Q in Claude Desktop"
echo "   • Run: killall Claude"
echo ""
echo "2. Verify no Claude processes:"
echo "   ps aux | grep Claude"
echo ""
echo "3. Restart Claude Desktop:"
echo "   open -a Claude"
echo ""
echo "4. Test your configuration:"
echo "   • Check MCP servers are loading"
echo "   • Verify settings persist"
echo ""
echo "5. If issues occur, restore from backup:"
echo "   $BACKUP_DIR"
echo ""
echo "=== PROOF OF FIX ==="
echo "Run this to verify only one config exists:"
echo "  mdfind -name 'claude*config*.json' | grep -v node_modules"
echo ""
