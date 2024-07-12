import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, send_file, jsonify, url_for
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import HTTPException
import yt_dlp
import io

from config import Config
from downloader import is_valid_youtube_url, prepare_download_options

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

    ydl_opts = prepare_download_options(quality, format)

    try:
        app.logger.info(f"Downloading video from URL: {url} with options: {ydl_opts}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            filename = ydl.prepare_filename(info)

            buffer = io.BytesIO()
            ydl.download_to_buffer(buffer, url)
            buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='audio/mpeg' if format == 'mp3' else 'video/mp4'
        )
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)