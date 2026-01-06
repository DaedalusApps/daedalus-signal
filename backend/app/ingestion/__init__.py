"""
Ingestion package - content scrapers
"""
from app.ingestion.youtube import YouTubeScraper
from app.ingestion.twitter import TwitterScraper
from app.ingestion.linkedin import LinkedInScraper
from app.ingestion.github import GitHubScraper

__all__ = ['YouTubeScraper', 'TwitterScraper', 'LinkedInScraper', 'GitHubScraper']


def get_scraper(source_type: str):
    """Get the appropriate scraper for a source type."""
    scrapers = {
        'youtube': YouTubeScraper,
        'twitter': TwitterScraper,
        'linkedin': LinkedInScraper,
        'github': GitHubScraper,
    }
    
    scraper_class = scrapers.get(source_type)
    if scraper_class:
        return scraper_class()
    return None
