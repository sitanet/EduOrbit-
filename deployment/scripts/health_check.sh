#!/bin/bash
set -e

URL="http://localhost/health/"

echo "Checking health of $URL..."
HTTP_STATUS=$(curl -o /dev/null -s -w "%{http_code}\n" "$URL")

if [ "$HTTP_STATUS" -eq 200 ]; then
    echo "Health check passed."
    exit 0
else
    echo "Health check failed with status $HTTP_STATUS."
    exit 1
fi
