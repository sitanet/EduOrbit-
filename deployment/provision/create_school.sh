#!/bin/bash
set -e

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 <tenant_name> <domain>"
    exit 1
fi

TENANT_NAME="$1"
DOMAIN="$2"

echo "Provisioning new school: $TENANT_NAME on domain $DOMAIN"

./create_database.sh "$TENANT_NAME"
./create_domain.sh "$DOMAIN"

source /var/www/eduorbit/venv/bin/activate
python provision_tenant.py --tenant "$TENANT_NAME" --domain "$DOMAIN"

echo "Provisioning complete for $TENANT_NAME."
