
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime

from sentinel_service.main import app

client = TestClient(app)

def test_health_check():
    """Test GET /api/health endpoint."""
    with patch("sentinel_service.main.get_graph_manager") as mock_get_manager:
        # Mock successful connectivity
        mock_manager = Mock()
        mock_manager.verify_connectivity.return_value = True
        mock_get_manager.return_value = mock_manager
        
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

def test_submit_job():
    """Test POST /job endpoint."""
    with patch("sentinel_service.celery_app.process_url_task.delay") as mock_delay:
        # Mock Celery task
        mock_task = Mock()
        mock_task.id = "test-task-id"
        mock_delay.return_value = mock_task
        
        payload = {"url": "https://example.com"}
        response = client.post("/job", json=payload)
        
        assert response.status_code == 202
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "submitted"
        
        # Verify Celery task was called
        mock_delay.assert_called_once_with("https://example.com")

def test_get_graph_history():
    """Test GET /graph/history endpoint."""
    with patch("sentinel_service.main.get_graph_manager") as mock_get_manager:
        # Mock graph snapshot
        mock_manager = Mock()
        mock_snapshot = {
            "nodes": [{"id": "n1"}],
            "links": [{"source": "n1", "target": "n2"}],
            "metadata": {"node_count": 1, "link_count": 1}
        }
        mock_manager.get_graph_snapshot.return_value = mock_snapshot
        mock_get_manager.return_value = mock_manager
        
        # Test with valid timestamp
        timestamp = datetime.utcnow().isoformat()
        response = client.get(f"/graph/history?timestamp={timestamp}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["nodes"]) == 1
        assert len(data["links"]) == 1
        
        # Verify manager called with correct timestamp
        mock_manager.get_graph_snapshot.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
