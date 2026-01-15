#!/bin/bash
# Fixed Claude Config Consolidation Script
# Fixes all bugs from previous version

set -euo pipefail  # Strict error handling

PRIMARY="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
BACKUP_DIR="$HOME/Desktop/claude_config_backup_$(date +%Y%m%d_%H%M%S)"

echo "=== CLAUDE CONFIG CONSOLIDATION (FIXED) ==="
echo ""

# Step 1: Find all configs
echo "Finding all config files..."
CONFIGS=$(mktemp)
mdfind -name "claude_config.json" 2>/dev/null | grep -v "/node_modules/" | grep -v "/.git/" > "$CONFIGS" || true
mdfind -name "claude_desktop_config.json" 2>/dev/null | grep -v "/node_modules/" | grep -v "/.git/" >> "$CONFIGS" || true

# Remove duplicates
sort -u "$CONFIGS" -o "$CONFIGS"

FILE_COUNT=$(wc -l < "$CONFIGS" | tr -d ' ')

if [ "$FILE_COUNT" -eq 0 ]; then
  echo "No config files found!"
  rm "$CONFIGS"
  exit 1
fi

echo "Found $FILE_COUNT config file(s)"
echo ""

# Step 2: Check for symlinks
echo "Checking for symlinks..."
HAS_SYMLINKS=false
while IFS= read -r file; do
  if [ -L "$file" ]; then
    echo "  SYMLINK: $file -> $(readlink "$file")"
    HAS_SYMLINKS=true
  fi
done < "$CONFIGS"

if [ "$HAS_SYMLINKS" = true ]; then
  echo ""
  echo "⚠️  SYMLINKS DETECTED!"
  echo "Consolidation may break symlink structure."
  read -p "Continue anyway? (yes/no): " CONFIRM
  if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted"
    rm "$CONFIGS"
    exit 0
  fi
fi

echo ""

# Step 3: Check which file Claude is using
echo "Checking which config Claude Desktop is using..."
CLAUDE_PID=$(pgrep -i "Claude Desktop" | head -1 || echo "")

if [ -n "$CLAUDE_PID" ]; then
  ACTIVE_CONFIG=$(lsof -p "$CLAUDE_PID" 2>/dev/null | grep -i "config.json" | awk '{print $9}' || echo "")
  if [ -n "$ACTIVE_CONFIG" ]; then
    echo "  ✓ Claude is using: $ACTIVE_CONFIG"
  else
    echo "  ⚠️  Could not determine active config"
    ACTIVE_CONFIG=""
  fi
else
  echo "  ⚠️  Claude Desktop is not running"
  echo "  (Cannot detect which config is in use)"
  ACTIVE_CONFIG=""
fi

echo ""

# Step 4: Backup EVERYTHING
echo "Creating backup..."
mkdir -p "$BACKUP_DIR"

while IFS= read -r file; do
  if [ -f "$file" ]; then
    SAFE_NAME=$(echo "$file" | sed "s|$HOME|HOME|g" | tr '/' '_')
    cp -p "$file" "$BACKUP_DIR/$SAFE_NAME"
    echo "  ✓ Backed up: $(basename "$file")"
  fi
done < "$CONFIGS"

echo ""
echo "✓ Backup complete: $BACKUP_DIR"
echo ""

# Step 5: Compare file contents
echo "Analyzing file contents..."
TEMP_HASHES=$(mktemp)

while IFS= read -r file; do
  if [ -f "$file" ]; then
    HASH=$(md5 -q "$file")
    SIZE=$(stat -f%z "$file")
    MTIME=$(stat -f%m "$file")
    echo "$HASH|$MTIME|$SIZE|$file" >> "$TEMP_HASHES"
  fi
done < "$CONFIGS"

UNIQUE_HASHES=$(cut -d'|' -f1 "$TEMP_HASHES" | sort -u | wc -l | tr -d ' ')

echo "Files found: $FILE_COUNT"
echo "Unique configs: $UNIQUE_HASHES"
echo ""

if [ "$UNIQUE_HASHES" -eq 1 ]; then
  echo "✓ All files have identical content"
  echo "  Issue is redundancy, not conflicting configs"
