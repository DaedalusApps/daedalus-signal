"""
Unsubscribe API endpoints
"""
import hmac
import hashlib
from flask import Blueprint, request, jsonify
from app.database import get_session, close_session
from app.models import EmailBlocklist, User
from app.config import SECRET_KEY

unsubscribe_bp = Blueprint('unsubscribe', __name__)


def generate_unsubscribe_token(email: str) -> str:
    """Generate a signed token for unsubscribe links."""
    signature = hmac.new(
        SECRET_KEY.encode(),
        email.encode(),
        hashlib.sha256
    ).hexdigest()[:32]
    return signature


def verify_unsubscribe_token(email: str, token: str) -> bool:
    """Verify an unsubscribe token."""
    expected = generate_unsubscribe_token(email)
    return hmac.compare_digest(expected, token)


@unsubscribe_bp.route('/<token>', methods=['GET'])
def unsubscribe(token):
    """
    Unsubscribe an email from digest emails.
    Token format: first 32 chars of HMAC signature, email in query param
    """
    email = request.args.get('email', '').lower().strip()
    
    if not email:
        return jsonify({'error': 'Email required'}), 400
    
    if not verify_unsubscribe_token(email, token):
        return jsonify({'error': 'Invalid or expired unsubscribe link'}), 403
    
    db = get_session()
    try:
        # Check if already blocked
        existing = db.query(EmailBlocklist).filter_by(email=email).first()
        if existing:
            return jsonify({'message': f'{email} is already unsubscribed'}), 200
        
        # Add to blocklist
        blocklist_entry = EmailBlocklist(
            email=email,
            reason='user_unsubscribed'
        )
        db.add(blocklist_entry)
        
        # Also disable digest for user if they have an account
        user = db.query(User).filter_by(email=email).first()
        if user:
            user.digest_enabled = False
        
        db.commit()
        
        return jsonify({
            'message': f'{email} has been unsubscribed from digest emails',
            'email': email
        }), 200
        
    except Exception as e:
        db.rollback()
        print(f"Unsubscribe error: {e}")
        return jsonify({'error': 'Failed to unsubscribe'}), 500
    finally:
        close_session(db)
