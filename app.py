import os
import time
import logging
from logging.handlers import RotatingFileHandler
import asyncio
import schedule
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import HTTPException
import uuid
import yt_dlp
from urllib.parse import quote as url_quote

from config import Config
from downloader import is_valid_youtube_url, sanitize_filename, download_video, prepare_download_options

app = Flask(__name__, static_folder='static')
app.config.from_object(Config)

CORS(app, resources={r"/*": {"origins": "*"}})

limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)

handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

@app.route('/', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
async def index():
    try:
        if request.method == 'POST':
            return await handle_post_request()
        return render_template('index.html')
    except Exception as e:
        app.logger.error(f"Beklenmeyen hata: {str(e)}")
        return jsonify(error="Beklenmeyen bir hata oluştu"), 500

async def handle_post_request():
    url = request.form['url']
    quality = request.form['quality']
    format = request.form['format']

    if not is_valid_youtube_url(url):
        return jsonify({'error': 'Geçersiz YouTube URL\'si'}), 400

    ydl_opts = prepare_download_options(quality, format, app.config['UPLOAD_FOLDER'])

    try:
        app.logger.info(f"Downloading video from URL: {url} with options: {ydl_opts}")
        return await download_video(url, ydl_opts)
    except Exception as e:
        app.logger.error(f"İndirme hatası: {str(e)}")
        return jsonify({'error': f'Video indirme sırasında bir hata oluştu: {str(e)}'}), 500

@app.route('/preview', methods=['POST'])
async def preview():
    url = request.json['url']
    with yt_dlp.YoutubeDL() as ydl:
        info = ydl.extract_info(url, download=False)
        return jsonify({
            'title': info['title'],
            'duration': info['duration'],
            'thumbnail': info['thumbnail']
        })

@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return jsonify(error=str(e)), e.code
    app.logger.error(f"Beklenmeyen hata: {str(e)}")
    return jsonify(error="Beklenmeyen bir hata oluştu"), 500

def clean_downloads():
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            if os.path.getmtime(file_path) < time.time() - 86400:
                os.remove(file_path)
        except Exception as e:
            app.logger.error(f"Temizleme hatası: {str(e)}")

schedule.every().day.do(clean_downloads)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(host='0.0.0.0', port=5000, debug=True)
