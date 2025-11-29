"""
Local scraper implementation using BeautifulSoup and Markdownify.

This is the free fallback scraper that works without any API keys.
It uses standard Python libraries to fetch and convert web pages to markdown.
"""

import asyncio
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

from ..models import ScrapeResult
from .base import BaseScraper


class LocalScraper(BaseScraper):
    """Free local scraper using requests + BeautifulSoup + markdownify.
    
    This scraper works without any API keys and is the default fallback
    when Firecrawl is not available. It's suitable for development and
    testing, though it may not handle JavaScript-heavy sites as well.
    """
    
    def __init__(self, config: Optional[dict] = None):
        """Initialize the local scraper.
        
        Args:
            config: Optional configuration with:
                - user_agent: Custom User-Agent string
                - timeout: Request timeout in seconds (default: 30)
        """
        super().__init__(config)
        self.user_agent = self.config.get(
            'user_agent',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        self.timeout = self.config.get('timeout', 30)
    
    async def scrape(self, url: str) -> ScrapeResult:
        """Scrape content from a URL using local tools.
        
        Args:
            url: The URL to scrape
            
        Returns:
            ScrapeResult with markdown content
            
        Raises:
            requests.RequestException: If the HTTP request fails
            Exception: For other scraping errors
        """
        # Run blocking requests in thread pool to keep async
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._scrape_sync, url)
    
    def _scrape_sync(self, url: str) -> ScrapeResult:
        """Synchronous scraping implementation.
        
        Args:
            url: The URL to scrape
            
        Returns:
            ScrapeResult with markdown content
        """
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Fetch the page
        response = requests.get(url, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = None
        if soup.title:
            title = soup.title.string.strip() if soup.title.string else None
        
        # Remove script and style elements
        for script in soup(["script", "style", "noscript"]):
            script.decompose()
        
        # Convert to markdown
        markdown_content = md(str(soup), heading_style="ATX")
        
        # Clean up excessive whitespace
        lines = [line.strip() for line in markdown_content.split('\n')]
        markdown_content = '\n'.join(line for line in lines if line)
        
        # Compute content hash
        content_hash = ScrapeResult.compute_content_hash(markdown_content)
        
        return ScrapeResult(
            url=url,
            content=markdown_content,
            content_hash=content_hash,
            title=title,
            metadata={
                'scraper': 'local',
                'user_agent': self.user_agent,
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type', 'unknown')
            },
            timestamp=datetime.utcnow()
        )
    
    def check_availability(self) -> bool:
        """Check if local scraper is available.
        
        Returns:
            Always True since local scraper has no external dependencies
        """
        return True
    
    def get_name(self) -> str:
        """Get scraper name.
        
        Returns:
            Human-readable name
        """
        return "Local Scraper (Free Mode)"
