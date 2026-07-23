#!/bin/bash
set -e

MEDIA_DIR="/var/www/eduorbit/media"
BACKUP_DIR="/tmp/media_backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/media_$DATE.tar.gz"
S3_BUCKET="s3://eduorbit-backups/media/"

mkdir -p "$BACKUP_DIR"

echo "Backing up media directory..."
tar -czvf "$BACKUP_FILE" -C "$MEDIA_DIR" .

echo "Uploading to S3..."
s3cmd put "$BACKUP_FILE" "$S3_BUCKET"

if [ $? -eq 0 ]; then
    echo "Media backup and upload successful."
else
    echo "Upload failed."
    exit 1
fi
