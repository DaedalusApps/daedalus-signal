"""
Ingestion package - content scrapers
"""
from app.ingestion.youtube import YouTubeScraper
from app.ingestion.twitter import TwitterScraper
# Future features - LinkedIn and GitHub scrapers
# from app.ingestion.linkedin import LinkedInScraper
# from app.ingestion.github import GitHubScraper

__all__ = ['YouTubeScraper', 'TwitterScraper']


def get_scraper(source_type: str):
    """Get the appropriate scraper for a source type."""
    # Only YouTube and Twitter are currently supported
    # LinkedIn and GitHub are future features
    scrapers = {
        'youtube': YouTubeScraper,
        'twitter': TwitterScraper,
        # 'linkedin': LinkedInScraper,  # Coming soon
        # 'github': GitHubScraper,      # Coming soon
    }
    
    scraper_class = scrapers.get(source_type)
    if scraper_class:
        return scraper_class()
    return None
