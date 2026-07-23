#!/bin/bash
set -e

echo "Starting update..."
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
echo "Update successful."
