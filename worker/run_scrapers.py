#!/usr/bin/env python3
"""
DreamHost Scraper Worker
Runs scrapers independently and POSTs results to PythonAnywhere
"""
import sys
import re
import time
import json
import random
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from config import SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX, USER_AGENT_ROTATE
from api_client import PAClient


class BaseScraper:
    """Base scraper class (standalone, no app.database dependency)."""

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
                    timeout=15
                )

                if response.status_code == 200:
                    return response.text
                elif response.status_code == 429:
                    wait_time = (attempt + 1) * 30
                    print(f"  Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                elif response.status_code >= 400:
                    print(f"  Error {response.status_code} for {url}")
                    return None

            except Exception as e:
                print(f"  Request failed (attempt {attempt + 1}): {e}")
                time.sleep((attempt + 1) * 5)

        return None

    def _parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content."""
        return BeautifulSoup(html, 'lxml')


class YouTubeScraper(BaseScraper):
    """YouTube channel scraper."""

    def scrape(self, url: str) -> list:
        """Scrape recent videos from a YouTube channel."""
        results = []

        # Normalize URL to get videos page
        if '/videos' not in url:
            videos_url = url.rstrip('/') + '/videos'
        else:
            videos_url = url

        html = self._fetch(videos_url)
        if not html:
            return results

        try:
            # YouTube embeds video data in a JSON object
            match = re.search(r'var ytInitialData = ({.*?});', html)
            if not match:
                match = re.search(r'ytInitialData\s*=\s*({.*?});', html)

            if match:
                data = json.loads(match.group(1))
                results = self._parse_videos(data)
            else:
                results = self._parse_html_fallback(html)

        except Exception as e:
            print(f"  YouTube scrape error: {e}")

        return results[:10]

    def _parse_videos(self, data: dict) -> list:
        """Parse videos from YouTube's JSON data."""
        videos = []

        try:
            tabs = data.get('contents', {}).get('twoColumnBrowseResultsRenderer', {}).get('tabs', [])

            for tab in tabs:
                tab_content = tab.get('tabRenderer', {}).get('content', {})
                section = tab_content.get('richGridRenderer', {})
                contents = section.get('contents', [])

                for item in contents:
                    renderer = item.get('richItemRenderer', {}).get('content', {}).get('videoRenderer', {})
                    if renderer:
                        video = self._extract_video_info(renderer)
                        if video:
                            videos.append(video)
        except Exception as e:
            print(f"  Parse error: {e}")

        return videos

    def _extract_video_info(self, renderer: dict) -> dict | None:
        """Extract video information from renderer."""
        try:
            video_id = renderer.get('videoId')
            if not video_id:
                return None

            title = renderer.get('title', {}).get('runs', [{}])[0].get('text', 'Unknown Title')
            description = renderer.get('descriptionSnippet', {}).get('runs', [{}])[0].get('text', '')

            return {
                'title': title,
                'description': description,
                'url': f'https://www.youtube.com/watch?v={video_id}',
                'content_type': 'video',
                'published_at': None
            }
        except Exception:
            return None

    def _parse_html_fallback(self, html: str) -> list:
        """Fallback HTML parsing when JSON extraction fails."""
        videos = []
        soup = self._parse_html(html)

        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/watch?v=' in href:
                video_id = href.split('v=')[1].split('&')[0]
                title = link.get('title') or link.get_text(strip=True) or f'Video {video_id}'

                if title and len(title) > 5:
                    videos.append({
                        'title': title,
                        'description': '',
                        'url': f'https://www.youtube.com/watch?v={video_id}',
                        'content_type': 'video',
                        'published_at': None
                    })

        # Deduplicate by URL
        seen = set()
        unique = []
        for v in videos:
            if v['url'] not in seen:
                seen.add(v['url'])
                unique.append(v)

        return unique


class TwitterScraper(BaseScraper):
    """Twitter/X scraper via Nitter mirrors."""

    NITTER_INSTANCES = [
        'nitter.net',
        'nitter.privacydev.net',
        'nitter.poast.org',
    ]

    def _get_username(self, url: str) -> str | None:
        """Extract username from Twitter URL or handle."""
        if url.startswith('@'):
            return url[1:]

        match = re.search(r'(?:twitter\.com|x\.com)/(\w+)', url)
        if match:
            return match.group(1)

        if re.match(r'^\w+$', url):
            return url

        return None

    def scrape(self, url: str) -> list:
        """Scrape recent tweets from a user via Nitter."""
        results = []
        username = self._get_username(url)

        if not username:
            print(f"  Could not extract username from: {url}")
            return results

        for instance in self.NITTER_INSTANCES:
            nitter_url = f'https://{instance}/{username}'
            html = self._fetch(nitter_url)

            if html:
                results = self._parse_tweets(html, username)
                if results:
                    break

        return results[:10]

    def _parse_tweets(self, html: str, username: str) -> list:
        """Parse tweets from Nitter HTML."""
        tweets = []
        soup = self._parse_html(html)

        timeline = soup.find_all('div', class_='timeline-item')

        for item in timeline:
            try:
                content_div = item.find('div', class_='tweet-content')
                if not content_div:
                    continue

                content = content_div.get_text(strip=True)
                if not content:
                    continue

                tweet_link = item.find('a', class_='tweet-link')
                tweet_url = f'https://twitter.com{tweet_link["href"]}' if tweet_link else None

                if not tweet_url:
                    links = item.find_all('a', href=True)
                    for link in links:
                        if f'/{username}/status/' in link['href']:
                            tweet_url = f'https://twitter.com{link["href"]}'
                            break

                if tweet_url:
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
                            except ValueError:
                                pass

                    tweets.append({
                        'title': content[:100] + '...' if len(content) > 100 else content,
                        'description': content,
                        'url': tweet_url,
                        'content_type': 'post',
                        'published_at': timestamp.isoformat() if timestamp else None
                    })

            except Exception as e:
                print(f"  Error parsing tweet: {e}")
                continue

        return tweets


class GitHubScraper(BaseScraper):
    """GitHub repository scraper."""

    def _extract_repo_info(self, url: str) -> tuple | None:
        """Extract owner/repo from GitHub URL."""
        match = re.search(r'github\.com/([^/]+)/([^/\?\#]+)', url)
        if match:
            return match.group(1), match.group(2)

        if '/' in url and 'github.com' not in url:
            parts = url.strip('/').split('/')
            if len(parts) >= 2:
                return parts[0], parts[1]

        return None

    def scrape(self, url: str) -> list:
        """Scrape recent activity from a GitHub repository."""
        results = []

        repo_info = self._extract_repo_info(url)
        if not repo_info:
            print(f"  Could not parse GitHub URL: {url}")
            return results

        owner, repo = repo_info

        releases = self._fetch_releases(owner, repo)
        results.extend(releases)

        commits = self._fetch_commits(owner, repo)
        results.extend(commits)

        return results[:10]

    def _fetch_releases(self, owner: str, repo: str) -> list:
        """Fetch recent releases from the repo."""
        releases = []
        url = f'https://github.com/{owner}/{repo}/releases'

        html = self._fetch(url)
        if not html:
            return releases

        soup = self._parse_html(html)
        release_entries = soup.find_all('div', class_=re.compile('Box-row'))[:5]

        for entry in release_entries:
            try:
                title_link = entry.find('a', class_=re.compile('Link--primary'))
                if not title_link:
                    continue

                title = title_link.get_text(strip=True)
                href = title_link.get('href', '')
                release_url = f'https://github.com{href}' if href.startswith('/') else href

                desc_elem = entry.find('div', class_=re.compile('markdown-body'))
                description = desc_elem.get_text(strip=True)[:500] if desc_elem else ''

                time_elem = entry.find('relative-time')
                published_at = None
                if time_elem and time_elem.get('datetime'):
                    published_at = time_elem['datetime']

                releases.append({
                    'title': f'[Release] {owner}/{repo}: {title}',
                    'description': description,
                    'url': release_url,
                    'content_type': 'repo',
                    'published_at': published_at
                })

            except Exception as e:
                print(f"  Error parsing release: {e}")
                continue

        return releases

    def _fetch_commits(self, owner: str, repo: str) -> list:
        """Fetch recent commits from the repo."""
        commits = []
        url = f'https://github.com/{owner}/{repo}/commits'

        html = self._fetch(url)
        if not html:
            return commits

        soup = self._parse_html(html)
        commit_links = soup.find_all('a', class_=re.compile('Link--primary'))[:5]

        for link in commit_links:
            try:
                href = link.get('href', '')
                if '/commit/' not in href:
                    continue

                message = link.get_text(strip=True)
                commit_url = f'https://github.com{href}' if href.startswith('/') else href

                commits.append({
                    'title': f'[Commit] {owner}/{repo}: {message[:80]}',
                    'description': message,
                    'url': commit_url,
                    'content_type': 'repo',
                    'published_at': None
                })

            except Exception as e:
                print(f"  Error parsing commit: {e}")
                continue

        return commits


# Map source types to scraper classes
SCRAPERS = {
    'youtube': YouTubeScraper,
    'twitter': TwitterScraper,
    'github': GitHubScraper,
}


def run_all_scrapers():
    """Main entry point - fetch sources, scrape, submit to PA."""
    print(f"\n[{datetime.now()}] Starting DreamHost scraper worker...")

    client = PAClient()

    try:
        sources = client.get_sources()
        print(f"  Fetched {len(sources)} sources from PythonAnywhere")
    except Exception as e:
        print(f"  ERROR fetching sources: {e}")
        sys.exit(1)

    for source in sources:
        source_type = source['source_type']
        scraper_class = SCRAPERS.get(source_type)

        if not scraper_class:
            print(f"  Skipping {source['name']}: no scraper for {source_type}")
            continue

        print(f"  Scraping: {source['name']} ({source_type})")

        try:
            scraper = scraper_class()
            content = scraper.scrape(source['url'])
            print(f"    Found {len(content)} items")

            if content:
                result = client.submit_content(source['id'], content)
                print(f"    Submitted: {result.get('added', 0)} added, {result.get('skipped', 0)} skipped")

        except Exception as e:
            print(f"    ERROR: {e}")

    print(f"[{datetime.now()}] Scraper worker complete\n")


if __name__ == '__main__':
    run_all_scrapers()
