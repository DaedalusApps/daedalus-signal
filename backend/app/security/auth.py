"""
Security utilities for authentication
"""
import bcrypt
from functools import wraps
from flask import session, jsonify
from app.database import get_session, close_session
from app.models import User
from app.config import ADMIN_EMAIL, ADMIN_PASSWORD, BCRYPT_ROUNDS


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def login_required(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        db = get_session()
        try:
            user = db.query(User).filter_by(id=session['user_id']).first()
            if not user or not user.is_admin:
                return jsonify({'error': 'Admin access required'}), 403
            return f(*args, **kwargs)
        finally:
            close_session(db)
    return decorated_function


def get_current_user():
    """Get the current authenticated user."""
    if 'user_id' not in session:
        return None
    
    db = get_session()
    try:
        user = db.query(User).filter_by(id=session['user_id']).first()
        return user
    finally:
        close_session(db)


def create_admin_if_not_exists():
    """Create the admin user if it doesn't exist."""
    db = get_session()
    try:
        admin = db.query(User).filter_by(email=ADMIN_EMAIL).first()
        if not admin:
            admin = User(
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PASSWORD),
                is_admin=True,
                onboarding_complete=True
            )
            db.add(admin)
            db.commit()
            print(f"Admin user created: {ADMIN_EMAIL}")
    except Exception as e:
        db.rollback()
        print(f"Error creating admin: {e}")
    finally:
        close_session(db)
