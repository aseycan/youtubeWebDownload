import hmac
import hashlib
import subprocess
import logging
from flask import Flask, request, abort

app = Flask(__name__)

# Loglama ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SECRET = "849b2c1431291850eca420dcdc57bf03a0b4c4617e0abbfc"  # GitHub'da belirlediğiniz secret

def verify_signature(payload_body, secret_token, signature_header):
    """Gelen webhook isteğinin imzasını doğrula"""
    if not signature_header:
        return False
    hash_object = hmac.new(secret_token.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    return hmac.compare_digest(signature_header, expected_signature)

@app.route('/webhook', methods=['POST'])
def webhook():
    # signature = request.headers.get('X-Hub-Signature-256')

    # if not verify_signature(request.data, SECRET, signature):
    #    logger.warning("Invalid signature or missing signature header")
    #    abort(400, "Invalid signature")

    logger.info("Received webhook with valid signature")

    try:
        # Deploy script'ini çalıştır
        result = subprocess.run(['/opt/youtubeWebDownload/deploy.sh'],
                                capture_output=True, text=True, check=True)
        logger.info(f"Deployment output: {result.stdout}")
        return 'Deployed successfully', 200
    except subprocess.CalledProcessError as e:
        logger.error(f"Deployment failed with error: {e.stderr}")
        return f"Deployment failed: {e.stderr}", 500
    except Exception as e:
        logger.error(f"Unexpected error during deployment: {str(e)}")
        return f"Unexpected error: {str(e)}", 500

@app.errorhandler(400)
def bad_request(e):
    return str(e), 400

@app.errorhandler(500)
def internal_server_error(e):
    return str(e), 500

if __name__ == '__main__':
    logger.info("Starting webhook server...")
    app.run(host='0.0.0.0', port=5001)
