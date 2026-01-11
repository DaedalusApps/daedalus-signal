"""
HTTP client for communicating with DreamHost PHP API
"""
import hmac
import hashlib
import time
import json
import requests
from config import API_URL, SECRET_KEY


class APIClient:
    """Client for DreamHost PHP API with HMAC authentication."""

    def __init__(self):
        self.base_url = API_URL.rstrip('/')
        self.session = requests.Session()

    def _sign_request(self) -> dict:
        """Generate authentication headers for a request.
        
        PHP API expects X-Worker-Signature in format: "timestamp:signature"
        where signature = HMAC-SHA256(timestamp, SECRET_KEY)
        """
        timestamp = str(int(time.time()))
        signature = hmac.new(
            SECRET_KEY.encode(),
            timestamp.encode(),
            hashlib.sha256
        ).hexdigest()

        return {
            'X-Worker-Signature': f'{timestamp}:{signature}',
            'Content-Type': 'application/json'
        }

    def get_sources(self) -> list:
        """Fetch all sources to scrape."""
        headers = self._sign_request()
        response = self.session.get(
            f"{self.base_url}/worker/sources",
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json().get('sources', [])

    def submit_content(self, source_id: int, content: list) -> dict:
        """Submit scraped content for ingestion."""
        body = json.dumps({
            'source_id': source_id,
            'content': content
        })
        headers = self._sign_request()

        response = self.session.post(
            f"{self.base_url}/worker/ingest",
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
            f"{self.base_url}/worker/digests",
            headers=headers,
            timeout=60
        )
        response.raise_for_status()
        return response.json().get('digests', [])

    def mark_digest_sent(self, email: str, content_ids: list) -> dict:
        """Notify API that a digest was sent."""
        body = json.dumps({
            'email': email,
            'content_ids': content_ids
        })
        headers = self._sign_request()

        response = self.session.post(
            f"{self.base_url}/worker/digest-sent",
            headers=headers,
            data=body,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
