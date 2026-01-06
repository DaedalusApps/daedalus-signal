"""
Tags API endpoints
"""
from flask import Blueprint, request, jsonify, session
from app.database import get_session, close_session
from app.models import User, Tag
from app.security.auth import login_required
from app.config import MAX_TAGS_PER_USER

tags_bp = Blueprint('tags', __name__)


@tags_bp.route('', methods=['GET'])
@login_required
def get_tags():
    """Get all tags for the current user."""
    db = get_session()
    try:
        user = db.query(User).filter_by(id=session['user_id']).first()
        tags = [t.to_dict() for t in user.tags]
        return jsonify({'tags': tags}), 200
    finally:
        close_session(db)


@tags_bp.route('/defaults', methods=['GET'])
def get_default_tags():
    """Get all default tags."""
    db = get_session()
    try:
        tags = db.query(Tag).filter_by(is_default=True).all()
        return jsonify({'tags': [t.to_dict() for t in tags]}), 200
    finally:
        close_session(db)


@tags_bp.route('', methods=['POST'])
@login_required
def add_tag():
    """Add a tag for the current user."""
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Tag name required'}), 400
    
    db = get_session()
    try:
        user = db.query(User).filter_by(id=session['user_id']).first()
        
        if len(user.tags) >= MAX_TAGS_PER_USER:
            return jsonify({'error': f'Maximum {MAX_TAGS_PER_USER} tags allowed'}), 400
        
        tag_name = data['name'].lower().strip()
        
        # Check if tag already exists
        existing = db.query(Tag).filter_by(name=tag_name).first()
        if existing:
            if existing not in user.tags:
                user.tags.append(existing)
                db.commit()
            return jsonify({'tag': existing.to_dict()}), 200
        
        tag = Tag(
            name=tag_name,
            category=data.get('category')
        )
        db.add(tag)
        user.tags.append(tag)
        db.commit()
        
        return jsonify({'tag': tag.to_dict()}), 201
    except Exception as e:
        db.rollback()
        print(f"Add tag error: {e}")
        return jsonify({'error': 'Failed to add tag'}), 500
    finally:
        close_session(db)


@tags_bp.route('/<int:tag_id>', methods=['DELETE'])
@login_required
def remove_tag(tag_id):
    """Remove a tag from the current user."""
    db = get_session()
    try:
        user = db.query(User).filter_by(id=session['user_id']).first()
        tag = db.query(Tag).filter_by(id=tag_id).first()
        
        if not tag:
            return jsonify({'error': 'Tag not found'}), 404
        
        if tag in user.tags:
            user.tags.remove(tag)
            db.commit()
        
        return jsonify({'message': 'Tag removed'}), 200
    except Exception as e:
        db.rollback()
        print(f"Remove tag error: {e}")
        return jsonify({'error': 'Failed to remove tag'}), 500
    finally:
        close_session(db)
