import os
from pathlib import Path

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'varsayilan_gizli_anahtar')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = str(Path.home() / "Downloads")
    ALLOWED_EXTENSIONS = {'mp4', 'mp3'}