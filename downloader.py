import os
import re
import asyncio
import yt_dlp
from werkzeug.utils import secure_filename
from flask import Response
import uuid
from urllib.parse import quote as url_quote
from config import Config


def is_valid_youtube_url(url):
    youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    return re.match(youtube_regex, url) is not None


def sanitize_filename(filename):
    # Dosya adından emoji ve özel karakterleri kaldır
    sanitized = re.sub(r'[^\w\-_\. ]', '_', filename)
    # Dosya adını 50 karakterle sınırla
    return sanitized[:50]


def generate(filename):
    chunk_size = 8192
    with open(filename, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk

    # Dosyayı sil
    os.remove(filename)


async def download_video(url, ydl_opts):
    loop = asyncio.get_event_loop()
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
        if info is None:
            raise ValueError("Video bilgileri alınamadı.")

        filename = ydl.prepare_filename(info)
        sanitized_filename = sanitize_filename(os.path.basename(filename))

        if not os.path.exists(filename):
            raise FileNotFoundError(f"Dosya bulunamadı: {filename}")

        mimetype = 'video/mp4' if filename.endswith('.mp4') else 'audio/mpeg'
        response = Response(
            generate(filename),
            mimetype=mimetype,
            headers={
                'Content-Disposition': f'attachment; filename="{url_quote(sanitized_filename)}"',
                'Content-Type': mimetype
            }
        )

        return response


def prepare_download_options(quality, format, upload_folder):
    ydl_opts = {
        'outtmpl': os.path.join(upload_folder, '%(title)s.%(ext)s'),
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best' if format != 'mp3' else 'bestaudio/best',
    }

    if quality == '480p':
        ydl_opts['format'] = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]'
    elif quality == '720p':
        ydl_opts['format'] = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]'

    if format == 'mp3':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    return ydl_opts


def download_file(file_url):
    local_filename = url_quote(file_url.split('/')[-1])
    local_path = os.path.join(Config.UPLOAD_FOLDER, local_filename)

    with requests.get(file_url, stream=True) as r:
        r.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    return local_path
