"""
Phase 1 Tests: Infrastructure & Scraper

Tests for Docker infrastructure and Firecrawl scraper functionality.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from neo4j import GraphDatabase

from sentinel_core import SentinelScraper, ScraperException


# ============================================
# Test 1: Neo4j Connectivity
# ============================================

def test_neo4j_reachable():
    """
    Test that Neo4j is reachable on port 7687.
    
    This test verifies the Docker infrastructure is running correctly.
    """
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")

    try:
        driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password),
        )
        
        # Verify connection
        with driver.session() as session:
            result = session.run("RETURN 1 AS num")
            record = result.single()
            assert record["num"] == 1
        
        driver.close()
        
    except Exception as e:
        pytest.fail(f"Neo4j is not reachable: {e}")


# ============================================
# Test 2: Mock Firecrawl Scraper
# ============================================

@pytest.mark.asyncio
async def test_scraper_saves_markdown_mock():
    """
    Test that SentinelScraper correctly saves markdown to disk (mocked).
    
    This test mocks the Firecrawl API response to avoid hitting the actual API.
    """
    # Setup
    test_url = "https://example.com/test"
    test_markdown = "# Test Page\n\nThis is test content."
    test_data_dir = Path("./test_data/raw")
    
    # Clean up test directory if it exists
    if test_data_dir.exists():
        import shutil
        shutil.rmtree(test_data_dir.parent)
    
    # Mock Firecrawl response
    mock_response = {
        "success": True,
        "markdown": test_markdown,
        "html": "<html><body><h1>Test Page</h1></body></html>",
        "metadata": {
            "title": "Test Page"
        }
    }
    
    # Create scraper with test directory
    scraper = SentinelScraper(
        api_key="test_api_key",
        raw_data_dir=str(test_data_dir),
    )
    
    # Mock the Firecrawl client
    with patch.object(scraper.client, 'scrape', return_value=mock_response):
        result = await scraper.scrape_url(test_url)
    
    # Assertions
    assert result["url"] == test_url
    assert result["markdown"] == test_markdown
    assert result["title"] == "Test Page"
    assert "file_path" in result
    
    # Verify file was saved
    file_path = Path(result["file_path"])
    assert file_path.exists()
    assert file_path.read_text(encoding="utf-8") == test_markdown
    
    # Verify directory structure: data/raw/{domain}/{hash}.md
    assert "example.com" in str(file_path)
    assert file_path.suffix == ".md"
    
    # Cleanup
    import shutil
    shutil.rmtree(test_data_dir.parent)


@pytest.mark.asyncio
async def test_scraper_retry_on_failure():
    """
    Test that scraper retries on failure with exponential backoff.
    """
    test_url = "https://example.com/fail"
    test_data_dir = Path("./test_data/raw")
    
    # Create scraper
    scraper = SentinelScraper(
        api_key="test_api_key",
        raw_data_dir=str(test_data_dir),
        retry_attempts=3,
    )
    
    # Mock to fail twice, then succeed
    call_count = 0
    
    def mock_scrape_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return {"success": False, "error": "Temporary failure"}
        return {
            "success": True,
            "markdown": "# Success after retry",
            "html": "<html></html>",
            "metadata": {"title": "Success"}
        }
    
    with patch.object(scraper.client, 'scrape', side_effect=mock_scrape_side_effect):
        result = await scraper.scrape_url(test_url)
    
    # Should have retried and eventually succeeded
    assert call_count == 3
    assert result["markdown"] == "# Success after retry"
    
    # Cleanup
    if test_data_dir.parent.exists():
        import shutil
        shutil.rmtree(test_data_dir.parent)


@pytest.mark.asyncio
async def test_scraper_batch_processing():
    """
    Test batch scraping of multiple URLs.
    """
    test_urls = [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page3",
    ]
    test_data_dir = Path("./test_data/raw")
    
    scraper = SentinelScraper(
        api_key="test_api_key",
        raw_data_dir=str(test_data_dir),
    )
    
    # Mock responses
    def mock_scrape(url, params=None):
        return {
            "success": True,
            "markdown": f"# Content from {url}",
            "html": f"<html>{url}</html>",
            "metadata": {"title": f"Page {url}"}
        }
    
    with patch.object(scraper.client, 'scrape', side_effect=mock_scrape):
        results = await scraper.scrape_batch(test_urls)
    
    # Assertions
    assert len(results) == 3
    for i, result in enumerate(results):
        assert result["url"] == test_urls[i]
        assert f"Content from {test_urls[i]}" in result["markdown"]
    
    # Cleanup
    if test_data_dir.parent.exists():
        import shutil
        shutil.rmtree(test_data_dir.parent)


# ============================================
# Test 3: Integration Test (Real URL)
# ============================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_scraper_real_url():
    """
    Integration test: Scrape a real URL (example.com).
    
    This test hits the actual Firecrawl API and requires:
    - Valid FIRECRAWL_API_KEY environment variable
    - Internet connection
    
    Mark with @pytest.mark.integration to run separately.
    """
    api_key = os.getenv("FIRECRAWL_API_KEY")
    
    if not api_key or api_key == "your_firecrawl_api_key_here":
        pytest.skip("FIRECRAWL_API_KEY not set - skipping integration test")
    
    test_url = "https://example.com"
    test_data_dir = Path("./test_data/raw")
    
    # Create scraper
    scraper = SentinelScraper(
        api_key=api_key,
        raw_data_dir=str(test_data_dir),
    )
    
    try:
        result = await scraper.scrape_url(test_url)
        
        # Assertions
        assert result["url"] == test_url
        assert len(result["markdown"]) > 0
        assert "example" in result["markdown"].lower()
        
        # Verify file was saved
        file_path = Path(result["file_path"])
        assert file_path.exists()
        
        print(f"\n✅ Successfully scraped {test_url}")
        print(f"   Content length: {len(result['markdown'])} chars")
        print(f"   Saved to: {file_path}")
        
    finally:
        # Cleanup
        if test_data_dir.parent.exists():
            import shutil
            shutil.rmtree(test_data_dir.parent)


# ============================================
# Test 4: Content Hash Generation
# ============================================

def test_content_hash_generation():
    """
    Test that content hash generation is consistent.
    """
    scraper = SentinelScraper(api_key="test_key")
    
    content1 = "Hello, World!"
    content2 = "Hello, World!"
    content3 = "Different content"
    
    hash1 = scraper.get_content_hash(content1)
    hash2 = scraper.get_content_hash(content2)
    hash3 = scraper.get_content_hash(content3)
    
    # Same content should produce same hash
    assert hash1 == hash2
    
    # Different content should produce different hash
    assert hash1 != hash3
    
    # Hash should be 64 characters (SHA-256 hex)
    assert len(hash1) == 64


# ============================================
# Test 5: Error Handling
# ============================================

@pytest.mark.asyncio
async def test_scraper_handles_empty_content():
    """
    Test that scraper raises exception for empty content.
    """
    test_url = "https://example.com/empty"
    test_data_dir = Path("./test_data/raw")
    
    scraper = SentinelScraper(
        api_key="test_api_key",
        raw_data_dir=str(test_data_dir),
    )
    
    # Mock empty response
    mock_response = {
        "success": True,
        "markdown": "",  # Empty content
        "html": "",
        "metadata": {"title": "Empty"}
    }
    
    with patch.object(scraper.client, 'scrape', return_value=mock_response):
        with pytest.raises(ScraperException, match="Empty markdown content"):
            await scraper.scrape_url(test_url)


@pytest.mark.asyncio
async def test_scraper_handles_api_failure():
    """
    Test that scraper handles API failures gracefully.
    """
    test_url = "https://example.com/fail"
    test_data_dir = Path("./test_data/raw")
    
    scraper = SentinelScraper(
        api_key="test_api_key",
        raw_data_dir=str(test_data_dir),
        retry_attempts=2,  # Reduce retries for faster test
    )
    
    # Mock failure response
    mock_response = {
        "success": False,
        "error": "API rate limit exceeded"
    }
    
    with patch.object(scraper.client, 'scrape', return_value=mock_response):
        with pytest.raises(ScraperException, match="Scrape failed"):
            await scraper.scrape_url(test_url)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