else
  echo "⚠️  FILES HAVE DIFFERENT CONTENT!"
  echo "  This confirms your hypothesis"
  echo ""
  echo "Content comparison:"
  while IFS='|' read -r hash mtime size file; do
    echo "  $file"
    echo "    Modified: $(date -r "$mtime" "+%Y-%m-%d %H:%M:%S")"
    echo "    Size: $size bytes"
    echo "    Hash: $hash"
    echo ""
  done < "$TEMP_HASHES"
fi

# Step 6: Select primary config
echo "Selecting primary configuration..."

if [ -n "$ACTIVE_CONFIG" ] && [ -f "$ACTIVE_CONFIG" ]; then
  # Use the file Claude is actively using
  SELECTED="$ACTIVE_CONFIG"
  echo "  Using active config: $SELECTED"
elif [ -f "$PRIMARY" ]; then
  # Use existing primary location
  SELECTED="$PRIMARY"
  echo "  Using existing primary: $SELECTED"
else
  # Use most recently modified
  SELECTED=$(sort -t'|' -k2 -rn "$TEMP_HASHES" | head -1 | cut -d'|' -f4)
  echo "  Using most recent: $SELECTED"
fi

echo ""

# Step 7: Validate selected config
echo "Validating selected config..."
if python3 -m json.tool "$SELECTED" > /dev/null 2>&1; then
  echo "  ✓ Valid JSON"
else
  echo "  ✗ INVALID JSON!"
  echo "  Config is corrupted. Aborting!"
  rm "$CONFIGS" "$TEMP_HASHES"
  exit 1
fi

echo ""

# Step 8: Show preview and confirm
echo "=== PREVIEW OF CHANGES ==="
echo ""
echo "Will keep: $SELECTED"
echo "Will remove:"
while IFS= read -r file; do
  if [ "$file" != "$SELECTED" ]; then
    echo "  - $file"
  fi
done < "$CONFIGS"

echo ""
echo "Primary location will be: $PRIMARY"
if [ "$SELECTED" != "$PRIMARY" ]; then
  echo "(Will copy from $SELECTED)"
fi

echo ""
read -p "Proceed with consolidation? (yes/no): " FINAL_CONFIRM
if [ "$FINAL_CONFIRM" != "yes" ]; then
  echo "Aborted"
  rm "$CONFIGS" "$TEMP_HASHES"
  exit 0
fi

echo ""

# Step 9: Perform consolidation
echo "Consolidating configs..."

# Ensure primary directory exists
mkdir -p "$(dirname "$PRIMARY")"

# Copy selected to primary if needed
if [ "$SELECTED" != "$PRIMARY" ]; then
  cp -p "$SELECTED" "$PRIMARY"
  echo "  ✓ Copied to primary location"
fi

# Remove duplicates (fixed: not in subshell)
REMOVED=0
while IFS= read -r file; do
  if [ "$file" != "$PRIMARY" ] && [ -f "$file" ]; then
    rm "$file"
    echo "  ✓ Removed: $file"
    REMOVED=$((REMOVED + 1))
  fi
done < "$CONFIGS"

echo ""
echo "Removed $REMOVED duplicate(s)"

# Cleanup temp files
rm "$CONFIGS" "$TEMP_HASHES"

echo ""
echo "=== CONSOLIDATION COMPLETE ==="
echo ""
echo "✓ Primary config: $PRIMARY"
echo "✓ Backup location: $BACKUP_DIR"
echo ""
echo "NEXT STEPS:"
echo "1. Restart Claude Desktop: killall Claude && open -a Claude"
echo "2. Verify configuration works"
echo "3. Test for 24 hours"
echo "4. If issues: restore from $BACKUP_DIR"
echo ""
echo "=== VERIFICATION ==="
REMAINING=$(mdfind -name "claude*config*.json" 2>/dev/null | grep -v "/node_modules/" | grep -v "/.git/" | grep -v "$BACKUP_DIR" | wc -l | tr -d ' ')
echo "Config files remaining: $REMAINING"
if [ "$REMAINING" -eq 1 ]; then
  echo "✅ SUCCESS - Only one config file remains"
else
  echo "⚠️  Warning: Found $REMAINING files (expected 1)"
fi
echo ""
