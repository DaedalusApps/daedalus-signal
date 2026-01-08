"""
Authentication API endpoints
"""
from flask import Blueprint, request, jsonify, session
from app.database import get_session, close_session
from app.models import User, Digest, Feedback
from app.security.auth import hash_password, verify_password, login_required
from app import limiter
from app.config import RATE_LIMIT_LOGIN

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
@limiter.limit(RATE_LIMIT_LOGIN)
def register():
    """Register a new user."""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    email = data['email'].lower().strip()
    password = data['password']
    
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    
    db = get_session()
    try:
        existing = db.query(User).filter_by(email=email).first()
        if existing:
            return jsonify({'error': 'Email already registered'}), 409
        
        user = User(
            email=email,
            password_hash=hash_password(password)
        )
        db.add(user)
        db.commit()
        
        session['user_id'] = user.id
        return jsonify({'user': user.to_dict()}), 201
    except Exception as e:
        db.rollback()
        print(f"Registration error: {e}")  # Log for debugging
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
        print(f"Update error: {e}")  # Log for debugging
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
