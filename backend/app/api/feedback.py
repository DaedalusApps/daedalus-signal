"""
Feedback API endpoints
"""
from flask import Blueprint, request, jsonify, session
from app.database import get_session, close_session
from app.models import Feedback

feedback_bp = Blueprint('feedback', __name__)


@feedback_bp.route('', methods=['POST'])
def submit_feedback():
    """Submit user feedback."""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('message'):
        return jsonify({'error': 'Email and message required'}), 400
    
    db = get_session()
    try:
        feedback = Feedback(
            user_id=session.get('user_id'),
            email=data['email'],
            message=data['message'],
            feedback_type=data.get('feedback_type', 'general')
        )
        db.add(feedback)
        db.commit()
        
        return jsonify({'message': 'Feedback submitted successfully'}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        close_session(db)
