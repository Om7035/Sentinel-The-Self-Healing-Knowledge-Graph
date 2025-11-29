"""
Scraper module for Sentinel Knowledge Graph.

This module provides a flexible scraping architecture that supports
multiple backends (Firecrawl, Local) with automatic fallback.
"""

from .base import BaseScraper
from .factory import get_scraper, get_available_scrapers, print_scraper_status
from .firecrawl import FirecrawlScraper
from .local import LocalScraper

__all__ = [
    "BaseScraper",
    "get_scraper",
    "get_available_scrapers",
    "print_scraper_status",
    "FirecrawlScraper",
    "LocalScraper",
]

