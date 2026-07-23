#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file_path_or_s3_uri>"
    exit 1
fi

BACKUP_FILE="$1"
MEDIA_DIR="/var/www/eduorbit/media"

if [[ "$BACKUP_FILE" == s3://* ]]; then
    LOCAL_FILE="/tmp/$(basename $BACKUP_FILE)"
    echo "Downloading from S3..."
    s3cmd get "$BACKUP_FILE" "$LOCAL_FILE"
    BACKUP_FILE="$LOCAL_FILE"
fi

echo "Restoring media to $MEDIA_DIR..."
mkdir -p "$MEDIA_DIR"
tar -xzvf "$BACKUP_FILE" -C "$MEDIA_DIR"

echo "Media restored successfully."
