#!/bin/bash
# Rollback Script - Restore Claude Configs from Backup

if [ $# -eq 0 ]; then
  echo "Usage: $0 <backup_directory>"
  echo ""
  echo "Example:"
  echo "  $0 ~/Desktop/claude_config_backup_20260115_123456"
  echo ""
  echo "Available backups:"
  ls -1 ~/Desktop/claude_config_backup_* 2>/dev/null || echo "  No backups found"
  exit 1
fi

BACKUP_DIR="$1"

if [ ! -d "$BACKUP_DIR" ]; then
  echo "Error: Backup directory not found: $BACKUP_DIR"
  exit 1
fi

echo "=== CLAUDE CONFIG ROLLBACK ==="
echo ""
echo "Backup directory: $BACKUP_DIR"
echo ""

# Count files in backup
FILE_COUNT=$(ls -1 "$BACKUP_DIR"/HOME_* 2>/dev/null | wc -l | tr -d ' ')

if [ "$FILE_COUNT" -eq 0 ]; then
  echo "Error: No backup files found in $BACKUP_DIR"
  exit 1
fi

echo "Found $FILE_COUNT backed up config(s)"
echo ""
echo "Files to restore:"
ls -1 "$BACKUP_DIR"/HOME_* | while read -r backup; do
  ORIGINAL=$(basename "$backup" | sed 's|HOME_|/Users/|g' | tr '_' '/' | sed "s|/Users|$HOME|")
  echo "  $ORIGINAL"
done

echo ""
read -p "Restore these files? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  echo "Aborted"
  exit 0
fi

echo ""
echo "Stopping Claude Desktop..."
killall Claude 2>/dev/null || echo "  (Claude not running)"

echo ""
echo "Restoring files..."

ls -1 "$BACKUP_DIR"/HOME_* | while read -r backup; do
  ORIGINAL=$(basename "$backup" | sed 's|HOME_|/Users/|g' | tr '_' '/' | sed "s|/Users|$HOME|")
  mkdir -p "$(dirname "$ORIGINAL")"
  cp -p "$backup" "$ORIGINAL"
  echo "  ✓ Restored: $ORIGINAL"
done

echo ""
echo "=== ROLLBACK COMPLETE ==="
echo ""
echo "Restarting Claude Desktop..."
sleep 2
open -a Claude

echo ""
echo "✓ Rollback complete"
echo "✓ Claude Desktop restarted"
echo ""
echo "Test your configuration to verify it's working"
echo ""
