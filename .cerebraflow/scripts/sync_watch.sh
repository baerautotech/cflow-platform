#!/bin/zsh
set -euo pipefail
LABEL="com.cerebraflow.sync"
if ! launchctl list | grep -q "$LABEL"; then
  /usr/bin/osascript -e 'display notification "Sync agent not found" with title "CerebraFlow" subtitle "Attempting start"'
  launchctl load -w ~/Library/LaunchAgents/com.cerebraflow.sync.plist || true
fi
if ! launchctl list | grep "$LABEL" | awk '{print $1}' | grep -qE '^[0-9]+$'; then
  /usr/bin/osascript -e 'display notification "Sync agent restarting" with title "CerebraFlow"'
  launchctl kickstart -k gui/$UID/$LABEL || launchctl load -w ~/Library/LaunchAgents/com.cerebraflow.sync.plist || true
fi
