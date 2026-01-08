"""
Authentication API endpoints
"""
import requests
from flask import Blueprint, request, jsonify, session
from app.database import get_session, close_session
from app.models import User, Digest, Feedback, VerificationCode
from app.security.auth import hash_password, verify_password, login_required
from app import limiter
from app.config import RATE_LIMIT_LOGIN, TURNSTILE_SECRET_KEY

auth_bp = Blueprint('auth', __name__)


def verify_turnstile(token: str) -> bool:
    """Verify Cloudflare Turnstile token."""
    if not TURNSTILE_SECRET_KEY:
        # Skip verification if not configured (development mode)
        print("Warning: Turnstile not configured, skipping verification")
        return True

    try:
        response = requests.post(
            'https://challenges.cloudflare.com/turnstile/v0/siteverify',
            data={
                'secret': TURNSTILE_SECRET_KEY,
                'response': token
            },
            timeout=10
        )
        result = response.json()
        return result.get('success', False)
    except Exception as e:
        print(f"Turnstile verification error: {e}")
        return False


@auth_bp.route('/register', methods=['POST'])
@limiter.limit(RATE_LIMIT_LOGIN)
def register():
    """Register a new user."""
    data = request.get_json()

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400

    email = data['email'].lower().strip()
    password = data['password']
    turnstile_token = data.get('turnstile_token')

    # Verify Turnstile CAPTCHA
    if TURNSTILE_SECRET_KEY and not turnstile_token:
        return jsonify({'error': 'CAPTCHA verification required'}), 400

    if not verify_turnstile(turnstile_token or ''):
        return jsonify({'error': 'CAPTCHA verification failed'}), 400

    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400

    db = get_session()
    try:
        existing = db.query(User).filter_by(email=email).first()
        if existing:
            return jsonify({'error': 'Email already registered'}), 409

        # Account is immediately verified after passing CAPTCHA
        user = User(
            email=email,
            password_hash=hash_password(password),
            email_verified=True
        )
        db.add(user)
        db.commit()

        # Log the user in immediately
        session['user_id'] = user.id

        return jsonify({
            'message': 'Registration successful',
            'user': user.to_dict()
        }), 201
    except Exception as e:
        db.rollback()
        print(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed. Please try again.'}), 500
    finally:
        close_session(db)


@auth_bp.route('/login', methods=['POST'])
@limiter.limit(RATE_LIMIT_LOGIN)
def login():
    """Login a user."""
    data = request.get_json()

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400

    email = data['email'].lower().strip()
    password = data['password']

    db = get_session()
    try:
        user = db.query(User).filter_by(email=email).first()

        if not user or not verify_password(password, user.password_hash):
            return jsonify({'error': 'Invalid credentials'}), 401

        if not user.is_active:
            return jsonify({'error': 'Account is disabled'}), 403

        session['user_id'] = user.id
        return jsonify({'user': user.to_dict()}), 200
    finally:
        close_session(db)


@auth_bp.route('/forgot-password', methods=['POST'])
@limiter.limit("3 per minute")
def forgot_password():
    """Submit a password reset request to admin."""
    data = request.get_json()

    if not data or not data.get('email'):
        return jsonify({'error': 'Email required'}), 400

    email = data['email'].lower().strip()
    message = data.get('message', '').strip()

    db = get_session()
    try:
        # Create a feedback entry for password reset request
        user = db.query(User).filter_by(email=email).first()

        feedback = Feedback(
            user_id=user.id if user else None,
            email=email,
            message=message or 'Password reset requested',
            feedback_type='password_reset',
            status='pending'
        )
        db.add(feedback)
        db.commit()

        return jsonify({
            'message': 'Your password reset request has been submitted. An administrator will review it and contact you.'
        }), 200
    except Exception as e:
        db.rollback()
        print(f"Forgot password error: {e}")
        return jsonify({'error': 'Failed to submit request. Please try again.'}), 500
    finally:
        close_session(db)


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout the current user."""
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'}), 200


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get the current authenticated user."""
    db = get_session()
    try:
        user = db.query(User).filter_by(id=session['user_id']).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({'user': user.to_dict()}), 200
    finally:
        close_session(db)


@auth_bp.route('/me', methods=['PATCH'])
@login_required
def update_current_user():
    """Update the current user's settings."""
    data = request.get_json()

    db = get_session()
    try:
        user = db.query(User).filter_by(id=session['user_id']).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if 'digest_enabled' in data:
            user.digest_enabled = bool(data['digest_enabled'])

        if 'onboarding_complete' in data:
            user.onboarding_complete = bool(data['onboarding_complete'])

        db.commit()
        return jsonify({'user': user.to_dict()}), 200
    except Exception as e:
        db.rollback()
        print(f"Update error: {e}")
        return jsonify({'error': 'Update failed. Please try again.'}), 500
    finally:
        close_session(db)


@auth_bp.route('/me', methods=['DELETE'])
@login_required
def delete_account():
    """Delete the current user's account."""
    db = get_session()
    try:
        user = db.query(User).filter_by(id=session['user_id']).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if user.is_admin:
            return jsonify({'error': 'Admin accounts cannot be deleted this way'}), 400

        email = user.email

        # Clear associations before deleting to avoid FK constraints
        user.sources.clear()
        user.tags.clear()

        # Delete related records that have FK to user
        db.query(Digest).filter_by(user_id=user.id).delete()
        db.query(Feedback).filter_by(user_id=user.id).delete()
        db.query(VerificationCode).filter_by(user_id=user.id).delete()

        db.delete(user)
        db.commit()
        session.pop('user_id', None)

        return jsonify({'message': f'Account {email} deleted successfully'}), 200
    except Exception as e:
        db.rollback()
        print(f"Delete account error: {e}")
        return jsonify({'error': 'Failed to delete account. Please try again.'}), 500
    finally:
        close_session(db)
