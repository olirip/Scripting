#!/bin/bash

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M")
SOURCE="/Users/olivier/Documents/Matchbox/21-V8/Shared"
DEST="/Users/olivier/Documents/Matchbox/21-V8/Version/$TIMESTAMP"

/usr/local/bin/rclone copy "$SOURCE" "$DEST" \
  --log-file="/Users/olivier/Library/Logs/rclone-matchbox-backup.log" \
  --log-level=INFO

echo "[$TIMESTAMP] Backup terminé vers $DEST" >> "/Users/olivier/Library/Logs/rclone-matchbox-backup.log"
