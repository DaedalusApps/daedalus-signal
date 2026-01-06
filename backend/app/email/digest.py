"""
Email digest system with console output mode
"""
from datetime import datetime, timedelta
from app.database import get_session, close_session
from app.models import User, Content, Digest
from app.config import EMAIL_MODE


def generate_digest(user_id: int) -> dict:
    """Generate a digest for a user."""
    db = get_session()
    try:
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            return None
        
        source_ids = [s.id for s in user.sources]
        if not source_ids:
            return {'user': user.email, 'content': [], 'message': 'No sources configured'}
        
        # Get top content from the last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        contents = db.query(Content)\
            .filter(Content.source_id.in_(source_ids))\
            .filter(Content.scraped_at >= yesterday)\
            .order_by(Content.relevance_score.desc())\
            .limit(10)\
            .all()
        
        return {
            'user': user.email,
            'content': [c.to_dict() for c in contents],
            'generated_at': datetime.utcnow().isoformat()
        }
    finally:
        close_session(db)


def send_digest(digest: dict) -> bool:
    """Send or display the digest based on EMAIL_MODE."""
    if not digest or not digest.get('content'):
        return False
    
    if EMAIL_MODE == 'console':
        # Console output mode
        print("\n" + "=" * 60)
        print(f"📧 DAILY DIGEST for {digest['user']}")
        print(f"   Generated: {digest['generated_at']}")
        print("=" * 60)
        
        for i, item in enumerate(digest['content'], 1):
            print(f"\n{i}. [{item['content_type'].upper()}] {item['title']}")
            print(f"   Score: {item['relevance_score']}")
            print(f"   URL: {item['url']}")
            if item.get('description'):
                desc = item['description'][:200] + '...' if len(item.get('description', '')) > 200 else item.get('description', '')
                print(f"   {desc}")
        
        print("\n" + "=" * 60 + "\n")
        return True
    
    else:
        # SMTP mode (implement when needed)
        print(f"SMTP mode not configured. Would send to: {digest['user']}")
        return False


def run_daily_digest():
    """Run the daily digest for all opted-in users."""
    db = get_session()
    try:
        users = db.query(User).filter_by(digest_enabled=True).all()
        
        print(f"Running daily digest for {len(users)} users...")
        
        for user in users:
            digest = generate_digest(user.id)
            if digest and digest.get('content'):
                sent = send_digest(digest)
                
                if sent:
                    # Record the digest
                    content_ids = ','.join(str(c['id']) for c in digest['content'])
                    record = Digest(
                        user_id=user.id,
                        content_ids=content_ids,
                        delivery_method='console' if EMAIL_MODE == 'console' else 'email'
                    )
                    db.add(record)
        
        db.commit()
        print("Daily digest complete!")
        
    except Exception as e:
        print(f"Digest error: {e}")
        db.rollback()
    finally:
        close_session(db)
