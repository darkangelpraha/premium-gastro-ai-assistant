#!/bin/bash
# Claude Config File Audit Script
# This script finds all Claude config files on your macOS system

echo "=== CLAUDE CONFIG FILE AUDIT ==="
echo "Date: $(date)"
echo ""
echo "Searching for all Claude config files..."
echo ""

FOUND=0

# Array of possible locations
LOCATIONS=(
  "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
  "$HOME/.config/claude/claude_config.json"
  "$HOME/.claude_config.json"
  "$HOME/Library/Preferences/claude_config.json"
  "$HOME/.claude/config.json"
  "$HOME/Documents/claude_config.json"
)

# Check each known location
for loc in "${LOCATIONS[@]}"; do
  if [ -f "$loc" ]; then
    FOUND=$((FOUND + 1))
    echo "[$FOUND] FOUND: $loc"
    echo "    Size: $(stat -f%z "$loc") bytes"
    echo "    Modified: $(stat -f%Sm "$loc")"
    echo "    Hash: $(md5 -q "$loc")"
    echo ""
  fi
done

# Also search entire system using Spotlight
echo "Performing full system search via Spotlight..."
echo "(This matches your manual Spotlight search that found 4 files)"
echo ""

EXTRA=$(mdfind -name claude_config.json 2>/dev/null | grep -v "/node_modules/" | grep -v "/.git/")
if [ ! -z "$EXTRA" ]; then
  while IFS= read -r file; do
    if [ -f "$file" ]; then
      FOUND=$((FOUND + 1))
      echo "[$FOUND] FOUND via Spotlight: $file"
      echo "    Size: $(stat -f%z "$file") bytes"
      echo "    Modified: $(stat -f%Sm "$file")"
      echo "    Hash: $(md5 -q "$file")"
      echo ""
    fi
  done <<< "$EXTRA"
fi

# Also check for claude_desktop_config.json
DESKTOP=$(mdfind -name claude_desktop_config.json 2>/dev/null | grep -v "/node_modules/" | grep -v "/.git/")
if [ ! -z "$DESKTOP" ]; then
  while IFS= read -r file; do
    if [ -f "$file" ]; then
      FOUND=$((FOUND + 1))
      echo "[$FOUND] FOUND Desktop Config: $file"
      echo "    Size: $(stat -f%z "$file") bytes"
      echo "    Modified: $(stat -f%Sm "$file")"
      echo "    Hash: $(md5 -q "$file")"
      echo ""
    fi
  done <<< "$DESKTOP"
fi

echo ""
echo "=== TOTAL FILES FOUND: $FOUND ==="
echo ""

# Check which process is using which file
echo "=== ACTIVE CLAUDE PROCESSES ==="
ps aux | grep -i "[C]laude" || echo "No Claude processes running"
echo ""

# Compare file contents
if [ $FOUND -gt 1 ]; then
  echo "=== FILE CONTENT COMPARISON ==="
  echo "Checking if all files are identical..."
  echo ""

  # Get all unique hashes
  HASHES=$(for loc in "${LOCATIONS[@]}"; do
    [ -f "$loc" ] && md5 -q "$loc"
  done | sort -u)

  HASH_COUNT=$(echo "$HASHES" | grep -v "^$" | wc -l)

  if [ $HASH_COUNT -gt 1 ]; then
    echo "⚠️  FILES HAVE DIFFERENT CONTENT!"
    echo "This confirms your hypothesis - different files contain different configs"
    echo "Number of unique configurations: $HASH_COUNT"
  else
    echo "ℹ️  All files have identical content (same hash)"
    echo "Issue is redundancy, not conflicting configs"
  fi
  echo ""
fi

echo "=== RECOMMENDATION ==="
if [ $FOUND -eq 0 ]; then
  echo "❌ No config files found. Create one at:"
  echo "   ~/Library/Application Support/Claude/claude_desktop_config.json"
elif [ $FOUND -eq 1 ]; then
  echo "✅ Only one config file found - this is correct."
  echo "   Your issue may be elsewhere."
else
  echo "⚠️  MULTIPLE CONFIG FILES DETECTED ($FOUND files)"
  echo ""
  echo "This confirms your hypothesis:"
  echo "  • Multiple config files exist in different locations"
  echo "  • When you edit one, Claude may be reading another"
  echo "  • This explains why fixes don't persist"
  echo ""
  echo "Next step: Run ./fix_claude_configs.sh to consolidate"
fi

echo ""
echo "=== DETAILED LOCATIONS ==="
echo "Expected primary location (Claude Desktop):"
echo "  ~/Library/Application Support/Claude/claude_desktop_config.json"
echo ""
echo "To fix this issue, run:"
echo "  ./fix_claude_configs.sh"
