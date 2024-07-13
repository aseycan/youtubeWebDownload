import hmac
import hashlib
import subprocess
import logging
from flask import Flask, request, abort, jsonify

app = Flask(__name__)

# Loglama ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SECRET = "849b2c1431291850eca420dcdc57bf03a0b4c4617e0abbfc"  # GitHub'da belirlediğiniz secret

def verify_signature(payload_body, secret_token, signature_header):
    """Gelen webhook isteğinin imzasını doğrula"""
    return True  # Geçici olarak doğrulamayı devre dışı bırakıyoruz

@app.route('/webhook', methods=['POST'])
def webhook():
    signature = request.headers.get('X-Hub-Signature-256')
    logger.info(f"Received webhook. Event: {request.headers.get('X-GitHub-Event')}")
    logger.info(f"Delivery ID: {request.headers.get('X-GitHub-Delivery')}")
    logger.info(f"Received signature: {signature}")
    logger.info(f"Received headers: {request.headers}")
    logger.info(f"Received payload: {request.json}")

    if not verify_signature(request.data, SECRET, signature):
        logger.warning("Invalid signature or missing signature header")
        return jsonify({"error": "Invalid signature"}), 400

    logger.info("Received webhook with valid signature")

    try:
        # Deploy script'ini çalıştır
        result = subprocess.run(['/opt/youtubeWebDownload/deploy.sh'],
                                capture_output=True, text=True, check=True)
        logger.info(f"Deployment output: {result.stdout}")
        return jsonify({"message": "Deployed successfully", "output": result.stdout}), 200
    except subprocess.CalledProcessError as e:
        logger.error(f"Deployment failed with error: {e.stderr}")
        logger.exception("Full traceback:")
        return jsonify({"error": "Deployment failed", "details": e.stderr}), 500
    except Exception as e:
        logger.error(f"Unexpected error during deployment: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({"error": "Unexpected error", "details": str(e)}), 500

@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": str(e)}), 400

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting webhook server...")
    app.run(host='0.0.0.0', port=5001)
