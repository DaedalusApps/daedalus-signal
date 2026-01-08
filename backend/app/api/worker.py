"""
Worker API endpoints - for DreamHost workers to communicate with PythonAnywhere
"""
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from app.database import get_session, close_session
from app.models import Source, Content, User, Digest, EmailBlocklist
from app.security.worker import worker_required
from app.filtering.keyword import KeywordFilter

worker_bp = Blueprint('worker', __name__)


@worker_bp.route('/sources', methods=['GET'])
@worker_required
def get_sources():
    """
    Get all sources that need to be scraped.
    Returns source details for the worker to scrape externally.
    """
    db = get_session()
    try:
        sources = db.query(Source).filter_by(is_approved=True).all()
        return jsonify({
            'sources': [{
                'id': s.id,
                'name': s.name,
                'url': s.url,
                'source_type': s.source_type,
                'last_scraped': s.last_scraped.isoformat() if s.last_scraped else None
            } for s in sources]
        }), 200
    finally:
        close_session(db)


@worker_bp.route('/ingest', methods=['POST'])
@worker_required
def ingest_content():
    """
    Accept scraped content from DreamHost worker.
    Handles deduplication and saves to database.

    Expected payload:
    {
        "source_id": 123,
        "content": [
            {
                "title": "...",
                "description": "...",
                "url": "...",
                "content_type": "video|post|article|repo",
                "published_at": "ISO datetime or null",
                "relevance_score": 0-100 (optional, will be calculated if missing)
            }
        ]
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    source_id = data.get('source_id')
    content_list = data.get('content', [])

    if not source_id:
        return jsonify({'error': 'source_id required'}), 400

    db = get_session()
    try:
        # Verify source exists
        source = db.query(Source).filter_by(id=source_id).first()
        if not source:
            return jsonify({'error': 'Source not found'}), 404

        # Initialize filter for scoring (uses default tags)
        filter_engine = KeywordFilter()

        added = 0
        skipped = 0

        for item in content_list:
            url = item.get('url')
            if not url:
                skipped += 1
                continue

            # Deduplication: check if URL already exists
            existing = db.query(Content).filter_by(url=url).first()
            if existing:
                skipped += 1
                continue

            # Calculate relevance score if not provided
            relevance_score = item.get('relevance_score')
            if relevance_score is None:
                relevance_score = filter_engine.calculate_relevance(item)

            # Skip low-relevance content
            if relevance_score < 10:
                skipped += 1
                continue

            # Parse published_at if provided
            published_at = None
            if item.get('published_at'):
                try:
                    published_at = datetime.fromisoformat(
                        item['published_at'].replace('Z', '+00:00')
                    )
                except (ValueError, AttributeError):
                    pass

            content = Content(
                title=item.get('title', 'Untitled')[:500],
                description=(item.get('description', '') or '')[:2000],
                url=url,
                content_type=item.get('content_type', 'article'),
                source_id=source_id,
                relevance_score=relevance_score,
                published_at=published_at
            )
            db.add(content)
            added += 1

        # Update source last_scraped timestamp
        source.last_scraped = datetime.utcnow()
        db.commit()

        return jsonify({
            'message': 'Content ingested successfully',
            'added': added,
            'skipped': skipped,
            'source_id': source_id
        }), 200

    except Exception as e:
        db.rollback()
        print(f"Ingest error: {e}")
        return jsonify({'error': 'Failed to ingest content'}), 500
    finally:
        close_session(db)


@worker_bp.route('/digests', methods=['GET'])
@worker_required
def get_digests():
    """
    Get digest payloads for all active users.
    Returns pre-generated HTML digests ready to be emailed.
    """
    from app.email.digest import generate_digest_html

    db = get_session()
    try:
        # Get blocked emails
        blocked_emails = {b.email for b in db.query(EmailBlocklist).all()}

        # Get users with digest enabled and active
        users = db.query(User).filter(
            User.digest_enabled == True,
            User.is_active == True
        ).all()

        digests = []
        yesterday = datetime.utcnow() - timedelta(days=1)

        for user in users:
            if user.email in blocked_emails:
                continue

            # Get user's sources
            source_ids = [s.id for s in user.sources]
            if not source_ids:
                continue

            # Get top content from last 24 hours
            contents = db.query(Content)\
                .filter(Content.source_id.in_(source_ids))\
                .filter(Content.scraped_at >= yesterday)\
                .order_by(Content.relevance_score.desc())\
                .limit(10)\
                .all()

            if not contents:
                continue

            # Generate HTML digest
            digest_html = generate_digest_html(user.email, contents)
            content_ids = [c.id for c in contents]

            digests.append({
                'email': user.email,
                'digest_html': digest_html,
                'content_count': len(contents),
                'content_ids': content_ids
            })

        return jsonify({'digests': digests}), 200

    finally:
        close_session(db)


@worker_bp.route('/digest-sent', methods=['POST'])
@worker_required
def mark_digest_sent():
    """
    Record that a digest was sent successfully.

    Expected payload:
    {
        "email": "user@example.com",
        "content_ids": [1, 2, 3]
    }
    """
    data = request.get_json()

    if not data or not data.get('email'):
        return jsonify({'error': 'Email required'}), 400

    db = get_session()
    try:
        user = db.query(User).filter_by(email=data['email']).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        content_ids = ','.join(str(cid) for cid in data.get('content_ids', []))

        record = Digest(
            user_id=user.id,
            content_ids=content_ids,
            delivery_method='email'
        )
        db.add(record)
        db.commit()

        return jsonify({'message': 'Digest recorded'}), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        close_session(db)
