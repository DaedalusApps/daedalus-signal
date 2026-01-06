"""
GitHub scraper - fetches public repository activity
"""
import re
from datetime import datetime
from app.ingestion.base import BaseScraper


class GitHubScraper(BaseScraper):
    """Scraper for GitHub repositories."""
    
    def get_source_type(self) -> str:
        return 'github'
    
    def scrape(self, source_url: str) -> list[dict]:
        """
        Scrape recent activity from a GitHub repository.
        Fetches releases, commits, and issues.
        """
        results = []
        
        # Extract owner/repo from URL
        repo_info = self._extract_repo_info(source_url)
        if not repo_info:
            print(f"Could not parse GitHub URL: {source_url}")
            return results
        
        owner, repo = repo_info
        
        # Fetch releases
        releases = self._fetch_releases(owner, repo)
        results.extend(releases)
        
        # Fetch recent commits
        commits = self._fetch_commits(owner, repo)
        results.extend(commits)
        
        return results[:10]
    
    def _extract_repo_info(self, url: str) -> tuple[str, str] | None:
        """Extract owner/repo from GitHub URL."""
        # Handle github.com/owner/repo format
        match = re.search(r'github\.com/([^/]+)/([^/\?\#]+)', url)
        if match:
            return match.group(1), match.group(2)
        
        # Handle owner/repo format
        if '/' in url and 'github.com' not in url:
            parts = url.strip('/').split('/')
            if len(parts) >= 2:
                return parts[0], parts[1]
        
        return None
    
    def _fetch_releases(self, owner: str, repo: str) -> list[dict]:
        """Fetch recent releases from the repo."""
        releases = []
        url = f'https://github.com/{owner}/{repo}/releases'
        
        html = self._fetch(url)
        if not html:
            return releases
        
        soup = self._parse_html(html)
        
        # Find release entries
        release_entries = soup.find_all('div', class_=re.compile('Box-row'))[:5]
        
        for entry in release_entries:
            try:
                # Get release title/tag
                title_link = entry.find('a', class_=re.compile('Link--primary'))
                if not title_link:
                    continue
                
                title = title_link.get_text(strip=True)
                href = title_link.get('href', '')
                release_url = f'https://github.com{href}' if href.startswith('/') else href
                
                # Get release description
                desc_elem = entry.find('div', class_=re.compile('markdown-body'))
                description = desc_elem.get_text(strip=True)[:500] if desc_elem else ''
                
                # Get date
                time_elem = entry.find('relative-time')
                published_at = None
                if time_elem and time_elem.get('datetime'):
                    try:
                        published_at = datetime.fromisoformat(
                            time_elem['datetime'].replace('Z', '+00:00')
                        )
                    except:
                        pass
                
                releases.append({
                    'title': f'[Release] {owner}/{repo}: {title}',
                    'description': description,
                    'url': release_url,
                    'content_type': 'repo',
                    'published_at': published_at
                })
                
            except Exception as e:
                print(f"Error parsing release: {e}")
                continue
        
        return releases
    
    def _fetch_commits(self, owner: str, repo: str) -> list[dict]:
        """Fetch recent commits from the repo."""
        commits = []
        url = f'https://github.com/{owner}/{repo}/commits'
        
        html = self._fetch(url)
        if not html:
            return commits
        
        soup = self._parse_html(html)
        
        # Find commit entries
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
                print(f"Error parsing commit: {e}")
                continue
        
        return commits
