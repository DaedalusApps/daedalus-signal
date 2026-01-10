"""
Admin API endpoints
"""
from flask import Blueprint, request, jsonify
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


@admin_bp.route('/test-email', methods=['POST'])
@admin_required
def send_test_email():
    """Send a test digest email to the admin."""
    from app.email.digest import send_test_digest
    from app.config import ADMIN_EMAIL
    
    try:
        result = send_test_digest(ADMIN_EMAIL)
        if result:
            return jsonify({'message': f'Test email sent to {ADMIN_EMAIL}'}), 200
        else:
            return jsonify({'error': 'Failed to send test email. Check email settings.'}), 500
    except Exception as e:
        print(f"Test email error: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/test-email-payload', methods=['GET'])
@admin_required
def get_test_email_payload():
    """
    Generate a signed test email payload for browser-to-DreamHost flow.
    Returns JSON with digest_html and HMAC signature.
    """
    import json
    import time
    from app.email.digest import generate_digest_html
    from app.security.worker import generate_test_email_signature
    from app.config import ADMIN_EMAIL

    # Create sample content for testing
    sample_contents = [
        {
            'title': 'Test Email - DaedalusSignal Digest',
            'url': 'https://signal.daedalusapps.com',
            'description': 'This is a test email to verify your digest configuration is working correctly.',
            'relevance_score': 100,
            'content_type': 'test'
        },
        {
            'title': 'Sample Article: The Future of AI Agents',
            'url': 'https://example.com/ai-agents',
            'description': 'This is what a typical digest item would look like with a description preview.',
            'relevance_score': 85,
            'content_type': 'article'
        }
    ]

    digest_html = generate_digest_html(ADMIN_EMAIL, sample_contents)
    timestamp = int(time.time())

    payload = {
        'email': ADMIN_EMAIL,
        'digest_html': digest_html,
        'timestamp': timestamp,
        'is_test': True
    }

    payload_json = json.dumps(payload, sort_keys=True)
    signature = generate_test_email_signature(payload_json, timestamp)

    return jsonify({
        'payload': payload,
        'payload_json': payload_json,  # Exact JSON string used for signing
        'signature': signature
    }), 200


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete a user (admin only)."""
    from flask import session
    
    db = get_session()
    try:
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Prevent admin from deleting themselves
        if user.id == session.get('user_id'):
            return jsonify({'error': 'Cannot delete your own account from admin panel'}), 400
        
        db.delete(user)
        db.commit()
        
        return jsonify({'message': f'User {user.email} deleted'}), 200
    except Exception as e:
        db.rollback()
        print(f"Delete user error: {e}")
        return jsonify({'error': 'Failed to delete user'}), 500
    finally:
        close_session(db)


@admin_bp.route('/blocklist', methods=['GET'])
@admin_required
def get_blocklist():
    """Get all blocked emails."""
    from app.models import EmailBlocklist
    
    db = get_session()
    try:
        blocked = db.query(EmailBlocklist).order_by(EmailBlocklist.blocked_at.desc()).all()
        return jsonify({'blocklist': [b.to_dict() for b in blocked]}), 200
    finally:
        close_session(db)


@admin_bp.route('/blocklist/<int:blocklist_id>', methods=['DELETE'])
@admin_required
def unblock_email(blocklist_id):
    """Remove an email from the blocklist (unblock)."""
    from app.models import EmailBlocklist
    
    db = get_session()
    try:
        entry = db.query(EmailBlocklist).filter_by(id=blocklist_id).first()
        if not entry:
            return jsonify({'error': 'Blocklist entry not found'}), 404
        
        email = entry.email
        db.delete(entry)
        
        # Re-enable digest for user if they have an account
        user = db.query(User).filter_by(email=email).first()
        if user:
            user.digest_enabled = True
        
        db.commit()
        
        return jsonify({'message': f'{email} has been unblocked'}), 200
    except Exception as e:
        db.rollback()
        print(f"Unblock error: {e}")
        return jsonify({'error': 'Failed to unblock email'}), 500
    finally:
        close_session(db)


@admin_bp.route('/trigger-scrape-payload', methods=['GET'])
@admin_required
def get_trigger_scrape_payload():
    """
    Generate a signed payload for browser-to-DreamHost scraper trigger.
    Returns JSON with action and HMAC signature.
    """
    import json
    import time
    from app.security.worker import generate_test_email_signature
    
    timestamp = int(time.time())
    
    payload = {
        'action': 'run_scrapers',
        'timestamp': timestamp
    }
    
    payload_json = json.dumps(payload, sort_keys=True)
    signature = generate_test_email_signature(payload_json, timestamp)
    
    return jsonify({
        'payload': payload,
        'payload_json': payload_json,
        'signature': signature
    }), 200


@admin_bp.route('/trigger-mailer-payload', methods=['GET'])
@admin_required
def get_trigger_mailer_payload():
    """
    Generate a signed payload for browser-to-DreamHost mailer trigger.
    Returns JSON with action and HMAC signature.
    """
    import json
    import time
    from app.security.worker import generate_test_email_signature
    
    timestamp = int(time.time())
    
    payload = {
        'action': 'run_mailer',
        'timestamp': timestamp
    }
    
    payload_json = json.dumps(payload, sort_keys=True)
    signature = generate_test_email_signature(payload_json, timestamp)
    
    return jsonify({
        'payload': payload,
        'payload_json': payload_json,
        'signature': signature
    }), 200


@admin_bp.route('/get-logs-payload', methods=['GET'])
@admin_required
def get_logs_payload():
    """
    Generate a signed payload for fetching logs from DreamHost.
    Query param: log_type (scraper or mailer)
    """
    import json
    import time
    from app.security.worker import generate_test_email_signature
    
    log_type = request.args.get('log_type', 'scraper')
    
    # Validate log type
    if log_type not in ['scraper', 'mailer']:
        return jsonify({'error': 'Invalid log type'}), 400
    
    timestamp = int(time.time())
    
    payload = {
        'action': 'get_logs',
        'log_type': log_type,
        'timestamp': timestamp
    }
    
    payload_json = json.dumps(payload, sort_keys=True)
    signature = generate_test_email_signature(payload_json, timestamp)
    
    return jsonify({
        'payload': payload,
        'payload_json': payload_json,
        'signature': signature
    }), 200
