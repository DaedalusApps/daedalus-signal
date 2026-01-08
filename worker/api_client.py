"""
HTTP client for communicating with PythonAnywhere API
"""
import hmac
import hashlib
import time
import json
import requests
from config import PA_API_URL, WORKER_SECRET


class PAClient:
    """Client for PythonAnywhere API with HMAC authentication."""

    def __init__(self):
        self.base_url = PA_API_URL.rstrip('/')
        self.session = requests.Session()

    def _sign_request(self, body: str = '') -> dict:
        """Generate authentication headers for a request."""
        timestamp = str(int(time.time()))
        message = f"{timestamp}:{body}"
        signature = hmac.new(
            WORKER_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return {
            'X-Worker-Signature': signature,
            'X-Worker-Timestamp': timestamp,
            'Content-Type': 'application/json'
        }

    def get_sources(self) -> list:
        """Fetch all sources to scrape."""
        headers = self._sign_request()
        response = self.session.get(
            f"{self.base_url}/api/worker/sources",
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json().get('sources', [])

    def submit_content(self, source_id: int, content: list) -> dict:
        """Submit scraped content to PA for ingestion."""
        body = json.dumps({
            'source_id': source_id,
            'content': content
        })
        headers = self._sign_request(body)

        response = self.session.post(
            f"{self.base_url}/api/worker/ingest",
            headers=headers,
            data=body,
            timeout=60
        )
        response.raise_for_status()
        return response.json()

    def get_digests(self) -> list:
        """Fetch digest payloads for all users."""
        headers = self._sign_request()
        response = self.session.get(
            f"{self.base_url}/api/worker/digests",
            headers=headers,
            timeout=60
        )
        response.raise_for_status()
        return response.json().get('digests', [])

    def mark_digest_sent(self, email: str, content_ids: list) -> dict:
        """Notify PA that a digest was sent."""
        body = json.dumps({
            'email': email,
            'content_ids': content_ids
        })
        headers = self._sign_request(body)

        response = self.session.post(
            f"{self.base_url}/api/worker/digest-sent",
            headers=headers,
            data=body,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
