#!/bin/bash
set -e

echo "Starting deployment..."
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
sudo systemctl restart celery
sudo systemctl restart celerybeat
echo "Deployment successful."
