"""
Base scraper interface for Sentinel Knowledge Graph.

This module defines the abstract base class that all scraper implementations
must inherit from, ensuring a consistent API across different backends.
"""

from abc import ABC, abstractmethod
from typing import Optional

from ..models import ScrapeResult


class BaseScraper(ABC):
    """Abstract base class for all scraper implementations.
    
    This ensures a consistent interface whether using Firecrawl (premium)
    or local scraping (free fallback).
    """
    
    def __init__(self, config: Optional[dict] = None):
        """Initialize the scraper.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
    
    @abstractmethod
    async def scrape(self, url: str) -> ScrapeResult:
        """Scrape content from a URL.
        
        Args:
            url: The URL to scrape
            
        Returns:
            ScrapeResult containing the scraped content and metadata
            
        Raises:
            Exception: If scraping fails
        """
        pass
    
    @abstractmethod
    def check_availability(self) -> bool:
        """Check if this scraper is available and properly configured.
        
        Returns:
            True if the scraper can be used, False otherwise
        """
        pass
    
    def get_name(self) -> str:
        """Get the name of this scraper implementation.
        
        Returns:
            Human-readable name of the scraper
        """
        return self.__class__.__name__
