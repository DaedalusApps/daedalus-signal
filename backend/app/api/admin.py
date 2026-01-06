"""
Admin API endpoints
"""
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from app.database import get_session, close_session
from app.models import User, Source, Tag, Content, Feedback
from app.security.auth import admin_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_stats():
    """Get system statistics."""
    db = get_session()
    try:
        stats = {
            'users': db.query(User).count(),
            'sources': db.query(Source).count(),
            'tags': db.query(Tag).count(),
            'contents': db.query(Content).count(),
            'feedback_pending': db.query(Feedback).filter_by(status='pending').count()
        }
        return jsonify({'stats': stats}), 200
    finally:
        close_session(db)


@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    """Get all users."""
    db = get_session()
    try:
        users = db.query(User).all()
        return jsonify({'users': [u.to_dict() for u in users]}), 200
    finally:
        close_session(db)


@admin_bp.route('/sources', methods=['GET'])
@admin_required
def get_all_sources():
    """Get all sources with approval status."""
    db = get_session()
    try:
        sources = db.query(Source).all()
        return jsonify({'sources': [s.to_dict() for s in sources]}), 200
    finally:
        close_session(db)


@admin_bp.route('/sources/<int:source_id>/approve', methods=['POST'])
@admin_required
def approve_source(source_id):
    """Approve a source as default."""
    db = get_session()
    try:
        source = db.query(Source).filter_by(id=source_id).first()
        if not source:
            return jsonify({'error': 'Source not found'}), 404
        
        source.is_approved = True
        source.is_default = True
        db.commit()
        
        return jsonify({'source': source.to_dict()}), 200
    except Exception as e:
        db.rollback()
        print(f"Approve source error: {e}")
        return jsonify({'error': 'Failed to approve source'}), 500
    finally:
        close_session(db)


@admin_bp.route('/tags', methods=['GET'])
@admin_required
def get_all_tags():
    """Get all tags."""
    db = get_session()
    try:
        tags = db.query(Tag).all()
        return jsonify({'tags': [t.to_dict() for t in tags]}), 200
    finally:
        close_session(db)


@admin_bp.route('/tags/<int:tag_id>/approve', methods=['POST'])
@admin_required
def approve_tag(tag_id):
    """Approve a tag as default."""
    db = get_session()
    try:
        tag = db.query(Tag).filter_by(id=tag_id).first()
        if not tag:
            return jsonify({'error': 'Tag not found'}), 404
        
        tag.is_default = True
        db.commit()
        
        return jsonify({'tag': tag.to_dict()}), 200
    except Exception as e:
        db.rollback()
        print(f"Approve tag error: {e}")
        return jsonify({'error': 'Failed to approve tag'}), 500
    finally:
        close_session(db)


@admin_bp.route('/feedback', methods=['GET'])
@admin_required
def get_feedback():
    """Get all feedback."""
    status = request.args.get('status')
    
    db = get_session()
    try:
        query = db.query(Feedback)
        if status:
            query = query.filter_by(status=status)
        
        feedback_items = query.order_by(Feedback.created_at.desc()).all()
        return jsonify({
            'feedback': [{
                'id': f.id,
                'email': f.email,
                'message': f.message,
                'feedback_type': f.feedback_type,
                'status': f.status,
                'created_at': f.created_at.isoformat()
            } for f in feedback_items]
        }), 200
    finally:
        close_session(db)
