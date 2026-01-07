"""
Content API endpoints
"""
from flask import Blueprint, request, jsonify, session
from sqlalchemy import desc
from app.database import get_session, close_session
from app.models import User, Content
from app.security.auth import login_required

content_bp = Blueprint('content', __name__)


@content_bp.route('', methods=['GET'])
@login_required
def get_content():
    """Get filtered content for the current user."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    source_type = request.args.get('source_type')
    
    per_page = min(per_page, 50)  # Max 50 items per page
    
    db = get_session()
    try:
        user = db.query(User).filter_by(id=session['user_id']).first()
        
        # Get user's source IDs
        source_ids = [s.id for s in user.sources]
        
        if not source_ids:
            return jsonify({'content': [], 'total': 0, 'page': page}), 200
        
        query = db.query(Content).filter(Content.source_id.in_(source_ids))
        
        if source_type:
            query = query.join(Content.source).filter(
                Content.source.has(source_type=source_type)
            )
        
        total = query.count()
        contents = query.order_by(desc(Content.relevance_score), desc(Content.scraped_at))\
            .offset((page - 1) * per_page)\
            .limit(per_page)\
            .all()
        
        return jsonify({
            'content': [c.to_dict() for c in contents],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }), 200
    finally:
        close_session(db)


@content_bp.route('/feed', methods=['GET'])
@login_required
def get_feed():
    """Get the latest content feed."""
    limit = request.args.get('limit', 10, type=int)
    limit = min(limit, 50)
    
    db = get_session()
    try:
        user = db.query(User).filter_by(id=session['user_id']).first()
        source_ids = [s.id for s in user.sources]
        
        if not source_ids:
            return jsonify({'feed': []}), 200
        
        contents = db.query(Content)\
            .filter(Content.source_id.in_(source_ids))\
            .order_by(desc(Content.scraped_at))\
            .limit(limit)\
            .all()
        
        return jsonify({'feed': [c.to_dict() for c in contents]}), 200
    finally:
        close_session(db)


@content_bp.route('/digest', methods=['GET'])
@login_required
def get_digest():
    """Get the daily digest content (top items)."""
    db = get_session()
    try:
        user = db.query(User).filter_by(id=session['user_id']).first()
        source_ids = [s.id for s in user.sources]
        
        if not source_ids:
            return jsonify({'digest': []}), 200
        
        # Get top 10 items by relevance score
        contents = db.query(Content)\
            .filter(Content.source_id.in_(source_ids))\
            .order_by(desc(Content.relevance_score))\
            .limit(10)\
            .all()
        
        return jsonify({'digest': [c.to_dict() for c in contents]}), 200
    finally:
        close_session(db)


@content_bp.route('/new-count', methods=['GET'])
@login_required
def get_new_count():
    """Get count of new content since a given timestamp."""
    from datetime import datetime
    
    since = request.args.get('since')
    if not since:
        return jsonify({'count': 0}), 200
    
    try:
        since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
    except ValueError:
        return jsonify({'error': 'Invalid timestamp format'}), 400
    
    db = get_session()
    try:
        user = db.query(User).filter_by(id=session['user_id']).first()
        source_ids = [s.id for s in user.sources]
        
        if not source_ids:
            return jsonify({'count': 0}), 200
        
        count = db.query(Content)\
            .filter(Content.source_id.in_(source_ids))\
            .filter(Content.scraped_at > since_dt)\
            .count()
        
        return jsonify({'count': count}), 200
    finally:
        close_session(db)
