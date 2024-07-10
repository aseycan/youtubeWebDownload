#!/bin/bash
set -e

echo "Deploying application..."

# Proje dizinine git
cd /root/youtubeWebDownload

# En son değişiklikleri çek
echo "Fetching latest changes..."
git pull origin main

# Virtual environment'ı aktive et
echo "Activating virtual environment..."
source venv/bin/activate

# Bağımlılıkları yükle
echo "Installing dependencies..."
pip install -r requirements.txt

# Uygulamayı yeniden başlat
echo "Restarting application..."
sudo supervisorctl restart youtubewebdownload

echo "Deployment completed successfully!"