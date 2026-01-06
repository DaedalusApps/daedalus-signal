"""
Scheduler for content ingestion and digest delivery
"""
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from app.database import get_session, close_session
from app.models import Source, Content
from app.ingestion import get_scraper
from app.filtering import KeywordFilter
from app.email import run_daily_digest


def scrape_all_sources():
    """Scrape content from all sources."""
    print(f"\n[{datetime.now()}] Starting content ingestion...")
    
    db = get_session()
    try:
        sources = db.query(Source).all()
        filter_engine = KeywordFilter()
        
        for source in sources:
            print(f"  Scraping: {source.name} ({source.source_type})")
            
            scraper = get_scraper(source.source_type)
            if not scraper:
                print(f"    No scraper for type: {source.source_type}")
                continue
            
            try:
                raw_content = scraper.scrape(source.url)
                print(f"    Found {len(raw_content)} items")
                
                # Filter and score content
                filtered = filter_engine.filter_content(raw_content)
                print(f"    {len(filtered)} items passed filtering")
                
                # Save to database
                for item in filtered:
                    # Check if content already exists
                    existing = db.query(Content).filter_by(url=item['url']).first()
                    if existing:
                        continue
                    
                    content = Content(
                        title=item['title'][:500],
                        description=item.get('description', '')[:2000],
                        url=item['url'],
                        content_type=item['content_type'],
                        source_id=source.id,
                        relevance_score=item.get('relevance_score', 0),
                        published_at=item.get('published_at')
                    )
                    db.add(content)
                
                # Update last scraped time
                source.last_scraped = datetime.utcnow()
                
            except Exception as e:
                print(f"    Error: {e}")
        
        db.commit()
        print(f"[{datetime.now()}] Ingestion complete!\n")
        
    except Exception as e:
        print(f"Ingestion error: {e}")
        db.rollback()
    finally:
        close_session(db)


def create_scheduler():
    """Create and configure the background scheduler."""
    scheduler = BackgroundScheduler()
    
    # Run ingestion every 6 hours
    scheduler.add_job(
        scrape_all_sources,
        'interval',
        hours=6,
        id='scrape_sources',
        name='Scrape all sources'
    )
    
    # Run daily digest at 8 AM
    scheduler.add_job(
        run_daily_digest,
        'cron',
        hour=8,
        id='daily_digest',
        name='Send daily digest'
    )
    
    return scheduler


if __name__ == '__main__':
    # Run manual scrape
    scrape_all_sources()
