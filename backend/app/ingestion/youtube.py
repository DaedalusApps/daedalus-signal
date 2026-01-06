"""
YouTube scraper - fetches public video information
"""
import re
import json
from datetime import datetime
from app.ingestion.base import BaseScraper


class YouTubeScraper(BaseScraper):
    """Scraper for YouTube channels."""
    
    def get_source_type(self) -> str:
        return 'youtube'
    
    def scrape(self, source_url: str) -> list[dict]:
        """
        Scrape recent videos from a YouTube channel.
        Supports channel URLs like:
        - https://www.youtube.com/@ChannelName
        - https://www.youtube.com/channel/CHANNEL_ID
        - https://www.youtube.com/c/ChannelName
        """
        results = []
        
        # Normalize URL to get videos page
        if '/videos' not in source_url:
            videos_url = source_url.rstrip('/') + '/videos'
        else:
            videos_url = source_url
        
        html = self._fetch(videos_url)
        if not html:
            return results
        
        try:
            # YouTube embeds video data in a JSON object
            # Look for ytInitialData
            match = re.search(r'var ytInitialData = ({.*?});', html)
            if not match:
                # Try alternative pattern
                match = re.search(r'ytInitialData\s*=\s*({.*?});', html)
            
            if match:
                data = json.loads(match.group(1))
                results = self._parse_videos(data)
            else:
                # Fallback to HTML parsing
                results = self._parse_html_fallback(html)
                
        except Exception as e:
            print(f"YouTube scrape error: {e}")
        
        return results[:10]  # Limit to 10 latest videos
    
    def _parse_videos(self, data: dict) -> list[dict]:
        """Parse videos from YouTube's JSON data."""
        videos = []
        
        try:
            # Navigate the nested structure
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
            print(f"Parse error: {e}")
        
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
                'published_at': None  # Would need additional parsing
            }
        except:
            return None
    
    def _parse_html_fallback(self, html: str) -> list[dict]:
        """Fallback HTML parsing when JSON extraction fails."""
        videos = []
        soup = self._parse_html(html)
        
        # Look for video links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/watch?v=' in href:
                video_id = href.split('v=')[1].split('&')[0]
                title = link.get('title') or link.get_text(strip=True) or f'Video {video_id}'
                
                if title and len(title) > 5:  # Filter out empty/short titles
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
