"""
Email digest system with console output mode
"""
from datetime import datetime, timedelta
from app.database import get_session, close_session
from app.models import User, Content, Digest
from app.config import EMAIL_MODE
from app.api.unsubscribe import generate_unsubscribe_token


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


def _escape_html(text: str) -> str:
    """Escape HTML special characters to prevent XSS."""
    if not text:
        return ''
    return (str(text)
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#x27;'))


def generate_digest_html(email: str, contents: list) -> str:
    """
    Generate HTML email content for a digest.

    Args:
        email: Recipient email address
        contents: List of Content model instances or dicts

    Returns:
        HTML string ready for email body
    """
    from app.config import PA_API_URL

    # Generate unsubscribe link
    token = generate_unsubscribe_token(email)
    base_url = PA_API_URL if PA_API_URL else 'https://signal.daedalusapps.com'
    unsubscribe_url = f"{base_url}/api/unsubscribe/{token}?email={email}"

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
             max-width: 600px; margin: 0 auto; padding: 20px; background: #f5f5f5;">
    <div style="background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <h1 style="color: #6366f1; margin: 0 0 10px 0;">
            DaedalusSignal Daily Digest
        </h1>
        <p style="color: #666; margin: 0 0 30px 0;">
            Your personalized AI content roundup
        </p>
"""

    for item in contents:
        # Handle both Content model instances and dicts
        if hasattr(item, 'to_dict'):
            item_dict = item.to_dict()
        elif hasattr(item, 'title'):
            item_dict = {
                'title': item.title,
                'url': item.url,
                'description': item.description,
                'relevance_score': item.relevance_score,
                'content_type': item.content_type
            }
        else:
            item_dict = item

        title = _escape_html(item_dict.get('title', 'Untitled'))
        url = _escape_html(item_dict.get('url', '#'))
        description = item_dict.get('description', '') or ''
        score = item_dict.get('relevance_score', 0)
        content_type = _escape_html(item_dict.get('content_type', 'article'))

        desc_preview = _escape_html(description[:200] + '...' if len(description) > 200 else description)

        html += f"""
        <div style="margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #6366f1;">
            <h3 style="margin: 0 0 10px 0;">
                <a href="{url}" style="color: #6366f1; text-decoration: none;">
                    {title}
                </a>
            </h3>
            <p style="color: #666; margin: 0 0 10px 0; font-size: 14px;">
                {desc_preview}
            </p>
            <div style="font-size: 12px; color: #999;">
                <span>Score: {score}</span> |
                <span>{content_type.upper()}</span>
            </div>
        </div>
"""

    html += f"""
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="color: #999; font-size: 12px; text-align: center;">
            <a href="{unsubscribe_url}" style="color: #999;">Unsubscribe</a> |
            <a href="https://signal.daedalusapps.com" style="color: #6366f1;">View Dashboard</a>
        </p>
    </div>
</body>
</html>
"""

    return html


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


def send_test_digest(email: str) -> bool:
    """Send a test digest email to verify email configuration."""
    from app.config import EMAIL_MODE, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
    
    # Create sample content for testing
    sample_digest = {
        'user': email,
        'content': [
            {
                'id': 0,
                'title': '🧪 Test Email - DaedalusSignal Digest',
                'content_type': 'test',
                'relevance_score': 100,
                'url': 'https://signal.daedalusapps.com',
                'description': 'This is a test email to verify your digest configuration is working correctly. '
                               'If you can see this, your email settings are configured properly!'
            },
            {
                'id': 1,
                'title': 'Sample Article: The Future of AI Agents',
                'content_type': 'article',
                'relevance_score': 85,
                'url': 'https://example.com/ai-agents',
                'description': 'This is what a typical digest item would look like with a description preview.'
            }
        ],
        'generated_at': datetime.utcnow().isoformat()
    }
    
    if EMAIL_MODE == 'console':
        print("\n" + "=" * 60)
        print(f"📧 TEST EMAIL for {email}")
        print("=" * 60)
        print("Email mode is 'console'. To send real emails, configure SMTP.")
        send_digest(sample_digest)
        return True
    
    elif EMAIL_MODE == 'smtp':
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Build email HTML
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #6366f1;">🔮 DaedalusSignal Daily Digest</h1>
            <p>Generated: {sample_digest['generated_at']}</p>
            <hr>
        """
        
        for item in sample_digest['content']:
            html_content += f"""
            <div style="margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                <h3 style="margin: 0 0 10px 0;">
                    <a href="{item['url']}" style="color: #6366f1;">{item['title']}</a>
                </h3>
                <p style="color: #666; margin: 0;">{item.get('description', '')}</p>
                <p style="color: #999; font-size: 12px;">Score: {item['relevance_score']}</p>
            </div>
            """
        
        html_content += """
            <hr>
            <p style="color: #999; font-size: 12px;">
                This is a test email from DaedalusSignal.
            </p>
        </body>
        </html>
        """
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = '🧪 DaedalusSignal Test Email'
            msg['From'] = SMTP_FROM
            msg['To'] = email
            
            msg.attach(MIMEText(html_content, 'html'))
            
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM, email, msg.as_string())
            
            print(f"Test email sent successfully to {email}")
            return True
            
        except Exception as e:
            print(f"SMTP Error: {e}")
            raise e
    
    return False
