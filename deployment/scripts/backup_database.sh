#!/bin/bash
set -e

DB_NAME="eduorbit"
BACKUP_DIR="/tmp/db_backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_$DATE.sql.gz"
S3_BUCKET="s3://eduorbit-backups/db/"

mkdir -p "$BACKUP_DIR"

echo "Backing up database $DB_NAME..."
pg_dump -U postgres $DB_NAME | gzip > "$BACKUP_FILE"

echo "Uploading to S3..."
s3cmd put "$BACKUP_FILE" "$S3_BUCKET"

if [ $? -eq 0 ]; then
    echo "Backup and upload successful."
else
    echo "Upload failed."
    exit 1
fi
