#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <tenant_name>"
    exit 1
fi

TENANT_NAME="$1"
DB_NAME="eduorbit_${TENANT_NAME}"
DB_USER="${TENANT_NAME}_user"
DB_PASS=$(openssl rand -base64 12)

echo "Creating database $DB_NAME..."
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';"
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

echo "Database created successfully."
echo "User: $DB_USER"
echo "Password: $DB_PASS"
