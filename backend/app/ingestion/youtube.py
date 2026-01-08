"""
YouTube scraper - fetches public video information with transcript extraction
"""
import re
import json
from app.ingestion.base import BaseScraper

# Try to import transcript API, graceful fallback if not available
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
    TRANSCRIPT_AVAILABLE = True
except ImportError:
    TRANSCRIPT_AVAILABLE = False


class YouTubeScraper(BaseScraper):
    """Scraper for YouTube channels with transcript extraction."""
    
    # Limit to 5 videos per channel
    MAX_VIDEOS_PER_CHANNEL = 5
    
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
        
        # Limit to MAX_VIDEOS_PER_CHANNEL and fetch transcripts
        limited_results = results[:self.MAX_VIDEOS_PER_CHANNEL]
        
        # Fetch transcripts for each video
        for video in limited_results:
            video['transcript'] = self._fetch_transcript(video.get('url', ''))
        
        return limited_results
    
    def _fetch_transcript(self, video_url: str) -> str:
        """
        Fetch transcript for a YouTube video.
        Returns empty string if transcript is not available.
        """
        if not TRANSCRIPT_AVAILABLE:
            return ''
        
        try:
            # Extract video ID from URL
            video_id = self._extract_video_id(video_url)
            if not video_id:
                return ''
            
            # Try to get transcript (prefer English, fall back to auto-generated)
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                # Try to get manually created transcript first
                try:
                    transcript = transcript_list.find_manually_created_transcript(['en'])
                except:
                    # Fall back to auto-generated
                    try:
                        transcript = transcript_list.find_generated_transcript(['en'])
                    except:
                        # Try any available transcript
                        transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
                
                # Fetch and join transcript text
                transcript_data = transcript.fetch()
                full_text = ' '.join([entry['text'] for entry in transcript_data])
                
                # Limit transcript length to prevent huge storage
                max_chars = 10000
                if len(full_text) > max_chars:
                    full_text = full_text[:max_chars] + '...'
                
                return full_text
                
            except (TranscriptsDisabled, NoTranscriptFound):
                return ''
                
        except Exception as e:
            print(f"Transcript fetch error for {video_url}: {e}")
            return ''
    
    def _extract_video_id(self, url: str) -> str | None:
        """Extract video ID from YouTube URL."""
        if not url:
            return None
        
        # Handle various URL formats
        patterns = [
            r'watch\?v=([a-zA-Z0-9_-]{11})',
            r'youtu\.be/([a-zA-Z0-9_-]{11})',
            r'embed/([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
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
                'published_at': None,  # Would need additional parsing
                'transcript': ''  # Will be filled in later
            }
        except Exception:
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
                        'published_at': None,
                        'transcript': ''  # Will be filled in later
                    })
        
        # Deduplicate by URL
        seen = set()
        unique = []
        for v in videos:
            if v['url'] not in seen:
                seen.add(v['url'])
                unique.append(v)
        
        return unique
