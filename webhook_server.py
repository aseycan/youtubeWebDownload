import hmac
import hashlib
from flask import Flask, request, abort
import subprocess

app = Flask(__name__)

SECRET = "849b2c1431291850eca420dcdc57bf03a0b4c4617e0abbfc"  # GitHub'da belirlediğiniz secret


@app.route('/webhook', methods=['POST'])
def webhook():
    signature = request.headers.get('X-Hub-Signature-256')
    if not signature:
        abort(400, "X-Hub-Signature-256 header is missing")

    hash_object = hmac.new(SECRET.encode('utf-8'), msg=request.data, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        abort(400, "Invalid signature")

    # Webhook işlemleri burada devam eder
    subprocess.call(['/root/deploy.sh'])
    return 'Deployed successfully', 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)