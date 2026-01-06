"""
Seed the database with default sources and tags from the PRD
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, get_session, close_session
from app.models import Source, Tag


def seed_default_sources():
    """Seed default sources from PRD."""
    sources = [
        # X (Twitter)
        {'name': '@OpenAI', 'url': 'https://twitter.com/OpenAI', 'source_type': 'twitter'},
        {'name': '@AndrewYNg', 'url': 'https://twitter.com/AndrewYNg', 'source_type': 'twitter'},
        {'name': '@ylecun', 'url': 'https://twitter.com/ylecun', 'source_type': 'twitter'},
        {'name': '@karpathy', 'url': 'https://twitter.com/karpathy', 'source_type': 'twitter'},
        {'name': '@huggingface', 'url': 'https://twitter.com/huggingface', 'source_type': 'twitter'},
        
        # GitHub
        {'name': 'openai/gym', 'url': 'https://github.com/openai/gym', 'source_type': 'github'},
        {'name': 'huggingface/transformers', 'url': 'https://github.com/huggingface/transformers', 'source_type': 'github'},
        {'name': 'deepmind/lab', 'url': 'https://github.com/deepmind/lab', 'source_type': 'github'},
        {'name': 'langchain-ai/langchain', 'url': 'https://github.com/langchain-ai/langchain', 'source_type': 'github'},
        {'name': 'microsoft/semantic-kernel', 'url': 'https://github.com/microsoft/semantic-kernel', 'source_type': 'github'},
        
        # YouTube
        {'name': 'Two Minute Papers', 'url': 'https://www.youtube.com/@TwoMinutePapers', 'source_type': 'youtube'},
        {'name': 'Yannic Kilcher', 'url': 'https://www.youtube.com/@YannicKilcher', 'source_type': 'youtube'},
        {'name': 'AI Explained', 'url': 'https://www.youtube.com/@aiexplained-official', 'source_type': 'youtube'},
        {'name': 'Lex Fridman', 'url': 'https://www.youtube.com/@lexfridman', 'source_type': 'youtube'},
        {'name': 'Computerphile', 'url': 'https://www.youtube.com/@Computerphile', 'source_type': 'youtube'},
        
        # LinkedIn (will use simulated data)
        {'name': 'Yann LeCun', 'url': 'https://www.linkedin.com/in/yann-lecun', 'source_type': 'linkedin'},
        {'name': 'Fei-Fei Li', 'url': 'https://www.linkedin.com/in/faboratory', 'source_type': 'linkedin'},
        {'name': 'Andrej Karpathy', 'url': 'https://www.linkedin.com/in/andrej-karpathy', 'source_type': 'linkedin'},
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
    """Seed default tags from PRD."""
    tags = [
        # General AI
        {'name': 'ai', 'category': 'general'},
        {'name': 'machine learning', 'category': 'general'},
        {'name': 'deep learning', 'category': 'general'},
        {'name': 'neural networks', 'category': 'general'},
        {'name': 'llm', 'category': 'general'},
        
        # Agentic/Context
        {'name': 'agentic systems', 'category': 'agentic'},
        {'name': 'context engineering', 'category': 'agentic'},
        {'name': 'prompt engineering', 'category': 'agentic'},
        {'name': 'autonomous agents', 'category': 'agentic'},
        {'name': 'ai agents', 'category': 'agentic'},
        
        # Tools/Frameworks
        {'name': 'transformers', 'category': 'tools'},
        {'name': 'langchain', 'category': 'tools'},
        {'name': 'openai', 'category': 'tools'},
        {'name': 'reinforcement learning', 'category': 'tools'},
        {'name': 'workflow automation', 'category': 'tools'},
        
        # Research
        {'name': 'ai research', 'category': 'research'},
        {'name': 'frontier ai', 'category': 'research'},
        {'name': 'explainable ai', 'category': 'research'},
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
    
    print("\nSeeding default sources...")
    seed_default_sources()
    
    print("\nSeeding default tags...")
    seed_default_tags()
    
    print("\n✓ Database seeded successfully!")


if __name__ == '__main__':
    main()
