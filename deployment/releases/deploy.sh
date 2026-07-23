#!/bin/bash
set -e

RELEASE_NAME=$(date +%Y%m%d%H%M%S)
RELEASES_DIR="/var/www/eduorbit/releases"
NEW_RELEASE_DIR="$RELEASES_DIR/$RELEASE_NAME"
CURRENT_LINK="/var/www/eduorbit/current"
REPO_URL="https://github.com/your-repo/eduorbit.git"

echo "Deploying new release: $RELEASE_NAME"

git clone "$REPO_URL" "$NEW_RELEASE_DIR"
cd "$NEW_RELEASE_DIR"

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput

ln -sfn "$NEW_RELEASE_DIR" "$CURRENT_LINK"

sudo systemctl restart gunicorn
sudo systemctl restart celery
sudo systemctl restart celerybeat

echo "Release $RELEASE_NAME deployed."
