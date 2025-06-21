#!/usr/bin/env bash
#
# setup_cron.sh — Install ASTA scan cron job

# Folder and script paths
SCRIPT_DIR="$HOME/asta-scripts"
SCRIPT="$SCRIPT_DIR/scan.py"
LOGFILE="$SCRIPT_DIR/scan.log"

# Cron: minute 0, hours 9–16 (i.e. 9 AM, 10 AM, …, 4 PM), Mon–Fri
CRON_SCHEDULE="0 9-16 * * 1-5"

# Full cron line: change into folder, run the script, append output to log
CRON_JOB="$CRON_SCHEDULE cd $SCRIPT_DIR && /usr/bin/env python3 $SCRIPT >> $LOGFILE 2>&1"

# Only add it if it's not already in your crontab
( crontab -l 2>/dev/null | grep -F "$SCRIPT" ) \
  || ( (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab - )

echo "✅ Cron job installed:"
echo "   $CRON_JOB"

