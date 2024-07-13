#!/bin/bash

# Variables
REPO_DIR="/opt/youtubeWebDownload"
APP_SOCK_FILE="/opt/youtubeWebDownload/app.sock"
WEBHOOK_SOCK_FILE="/opt/youtubeWebDownload/webhook.sock"

echo "Deploy script started..."

# Change to the repository directory
cd $REPO_DIR || exit

# Stash any local changes
git stash

# Pull the latest changes from the repository
git pull origin master

# Install/update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart Gunicorn for app.py
echo "Restarting Gunicorn for app.py..."
if [ -f $APP_SOCK_FILE ]; then
    pkill -f "gunicorn --workers 3 --bind unix:$APP_SOCK_FILE"
fi

nohup gunicorn --workers 3 --bind unix:$APP_SOCK_FILE -m 007 app:app > gunicorn_app.log 2>&1 &

# Restart Gunicorn for webhook_server.py
echo "Restarting Gunicorn for webhook_server.py..."
if [ -f $WEBHOOK_SOCK_FILE ]; then
    pkill -f "gunicorn --workers 3 --bind unix:$WEBHOOK_SOCK_FILE"
fi

nohup gunicorn --workers 3 --bind unix:$WEBHOOK_SOCK_FILE -m 007 webhook_server:app > gunicorn_webhook.log 2>&1 &

# Restart Nginx to apply any new configurations
echo "Restarting Nginx..."
systemctl restart nginx

echo "Deploy script finished."
