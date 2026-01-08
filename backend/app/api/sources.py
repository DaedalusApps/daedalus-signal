"""
Sources API endpoints
"""
from flask import Blueprint, request, jsonify, session
from app.database import get_session, close_session
from app.models import User, Source
from app.security.auth import login_required
from app.config import MAX_SOURCES_PER_USER

sources_bp = Blueprint('sources', __name__)


@sources_bp.route('', methods=['GET'])
@login_required
def get_sources():
    """Get all sources for the current user."""
    db = get_session()
    try:
        user = db.query(User).filter_by(id=session['user_id']).first()
        sources = [s.to_dict() for s in user.sources]
        return jsonify({'sources': sources}), 200
    finally:
        close_session(db)


@sources_bp.route('/defaults', methods=['GET'])
def get_default_sources():
    """Get all default sources."""
    from app.config import DATABASE_URL
    db = get_session()
    try:
        # Debug: count all sources first
        total = db.query(Source).count()
        sources = db.query(Source).filter_by(is_default=True, is_approved=True).all()
        return jsonify({
            'sources': [s.to_dict() for s in sources],
            '_debug': {
                'total_sources': total,
                'filtered_count': len(sources),
                'db_url_prefix': DATABASE_URL[:30] if DATABASE_URL else 'None'
            }
        }), 200
    finally:
        close_session(db)


@sources_bp.route('', methods=['POST'])
@login_required
def add_source():
    """Add a source for the current user."""
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('url') or not data.get('source_type'):
        return jsonify({'error': 'Name, URL, and source_type required'}), 400
    
    source_type = data['source_type']
    if source_type not in ['youtube', 'twitter', 'linkedin', 'github']:
        return jsonify({'error': 'Invalid source type'}), 400
    
    db = get_session()
    try:
        user = db.query(User).filter_by(id=session['user_id']).first()
        
        if len(user.sources) >= MAX_SOURCES_PER_USER:
            return jsonify({'error': f'Maximum {MAX_SOURCES_PER_USER} sources allowed'}), 400
        
        # Check if source already exists
        existing = db.query(Source).filter_by(url=data['url']).first()
        if existing:
            if existing not in user.sources:
                user.sources.append(existing)
                db.commit()
            return jsonify({'source': existing.to_dict()}), 200
        
        source = Source(
            name=data['name'],
            url=data['url'],
            source_type=source_type
        )
        db.add(source)
        user.sources.append(source)
        db.commit()
        
        return jsonify({'source': source.to_dict()}), 201
    except Exception as e:
        db.rollback()
        print(f"Add source error: {e}")
        return jsonify({'error': 'Failed to add source'}), 500
    finally:
        close_session(db)


@sources_bp.route('/<int:source_id>', methods=['DELETE'])
@login_required
def remove_source(source_id):
    """Remove a source from the current user."""
    db = get_session()
    try:
        user = db.query(User).filter_by(id=session['user_id']).first()
        source = db.query(Source).filter_by(id=source_id).first()
        
        if not source:
            return jsonify({'error': 'Source not found'}), 404
        
        if source in user.sources:
            user.sources.remove(source)
            db.commit()
        
        return jsonify({'message': 'Source removed'}), 200
    except Exception as e:
        db.rollback()
        print(f"Remove source error: {e}")
        return jsonify({'error': 'Failed to remove source'}), 500
    finally:
        close_session(db)
