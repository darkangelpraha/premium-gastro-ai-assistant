#!/bin/bash
# Setup daily BlueJet sync at 10 AM
# Run this once to configure automatic daily syncs

set -e

echo "🔧 Setting up daily BlueJet sync"
echo "================================"
echo ""

# Check if crontab exists
if ! crontab -l &>/dev/null; then
    echo "Creating new crontab..."
    touch /tmp/crontab_new
else
    echo "Updating existing crontab..."
    crontab -l > /tmp/crontab_new
fi

# Remove any existing BlueJet sync entries
sed -i.bak '/bluejet.*sync/d' /tmp/crontab_new 2>/dev/null || sed '/bluejet.*sync/d' /tmp/crontab_new > /tmp/crontab_new.tmp && mv /tmp/crontab_new.tmp /tmp/crontab_new

# Add new entry for 10 AM daily
echo "" >> /tmp/crontab_new
echo "# BlueJet → Qdrant sync - Daily at 10 AM" >> /tmp/crontab_new
echo "0 10 * * * cd ~/premium-gastro-ai-assistant && ./RUN_BLUEJET_SYNC.sh >> ~/premium-gastro-ai-assistant/sync.log 2>&1" >> /tmp/crontab_new

# Install new crontab
crontab /tmp/crontab_new

echo "✅ Cron job installed!"
echo ""
echo "Daily sync configured:"
echo "  - Time: 10:00 AM every day"
echo "  - Script: ~/premium-gastro-ai-assistant/RUN_BLUEJET_SYNC.sh"
echo "  - Log: ~/premium-gastro-ai-assistant/sync.log"
echo ""
echo "View crontab: crontab -l"
echo "View logs: tail -f ~/premium-gastro-ai-assistant/sync.log"
echo ""
echo "To remove: crontab -e (then delete the BlueJet line)"
