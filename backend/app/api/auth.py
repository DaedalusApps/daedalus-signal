"""
Authentication API endpoints
"""
import requests
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from app.database import get_session, close_session
from app.models import User, Digest, Feedback, VerificationCode
from app.security.auth import hash_password, verify_password, login_required
from app import limiter
from app.config import RATE_LIMIT_LOGIN, TURNSTILE_SECRET_KEY
from app.email.verification import (
    generate_verification_code,
    get_code_expiry,
    send_verification_email
)

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


def _create_and_send_verification_code(db, user_id: int, email: str, code_type: str) -> bool:
    """Create a verification code and send it via email."""
    # Invalidate any existing codes for this email and type
    db.query(VerificationCode).filter_by(
        email=email,
        code_type=code_type,
        used=False
    ).update({'used': True})

    # Generate new code
    code = generate_verification_code()
    verification = VerificationCode(
        user_id=user_id,
        email=email,
        code=code,
        code_type=code_type,
        expires_at=get_code_expiry()
    )
    db.add(verification)
    db.commit()

    # Send email
    return send_verification_email(email, code, code_type)


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

        user = User(
            email=email,
            password_hash=hash_password(password),
            email_verified=False
        )
        db.add(user)
        db.commit()

        # Create and send verification code
        _create_and_send_verification_code(db, user.id, email, 'email_verify')

        # Don't log in the user yet - they need to verify email first
        return jsonify({
            'message': 'Registration successful. Please check your email for verification code.',
            'verification_required': True,
            'email': email
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

        # Check if email is verified
        if not user.email_verified:
            # Send a new verification code
            _create_and_send_verification_code(db, user.id, email, 'email_verify')
            return jsonify({
                'error': 'Email not verified',
                'verification_required': True,
                'email': email
            }), 403

        session['user_id'] = user.id
        return jsonify({'user': user.to_dict()}), 200
    finally:
        close_session(db)


@auth_bp.route('/verify-email', methods=['POST'])
@limiter.limit(RATE_LIMIT_LOGIN)
def verify_email():
    """Verify email with 6-digit code."""
    data = request.get_json()

    if not data or not data.get('email') or not data.get('code'):
        return jsonify({'error': 'Email and code required'}), 400

    email = data['email'].lower().strip()
    code = data['code'].strip()

    db = get_session()
    try:
        # Find the verification code
        verification = db.query(VerificationCode).filter_by(
            email=email,
            code=code,
            code_type='email_verify',
            used=False
        ).first()

        if not verification:
            return jsonify({'error': 'Invalid verification code'}), 400

        # Check expiry
        if datetime.utcnow() > verification.expires_at:
            return jsonify({'error': 'Verification code has expired'}), 400

        # Mark code as used
        verification.used = True

        # Mark user as verified
        user = db.query(User).filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        user.email_verified = True
        db.commit()

        # Log the user in
        session['user_id'] = user.id
        return jsonify({
            'message': 'Email verified successfully',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.rollback()
        print(f"Verify email error: {e}")
        return jsonify({'error': 'Verification failed. Please try again.'}), 500
    finally:
        close_session(db)


@auth_bp.route('/resend-verification', methods=['POST'])
@limiter.limit("3 per minute")
def resend_verification():
    """Resend verification code."""
    data = request.get_json()

    if not data or not data.get('email'):
        return jsonify({'error': 'Email required'}), 400

    email = data['email'].lower().strip()

    db = get_session()
    try:
        user = db.query(User).filter_by(email=email).first()

        if not user:
            # Don't reveal whether email exists
            return jsonify({'message': 'If the email exists, a verification code has been sent.'}), 200

        if user.email_verified:
            return jsonify({'error': 'Email is already verified'}), 400

        # Create and send new verification code
        _create_and_send_verification_code(db, user.id, email, 'email_verify')

        return jsonify({'message': 'Verification code sent'}), 200
    except Exception as e:
        db.rollback()
        print(f"Resend verification error: {e}")
        return jsonify({'error': 'Failed to send verification code. Please try again.'}), 500
    finally:
        close_session(db)


@auth_bp.route('/forgot-password', methods=['POST'])
@limiter.limit("3 per minute")
def forgot_password():
    """Initiate password reset."""
    data = request.get_json()

    if not data or not data.get('email'):
        return jsonify({'error': 'Email required'}), 400

    email = data['email'].lower().strip()

    db = get_session()
    try:
        user = db.query(User).filter_by(email=email).first()

        # Always return success to prevent email enumeration
        if user:
            _create_and_send_verification_code(db, user.id, email, 'password_reset')

        return jsonify({
            'message': 'If the email exists, a password reset code has been sent.'
        }), 200
    except Exception as e:
        db.rollback()
        print(f"Forgot password error: {e}")
        return jsonify({'error': 'Failed to process request. Please try again.'}), 500
    finally:
        close_session(db)


@auth_bp.route('/reset-password', methods=['POST'])
@limiter.limit(RATE_LIMIT_LOGIN)
def reset_password():
    """Reset password with verification code."""
    data = request.get_json()

    if not data or not data.get('email') or not data.get('code') or not data.get('new_password'):
        return jsonify({'error': 'Email, code, and new password required'}), 400

    email = data['email'].lower().strip()
    code = data['code'].strip()
    new_password = data['new_password']

    if len(new_password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400

    db = get_session()
    try:
        # Find the verification code
        verification = db.query(VerificationCode).filter_by(
            email=email,
            code=code,
            code_type='password_reset',
            used=False
        ).first()

        if not verification:
            return jsonify({'error': 'Invalid reset code'}), 400

        # Check expiry
        if datetime.utcnow() > verification.expires_at:
            return jsonify({'error': 'Reset code has expired'}), 400

        # Mark code as used
        verification.used = True

        # Update user password
        user = db.query(User).filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        user.password_hash = hash_password(new_password)
        db.commit()

        return jsonify({'message': 'Password reset successfully'}), 200
    except Exception as e:
        db.rollback()
        print(f"Reset password error: {e}")
        return jsonify({'error': 'Password reset failed. Please try again.'}), 500
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
