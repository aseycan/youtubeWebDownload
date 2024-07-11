import os
import re
import asyncio
import yt_dlp
from werkzeug.utils import secure_filename
import uuid
from urllib.parse import quote as url_quote

def is_valid_youtube_url(url):
    youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    return re.match(youtube_regex, url) is not None


def sanitize_filename(filename):
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    return filename[:50]


async def download_video(url, ydl_opts):
    loop = asyncio.get_event_loop()
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
        if info is None:
            raise ValueError("Video bilgileri alınamadı.")

        filename = ydl.prepare_filename(info)
        return info, filename


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