"""Fellow.app API client service."""
import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx

from src.lib.logger import get_logger
from src.lib.rate_limiter import RateLimiter
from src.models import Note

logger = get_logger(__name__)


class FellowAPIClient:
    """Client for interacting with Fellow.app API."""
    
    def __init__(self, rate_limit: float = 10.0):
        """
        Initialize API client.
        
        Args:
            rate_limit: Requests per second (default: 10)
        """
        self.api_token = os.getenv('FELLOW_API_TOKEN', '')
        subdomain = os.getenv('FELLOW_SUBDOMAIN', '')
        
        if not self.api_token:
            raise ValueError("FELLOW_API_TOKEN environment variable is required")
        
        if not subdomain:
            raise ValueError("FELLOW_SUBDOMAIN environment variable is required")
        
        self.base_url = f'https://{subdomain}.fellow.app'
        
        self.headers = {
            'X-API-KEY': self.api_token,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        self.rate_limiter = RateLimiter(requests_per_second=rate_limit)
        self.client = httpx.Client(timeout=60.0)
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request with rate limiting and logging.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for httpx request
            
        Returns:
            Response JSON data
        """
        self.rate_limiter.acquire()
        
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            response = self.client.request(method, url, headers=self.headers, **kwargs)
            elapsed = time.time() - start_time
            
            logger.info(
                "api_request",
                method=method,
                endpoint=endpoint,
                status_code=response.status_code,
                response_time=round(elapsed, 3)
            )
            
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 30))
                logger.warning("rate_limit_exceeded", retry_after=retry_after)
                time.sleep(retry_after)
                return self._make_request(method, endpoint, **kwargs)
            
            elif response.status_code >= 500:
                logger.error("server_error", status_code=response.status_code)
                raise httpx.HTTPStatusError(
                    f"Server error: {response.status_code}",
                    request=response.request,
                    response=response
                )
            
            elif response.status_code == 401:
                logger.error("authentication_failed")
                raise httpx.HTTPStatusError(
                    "Authentication failed - check API token",
                    request=response.request,
                    response=response
                )
            
            response.raise_for_status()
            return response.json()
            
        except httpx.TimeoutException as e:
            elapsed = time.time() - start_time
            logger.error("api_request_timeout", endpoint=endpoint, elapsed=elapsed)
            raise
        except httpx.HTTPError as e:
            logger.error("api_request_failed", endpoint=endpoint, error=str(e))
            raise
    
    def fetch_notes(
        self,
        cursor: Optional[str] = None,
        page_size: int = 50,
        updated_after: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Fetch notes from Fellow.app API using POST /api/v1/notes.
        
        Args:
            cursor: Pagination cursor (None for first page)
            page_size: Results per page (1-50, default 50)
            updated_after: Optional filter for incremental backup
            
        Returns:
            Dict with 'notes' containing 'data' and 'page_info' keys
        """
        body = {
            'pagination': {
                'cursor': cursor,
                'page_size': min(page_size, 50)  # API max is 50
            },
            'include': {
                'event_attendees': True,
                'content_markdown': True
            }
        }
        
        if updated_after:
            body['updated_after'] = updated_after.isoformat()
        
        logger.debug("fetching_notes", cursor=cursor, page_size=page_size)
        
        response = self._make_request('POST', '/api/v1/notes', json=body)
        
        return response
    
    def close(self):
        """Close HTTP client."""
        self.client.close()
