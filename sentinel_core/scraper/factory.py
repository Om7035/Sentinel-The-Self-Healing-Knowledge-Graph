"""
Scraper factory for automatic scraper selection.

This module provides intelligent scraper selection based on available
API keys and configuration, with automatic fallback to local scraping.
"""

import os
import structlog
from typing import Optional

from .base import BaseScraper
from .firecrawl import FirecrawlScraper, FIRECRAWL_AVAILABLE
from .local import LocalScraper

logger = structlog.get_logger(__name__)


def get_scraper(config: Optional[dict] = None, prefer_local: bool = False) -> BaseScraper:
    """Get the best available scraper based on configuration.
    
    Selection logic:
    1. If prefer_local=True, always use LocalScraper
    2. If FIRECRAWL_API_KEY is set and firecrawl-py is installed, use FirecrawlScraper
    3. Otherwise, fall back to LocalScraper with a warning
    
    Args:
        config: Optional configuration dictionary to pass to the scraper
        prefer_local: If True, force use of LocalScraper even if Firecrawl is available
        
    Returns:
        An initialized scraper instance (FirecrawlScraper or LocalScraper)
        
    Example:
        >>> scraper = get_scraper()
        >>> result = await scraper.scrape("https://example.com")
    """
    config = config or {}
    
    # Force local if requested
    if prefer_local:
        logger.info("Using LocalScraper (forced by prefer_local=True)")
        return LocalScraper(config)
    
    # Check for Firecrawl availability
    api_key = config.get('firecrawl_api_key') or os.getenv('FIRECRAWL_API_KEY')
    
    if api_key and FIRECRAWL_AVAILABLE:
        try:
            scraper = FirecrawlScraper(config)
            if scraper.check_availability():
                logger.info(
                    "Using FirecrawlScraper (Premium Mode)",
                    api_key_present=True,
                    library_installed=True
                )
                return scraper
        except Exception as e:
            logger.warning(
                "Failed to initialize FirecrawlScraper, falling back to LocalScraper",
                error=str(e)
            )
    
    # Fallback to local scraper
    if not api_key:
        logger.warning(
            "⚠️  No FIRECRAWL_API_KEY found. Using LocalScraper (Free Mode).",
            recommendation="Set FIRECRAWL_API_KEY for better scraping quality"
        )
    elif not FIRECRAWL_AVAILABLE:
        logger.warning(
            "⚠️  firecrawl-py not installed. Using LocalScraper (Free Mode).",
            recommendation="Install with: pip install firecrawl-py"
        )
    
    return LocalScraper(config)


def get_available_scrapers() -> dict[str, bool]:
    """Get a dictionary of available scrapers and their status.
    
    Returns:
        Dictionary mapping scraper names to availability status
        
    Example:
        >>> status = get_available_scrapers()
        >>> print(status)
        {'firecrawl': True, 'local': True}
    """
    return {
        'firecrawl': FIRECRAWL_AVAILABLE and bool(os.getenv('FIRECRAWL_API_KEY')),
        'local': True  # Always available
    }


def print_scraper_status() -> None:
    """Print the status of available scrapers to console.
    
    Useful for debugging and user information.
    """
    status = get_available_scrapers()
    
    print("\n🔍 Scraper Status:")
    print("-" * 50)
    
    if status['firecrawl']:
        print("✅ Firecrawl: Available (Premium Mode)")
    else:
        print("❌ Firecrawl: Not available")
        if not FIRECRAWL_AVAILABLE:
            print("   → Install: pip install firecrawl-py")
        if not os.getenv('FIRECRAWL_API_KEY'):
            print("   → Set FIRECRAWL_API_KEY environment variable")
    
    if status['local']:
        print("✅ Local Scraper: Available (Free Mode)")
    
    print("-" * 50)
    
    # Show which will be used (but don't actually instantiate to avoid import issues)
    if status['firecrawl']:
        print(f"\n🎯 Active Scraper: Firecrawl Scraper (Premium)\n")
    else:
        print(f"\n🎯 Active Scraper: Local Scraper (Free Mode)\n")

