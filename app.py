import os
import time
import logging
from logging.handlers import RotatingFileHandler
import asyncio
import schedule
from flask import Flask, render_template, request, send_file, jsonify, url_for
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import HTTPException
from werkzeug.utils import quote as url_quote  # Güncel import
import uuid
import yt_dlp

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
        info, temp_filename = await download_video(url, ydl_opts)

        original_filename = os.path.basename(temp_filename)
        sanitized_filename = sanitize_filename(original_filename)

        file_extension = os.path.splitext(original_filename)[1]
        unique_filename = f"{sanitized_filename}_{uuid.uuid4().hex[:8]}{file_extension}"

        full_file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

        os.rename(temp_filename, full_file_path)
        app.logger.info(f"Dosya indirme yolu: {full_file_path}")

        file_url = url_for('download_file', filename=unique_filename, _external=True)
        return jsonify({
            'url': file_url,
            'filename': unique_filename,
            'title': info.get('title'),
            'duration': info.get('duration'),
            'thumbnail': info.get('thumbnail'),
            'status': 'İndirme tamamlandı!'
        })
    except Exception as e:
        app.logger.error(f"İndirme hatası: {str(e)}")
        return jsonify({'error': f'Video indirme sırasında bir hata oluştu: {str(e)}'}), 500


@app.route('/download/<path:filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

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
    while True:
        schedule.run_pending()
        time.sleep(1)
