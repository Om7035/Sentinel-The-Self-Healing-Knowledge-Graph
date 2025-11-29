"""
Firecrawl scraper implementation (Premium).

This scraper uses the Firecrawl API for high-quality web scraping
with JavaScript rendering, anti-bot protection, and clean markdown output.
"""

import os
from datetime import datetime
from typing import Optional

try:
    from firecrawl import FirecrawlApp
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False

from ..models import ScrapeResult
from .base import BaseScraper


class FirecrawlScraper(BaseScraper):
    """Premium scraper using Firecrawl API.
    
    Firecrawl provides:
    - JavaScript rendering
    - Anti-bot protection bypass
    - Clean markdown conversion
    - Rate limit handling
    
    Requires FIRECRAWL_API_KEY environment variable.
    """
    
    def __init__(self, config: Optional[dict] = None):
        """Initialize Firecrawl scraper.
        
        Args:
            config: Optional configuration with:
                - api_key: Firecrawl API key (defaults to env var)
                - timeout: Request timeout in seconds
                
        Raises:
            ImportError: If firecrawl-py is not installed
            ValueError: If API key is not provided
        """
        super().__init__(config)
        
        if not FIRECRAWL_AVAILABLE:
            raise ImportError(
                "firecrawl-py is not installed. "
                "Install it with: pip install firecrawl-py"
            )
        
        # Get API key from config or environment
        self.api_key = self.config.get('api_key') or os.getenv('FIRECRAWL_API_KEY')
        if not self.api_key:
            raise ValueError(
                "FIRECRAWL_API_KEY not found. "
                "Set it in environment or pass via config."
            )
        
        # Initialize Firecrawl client
        self.client = FirecrawlApp(api_key=self.api_key)
    
    async def scrape(self, url: str) -> ScrapeResult:
        """Scrape content from a URL using Firecrawl.
        
        Args:
            url: The URL to scrape
            
        Returns:
            ScrapeResult with markdown content
            
        Raises:
            Exception: If Firecrawl API call fails
        """
        try:
            # Call Firecrawl API (synchronous, but we're in async context)
            # Firecrawl v1 used scrape_url, v2+ uses scrape
            if hasattr(self.client, 'scrape_url'):
                result = self.client.scrape_url(url)
            else:
                result = self.client.scrape(url)
            
            # Extract data from Firecrawl response
            # The response structure varies, so we handle both formats
            if isinstance(result, dict):
                markdown_content = result.get('markdown', result.get('content', ''))
                metadata = result.get('metadata', {})
                title = metadata.get('title') if isinstance(metadata, dict) else None
            else:
                # Fallback if result is not a dict
                markdown_content = str(result)
                title = None
                metadata = {}
            
            # Compute content hash
            content_hash = ScrapeResult.compute_content_hash(markdown_content)
            
            return ScrapeResult(
                url=url,
                content=markdown_content,
                content_hash=content_hash,
                title=title,
                metadata={
                    'scraper': 'firecrawl',
                    'firecrawl_metadata': metadata,
                },
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            # Re-raise with more context
            raise Exception(f"Firecrawl scraping failed for {url}: {str(e)}") from e
    
    def check_availability(self) -> bool:
        """Check if Firecrawl is available and configured.
        
        Returns:
            True if API key is set and library is installed
        """
        return FIRECRAWL_AVAILABLE and bool(self.api_key)
    
    def get_name(self) -> str:
        """Get scraper name.
        
        Returns:
            Human-readable name
        """
        return "Firecrawl Scraper (Premium)"
