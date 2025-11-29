
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from sentinel_core.orchestrator import Sentinel
from sentinel_core.graph_store import GraphManager

@pytest.mark.asyncio
async def test_healing_unchanged_content():
    """
    Test that process_url correctly handles unchanged content by updating verification timestamps.
    """
    # Mock dependencies
    mock_graph = Mock(spec=GraphManager)
    mock_scraper = AsyncMock()
    mock_extractor = Mock()
    
    # Setup Sentinel
    sentinel = Sentinel(mock_graph, mock_scraper, mock_extractor)
    
    # Test data
    url = "https://example.com"
    content_hash = "hash123"
    
    # Mock graph state: document exists with same hash
    mock_graph.get_document_state.return_value = content_hash
    
    # Mock scraper: returns same content and hash
    mock_scraper.scrape_and_hash.return_value = ("markdown content", content_hash)
    
    # Mock mark_edges_verified return value
    mock_graph.mark_edges_verified.return_value = 5
    
    # Run process_url
    result = await sentinel.process_url(url)
    
    # Verify results
    assert result["status"] == "unchanged_verified"
    assert result["reason"] == "content_unchanged"
    assert result["edges_updated"] == 5
    
    # Verify graph interactions
    mock_graph.get_document_state.assert_called_once_with(url)
    mock_graph.mark_edges_verified.assert_called_once_with(url)
    mock_graph.update_document_state.assert_called_once_with(url, content_hash)
    
    # Verify extractor was NOT called
    mock_extractor.extract.assert_not_called()
    mock_graph.upsert_data.assert_not_called()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
