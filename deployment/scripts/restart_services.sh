#!/bin/bash
set -e

echo "Restarting services..."
sudo systemctl restart gunicorn
sudo systemctl restart celery
sudo systemctl restart celerybeat
echo "Services restarted successfully."
