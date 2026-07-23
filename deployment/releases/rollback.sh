#!/bin/bash
set -e

RELEASES_DIR="/var/www/eduorbit/releases"
CURRENT_LINK="/var/www/eduorbit/current"

# Find the second most recent release
PREVIOUS_RELEASE=$(ls -1t "$RELEASES_DIR" | sed -n '2p')

if [ -z "$PREVIOUS_RELEASE" ]; then
    echo "No previous release found for rollback."
    exit 1
fi

echo "Rolling back to release: $PREVIOUS_RELEASE"

ln -sfn "$RELEASES_DIR/$PREVIOUS_RELEASE" "$CURRENT_LINK"

sudo systemctl restart gunicorn
sudo systemctl restart celery
sudo systemctl restart celerybeat

echo "Rollback successful."
