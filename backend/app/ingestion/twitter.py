"""
Twitter/X scraper - fetches public profile content via Nitter
Note: Direct Twitter scraping is blocked, so we use Nitter instances
"""
import re
from datetime import datetime
from app.ingestion.base import BaseScraper


class TwitterScraper(BaseScraper):
    """Scraper for Twitter/X accounts via Nitter mirrors."""
    
    # List of Nitter instances to try
    NITTER_INSTANCES = [
        'nitter.net',
        'nitter.privacydev.net',
        'nitter.poast.org',
    ]
    
    def get_source_type(self) -> str:
        return 'twitter'
    
    def _get_username(self, url: str) -> str | None:
        """Extract username from Twitter URL or handle."""
        # Handle @username format
        if url.startswith('@'):
            return url[1:]
        
        # Handle twitter.com/username or x.com/username
        match = re.search(r'(?:twitter\.com|x\.com)/(\w+)', url)
        if match:
            return match.group(1)
        
        # Assume it's just a username
        if re.match(r'^\w+$', url):
            return url
        
        return None
    
    def scrape(self, source_url: str) -> list[dict]:
        """Scrape recent tweets from a user via Nitter."""
        results = []
        username = self._get_username(source_url)
        
        if not username:
            print(f"Could not extract username from: {source_url}")
            return results
        
        # Try each Nitter instance
        for instance in self.NITTER_INSTANCES:
            nitter_url = f'https://{instance}/{username}'
            html = self._fetch(nitter_url)
            
            if html:
                results = self._parse_tweets(html, username)
                if results:
                    break
        
        return results[:10]
    
    def _parse_tweets(self, html: str, username: str) -> list[dict]:
        """Parse tweets from Nitter HTML."""
        tweets = []
        soup = self._parse_html(html)
        
        # Find tweet containers (Nitter structure)
        timeline = soup.find_all('div', class_='timeline-item')
        
        for item in timeline:
            try:
                # Get tweet content
                content_div = item.find('div', class_='tweet-content')
                if not content_div:
                    continue
                
                content = content_div.get_text(strip=True)
                if not content:
                    continue
                
                # Get tweet link
                tweet_link = item.find('a', class_='tweet-link')
                tweet_url = f'https://twitter.com{tweet_link["href"]}' if tweet_link else None
                
                if not tweet_url:
                    # Try to find any link to the tweet
                    links = item.find_all('a', href=True)
                    for link in links:
                        if f'/{username}/status/' in link['href']:
                            tweet_url = f'https://twitter.com{link["href"]}'
                            break
                
                if tweet_url:
                    # Get timestamp
                    time_elem = item.find('span', class_='tweet-date')
                    timestamp = None
                    if time_elem:
                        time_link = time_elem.find('a')
                        if time_link and time_link.get('title'):
                            try:
                                timestamp = datetime.strptime(
                                    time_link['title'],
                                    '%b %d, %Y · %I:%M %p %Z'
                                )
                            except:
                                pass
                    
                    tweets.append({
                        'title': content[:100] + '...' if len(content) > 100 else content,
                        'description': content,
                        'url': tweet_url,
                        'content_type': 'post',
                        'published_at': timestamp
                    })
                    
            except Exception as e:
                print(f"Error parsing tweet: {e}")
                continue
        
        return tweets
