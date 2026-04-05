#!/bin/zsh

SOURCE="/Users/olivier/Obsidian/Main"
DEST="/Users/olivier/Library/CloudStorage/Dropbox/Data/Obsidian Archives"
DATE=$(date +"%Y-%m-%d_%H-%M")
ARCHIVE_NAME="Obsidian_${DATE}.zip"

zip -r "${DEST}/${ARCHIVE_NAME}" "${SOURCE}" -x "*.DS_Store" -x "__MACOSX"

# Keep only the last 72 archives (3 days at hourly intervals)
ls -t "${DEST}"/Obsidian_*.zip 2>/dev/null | tail -n +73 | xargs rm -f
