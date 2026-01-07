"""
LinkedIn scraper - limited public profile scraping
Note: LinkedIn heavily restricts scraping, so this provides simulated data
for development/testing. In production, consider using their API.
"""
import re
from datetime import datetime, timedelta
import random
from app.ingestion.base import BaseScraper


class LinkedInScraper(BaseScraper):
    """
    Scraper for LinkedIn profiles.
    
    WARNING: LinkedIn actively blocks scraping. This scraper provides
    simulated data for development. For production use, you would need
    to use LinkedIn's official API with proper authentication.
    """
    
    def get_source_type(self) -> str:
        return 'linkedin'
    
    def scrape(self, source_url: str) -> list[dict]:
        """
        Attempt to scrape LinkedIn profile posts.
        Falls back to simulated data if blocked.
        """
        results = []
        
        # Extract profile name from URL
        profile_name = self._extract_profile_name(source_url)
        
        # Try to fetch the profile page
        html = self._fetch(source_url)
        
        if html and 'authwall' not in html.lower():
            # If we got actual content, try to parse it
            results = self._parse_posts(html, profile_name, source_url)
        
        # If no results (likely blocked), return simulated data for dev purposes
        if not results:
            print(f"LinkedIn blocked or no posts found. Using dev mode for: {profile_name}")
            results = self._generate_dev_data(profile_name)
        
        return results[:10]
    
    def _extract_profile_name(self, url: str) -> str:
        """Extract profile name from LinkedIn URL."""
        # Handle various LinkedIn URL formats
        patterns = [
            r'linkedin\.com/in/([^/\?]+)',
            r'linkedin\.com/company/([^/\?]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1).replace('-', ' ').title()
        
        return 'Unknown Profile'
    
    def _parse_posts(self, html: str, profile_name: str, source_url: str) -> list[dict]:
        """Parse posts from LinkedIn HTML (if accessible)."""
        posts = []
        soup = self._parse_html(html)
        
        # LinkedIn's structure is complex and obfuscated
        # This is a best-effort parser
        post_containers = soup.find_all('div', class_=re.compile('feed-shared-update'))
        
        for container in post_containers:
            try:
                text_elem = container.find('span', class_=re.compile('break-words'))
                if text_elem:
                    content = text_elem.get_text(strip=True)
                    if content:
                        posts.append({
                            'title': f"{profile_name}: {content[:80]}...",
                            'description': content,
                            'url': source_url,
                            'content_type': 'post',
                            'published_at': None
                        })
            except Exception:
                continue
        
        return posts
    
    def _generate_dev_data(self, profile_name: str) -> list[dict]:
        """Generate simulated posts for development/testing."""
        topics = [
            "Excited to share thoughts on the future of AI agents",
            "Context engineering is transforming how we build LLM applications",
            "New research on agentic systems architecture",
            "Exploring frontier AI tooling for enterprise workflows",
            "Thoughts on prompt engineering best practices",
            "The role of autonomous agents in software development",
            "Building more reliable AI systems with better context",
            "Lessons learned from deploying LLM-powered applications",
        ]
        
        posts = []
        for i, topic in enumerate(random.sample(topics, min(5, len(topics)))):
            posts.append({
                'title': f"{profile_name}: {topic}",
                'description': f"{topic}. This is simulated content for development purposes. "
                              f"In production, this would be actual LinkedIn post content.",
                'url': f'https://linkedin.com/posts/{profile_name.lower().replace(" ", "-")}-{i}',
                'content_type': 'post',
                'published_at': datetime.utcnow() - timedelta(days=i)
            })
        
        return posts
