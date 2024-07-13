#!/bin/bash

# Variables
REPO_DIR="/opt/youtubeWebDownload"
SOCK_FILE="/opt/youtubeWebDownload/youtubeWebDownload.sock"
GUNICORN_SERVICE="gunicorn.service"

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

# Restart Gunicorn
echo "Restarting Gunicorn..."
if [ -f $SOCK_FILE ]; then
    pkill gunicorn
fi

nohup gunicorn --workers 3 --bind unix:$SOCK_FILE -m 007 app:app > gunicorn.log 2>&1 &

# Restart Nginx to apply any new configurations
echo "Restarting Nginx..."
systemctl restart nginx

echo "Deploy script finished."
