"""
Base scraper with rate limiting and anti-ban measures
"""
import time
import random
import requests
from abc import ABC, abstractmethod
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from app.config import SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX, USER_AGENT_ROTATE


class BaseScraper(ABC):
    """Base class for all scrapers with rate limiting."""
    
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.last_request_time = 0
    
    def _get_headers(self):
        """Get headers with rotating user agent."""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        if USER_AGENT_ROTATE:
            headers['User-Agent'] = self.ua.random
        else:
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        return headers
    
    def _rate_limit(self):
        """Apply rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        delay = random.uniform(SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX)
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self.last_request_time = time.time()
    
    def _fetch(self, url: str, retries: int = 3) -> str | None:
        """Fetch a URL with rate limiting and retries."""
        self._rate_limit()
        
        for attempt in range(retries):
            try:
                response = self.session.get(
                    url,
                    headers=self._get_headers(),
                    timeout=10
                )
                
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 429:  # Rate limited
                    wait_time = (attempt + 1) * 30
                    print(f"Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                elif response.status_code >= 400:
                    print(f"Error {response.status_code} for {url}")
                    return None
                    
            except Exception as e:
                print(f"Request failed (attempt {attempt + 1}): {e}")
                time.sleep((attempt + 1) * 5)
        
        return None
    
    def _parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content."""
        return BeautifulSoup(html, 'lxml')
    
    @abstractmethod
    def scrape(self, source_url: str) -> list[dict]:
        """Scrape content from the source. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def get_source_type(self) -> str:
        """Return the source type identifier."""
        pass
