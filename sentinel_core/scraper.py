"""Sentinel Scraper Module - Firecrawl Integration"""

from __future__ import annotations

import asyncio
import hashlib
import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import structlog
from firecrawl import FirecrawlApp
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = structlog.get_logger(__name__)


class ScraperException(Exception):
    """Raised when scraping operations fail"""
    pass


class SentinelScraper:
    """
    Firecrawl-based web scraper with retry logic and local persistence.
    
    Follows Single Responsibility Principle: handles only web scraping
    and raw content storage.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.firecrawl.dev",
        raw_data_dir: str = "./data/raw",
        retry_attempts: int = 3,
        retry_backoff_base: float = 2.0,
        timeout: int = 30,
    ) -> None:
        """
        Initialize the Sentinel Scraper.

        Args:
            api_key: Firecrawl API key
            base_url: Firecrawl API base URL
            raw_data_dir: Directory to store raw scraped content
            retry_attempts: Number of retry attempts on failure
            retry_backoff_base: Base for exponential backoff (seconds)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url
        self.raw_data_dir = Path(raw_data_dir)
        self.retry_attempts = retry_attempts
        self.retry_backoff_base = retry_backoff_base
        self.timeout = timeout

        # Initialize Firecrawl client
        self.client = FirecrawlApp(api_key=api_key, api_url=base_url)

        # Ensure raw data directory exists
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "sentinel_scraper_initialized",
            raw_data_dir=str(self.raw_data_dir),
            retry_attempts=retry_attempts,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ScraperException),
        reraise=True,
    )
    async def scrape_url(self, url: str) -> dict[str, str]:
        """
        Scrape a single URL and return structured content.

        This method includes automatic retry with exponential backoff.
        Raw markdown is saved to disk in a domain-based directory structure.

        Args:
            url: The URL to scrape

        Returns:
            Dictionary containing:
                - url: Original URL
                - markdown: Extracted markdown content
                - html: Raw HTML (if available)
                - title: Page title
                - file_path: Path where raw content was saved

        Raises:
            ScraperException: If scraping fails after all retries
        """
        logger.info("scraping_url", url=url)

        try:
            # Scrape using Firecrawl (run in thread pool as it's synchronous)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.scrape(
                    url,
                ),
            )

            # Handle different response types (dict or object)
            if isinstance(response, list):
                if not response:
                    raise ScraperException("Empty response list from Firecrawl")
                response = response[0]

            # Extract content based on type
            if hasattr(response, "markdown"):
                # Object style (newer SDKs)
                markdown = response.markdown
                html = getattr(response, "html", "")
                # Metadata might be an object or dict
                metadata = getattr(response, "metadata", {})
                if isinstance(metadata, dict):
                    title = metadata.get("title", "Untitled")
                else:
                    title = getattr(metadata, "title", "Untitled")
            elif isinstance(response, dict):
                # Dict style
                if not response.get("success", True): # Default to true if key missing
                     raise ScraperException(f"Scrape failed: {response.get('error')}")
                markdown = response.get("markdown", "")
                html = response.get("html", "")
                title = response.get("metadata", {}).get("title", "Untitled")
            else:
                logger.error("unknown_response_type", type=str(type(response)))
                raise ScraperException(f"Unknown response type: {type(response)}")

            if not markdown:
                logger.warning("empty_markdown_content", url=url)
                raise ScraperException(f"Empty markdown content for {url}")

            # Save to disk
            file_path = await self._save_raw_content(url, markdown)

            logger.info(
                "scraping_successful",
                url=url,
                content_length=len(markdown),
                file_path=str(file_path),
            )

            return {
                "url": url,
                "markdown": markdown,
                "html": html,
                "title": title,
                "file_path": str(file_path),
            }

        except ScraperException:
            raise
        except Exception as e:
            logger.error("unexpected_scraping_error", url=url, error=str(e), exc_info=True)
            raise ScraperException(f"Unexpected error scraping {url}: {e}") from e

    async def scrape_and_hash(self, url: str) -> tuple[str, str]:
        """
        Scrape a URL and return its markdown content and SHA-256 hash.

        Args:
            url: The URL to scrape

        Returns:
            Tuple of (markdown_content, content_hash)
        """
        result = await self.scrape_url(url)
        markdown = result["markdown"]
        content_hash = self.get_content_hash(markdown)
        return markdown, content_hash

    async def _save_raw_content(self, url: str, content: str) -> Path:
        """
        Save raw markdown content to disk.

        Files are organized as: data/raw/{domain}/{content_hash}.md

        Args:
            url: Source URL
            content: Markdown content to save

        Returns:
            Path to saved file
        """
        # Extract domain from URL
        parsed = urlparse(url)
        domain = parsed.netloc or "unknown"
        domain = domain.replace(":", "_")  # Handle ports

        # Create content hash for filename
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

        # Create domain directory
        domain_dir = self.raw_data_dir / domain
        domain_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = domain_dir / f"{content_hash}.md"

        # Write content asynchronously
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: file_path.write_text(content, encoding="utf-8"),
        )

        logger.debug("raw_content_saved", file_path=str(file_path), size=len(content))

        return file_path

    async def scrape_batch(self, urls: list[str]) -> list[dict[str, str]]:
        """
        Scrape multiple URLs concurrently.

        Args:
            urls: List of URLs to scrape

        Returns:
            List of scrape results (successful scrapes only)
        """
        logger.info("scraping_batch", num_urls=len(urls))

        tasks = [self.scrape_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log them
        successful_results = []
        failed_count = 0

        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                logger.error("batch_scrape_failed", url=url, error=str(result))
                failed_count += 1
            else:
                successful_results.append(result)

        logger.info(
            "batch_scraping_complete",
            total=len(urls),
            successful=len(successful_results),
            failed=failed_count,
        )

        return successful_results

    def get_content_hash(self, content: str) -> str:
        """
        Generate SHA-256 hash of content.

        Useful for change detection.

        Args:
            content: Content to hash

        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
