"""
Seed the database with default sources, tags, and admin user from the PRD
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bcrypt
from app.database import init_db, get_session, close_session
from app.models import Source, Tag, User
from app.config import ADMIN_EMAIL, ADMIN_PASSWORD


def seed_admin_user():
    """Create admin user from environment variables."""
    db = get_session()
    try:
        existing = db.query(User).filter_by(email=ADMIN_EMAIL).first()
        if not existing:
            password_hash = bcrypt.hashpw(
                ADMIN_PASSWORD.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            
            admin = User(
                email=ADMIN_EMAIL,
                password_hash=password_hash,
                is_admin=True,
                is_active=True,
                onboarding_complete=True
            )
            db.add(admin)
            db.commit()
            print(f"  Created admin user: {ADMIN_EMAIL}")
        else:
            print(f"  Admin user already exists: {ADMIN_EMAIL}")
    finally:
        close_session(db)


def seed_default_sources():
    """Seed default sources from defaults.md."""
    sources = [
        # X (Twitter) - ordered by external influence (from defaults.md)
        {'name': '@karpathy', 'url': 'https://x.com/karpathy', 'source_type': 'twitter'},
        {'name': '@AnthropicAI', 'url': 'https://x.com/AnthropicAI', 'source_type': 'twitter'},
        {'name': '@MistralAI', 'url': 'https://x.com/MistralAI', 'source_type': 'twitter'},
        {'name': '@cursor_ai', 'url': 'https://x.com/cursor_ai', 'source_type': 'twitter'},
        {'name': '@Steve_Yegge', 'url': 'https://x.com/Steve_Yegge', 'source_type': 'twitter'},
        {'name': '@emollick', 'url': 'https://x.com/emollick', 'source_type': 'twitter'},
        {'name': '@bcherny', 'url': 'https://x.com/bcherny', 'source_type': 'twitter'},
        {'name': '@langchain_oss', 'url': 'https://x.com/LangChainAI', 'source_type': 'twitter'},
        {'name': '@GroqInc', 'url': 'https://x.com/GroqInc', 'source_type': 'twitter'},
        {'name': '@manusai', 'url': 'https://x.com/manaboroshii', 'source_type': 'twitter'},
        
        # YouTube
        {'name': 'Two Minute Papers', 'url': 'https://www.youtube.com/@TwoMinutePapers', 'source_type': 'youtube'},
        {'name': 'Yannic Kilcher', 'url': 'https://www.youtube.com/@YannicKilcher', 'source_type': 'youtube'},
        {'name': 'AI Explained', 'url': 'https://www.youtube.com/@aiexplained-official', 'source_type': 'youtube'},
        {'name': 'Lex Fridman', 'url': 'https://www.youtube.com/@lexfridman', 'source_type': 'youtube'},
        {'name': 'Computerphile', 'url': 'https://www.youtube.com/@Computerphile', 'source_type': 'youtube'},
        
        # GitHub and LinkedIn - Future features (disabled in UI)
    ]
    
    db = get_session()
    try:
        for src in sources:
            existing = db.query(Source).filter_by(url=src['url']).first()
            if not existing:
                source = Source(
                    name=src['name'],
                    url=src['url'],
                    source_type=src['source_type'],
                    is_default=True,
                    is_approved=True
                )
                db.add(source)
                print(f"  Added source: {src['name']}")
        
        db.commit()
    finally:
        close_session(db)


def seed_default_tags():
    """Seed default tags from defaults.md - ordered by external popularity."""
    tags = [
        # Ordered by external popularity (from defaults.md)
        {'name': 'AI', 'category': 'general'},
        {'name': 'ArtificialIntelligence', 'category': 'general'},
        {'name': 'MachineLearning', 'category': 'general'},
        {'name': 'DeepLearning', 'category': 'general'},
        {'name': 'Tech', 'category': 'general'},
        {'name': 'DataScience', 'category': 'general'},
        {'name': 'Robotics', 'category': 'general'},
        {'name': 'Coding', 'category': 'tools'},
        {'name': 'Python', 'category': 'tools'},
        {'name': 'Innovation', 'category': 'general'},
        {'name': 'Startup', 'category': 'general'},
        {'name': 'BigData', 'category': 'general'},
        {'name': 'CloudComputing', 'category': 'tools'},
        {'name': 'Programming', 'category': 'tools'},
        {'name': 'Developer', 'category': 'tools'},
        {'name': 'Analytics', 'category': 'general'},
        {'name': 'DigitalTransformation', 'category': 'general'},
        {'name': 'Automation', 'category': 'tools'},
        {'name': 'Computerscience', 'category': 'general'},
        {'name': 'Blockchain', 'category': 'general'},
        {'name': 'IoT', 'category': 'general'},
    ]
    
    db = get_session()
    try:
        for t in tags:
            existing = db.query(Tag).filter_by(name=t['name']).first()
            if not existing:
                tag = Tag(
                    name=t['name'],
                    category=t['category'],
                    is_default=True
                )
                db.add(tag)
                print(f"  Added tag: {t['name']}")
        
        db.commit()
    finally:
        close_session(db)


def main():
    """Run the seeder."""
    print("Initializing database...")
    init_db()
    
    print("\nSeeding admin user...")
    seed_admin_user()
    
    print("\nSeeding default sources...")
    seed_default_sources()
    
    print("\nSeeding default tags...")
    seed_default_tags()
    
    print("\nDatabase seeded successfully!")


if __name__ == '__main__':
    main()
