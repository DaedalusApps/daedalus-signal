"""
Worker authentication utilities for DreamHost worker communication
"""
import hmac
import hashlib
import time
from functools import wraps
from flask import request, jsonify
from app.config import WORKER_SECRET, SECRET_KEY


def worker_required(f):
    """
    Decorator to require worker authentication via HMAC signature.

    Expected headers:
    - X-Worker-Signature: HMAC-SHA256 of timestamp:body using WORKER_SECRET
    - X-Worker-Timestamp: Unix timestamp (must be within 5 minutes)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not WORKER_SECRET:
            return jsonify({'error': 'Worker authentication not configured'}), 500

        signature = request.headers.get('X-Worker-Signature', '')
        timestamp = request.headers.get('X-Worker-Timestamp', '')

        if not signature or not timestamp:
            return jsonify({'error': 'Missing worker authentication headers'}), 401

        # Validate timestamp (prevent replay attacks)
        try:
            ts = int(timestamp)
            if abs(time.time() - ts) > 300:  # 5 minute window
                return jsonify({'error': 'Request timestamp expired'}), 401
        except ValueError:
            return jsonify({'error': 'Invalid timestamp'}), 401

        # Compute expected signature
        body = request.get_data(as_text=True) or ''
        message = f"{timestamp}:{body}"
        expected = hmac.new(
            WORKER_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected, signature):
            return jsonify({'error': 'Invalid worker signature'}), 403

        return f(*args, **kwargs)
    return decorated_function


def generate_test_email_signature(payload_json: str, timestamp: int) -> str:
    """
    Generate HMAC signature for test email payload.
    Used by frontend to verify payload before sending to DreamHost.

    Args:
        payload_json: JSON string of the payload
        timestamp: Unix timestamp

    Returns:
        HMAC-SHA256 hex digest
    """
    message = f"{timestamp}:{payload_json}"
    return hmac.new(
        SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()


def verify_test_email_signature(payload_json: str, timestamp: int, signature: str) -> bool:
    """
    Verify test email payload signature.

    Args:
        payload_json: JSON string of the payload
        timestamp: Unix timestamp
        signature: HMAC signature to verify

    Returns:
        True if signature is valid and not expired
    """
    # 10 minute window for test emails
    if abs(time.time() - timestamp) > 600:
        return False
    expected = generate_test_email_signature(payload_json, timestamp)
    return hmac.compare_digest(expected, signature)
