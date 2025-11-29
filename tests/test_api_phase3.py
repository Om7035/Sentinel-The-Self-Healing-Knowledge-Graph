"""
Phase 3 API Tests.

Tests for:
1. POST /job (Job Submission)
2. GET /graph/history (Time Travel Query)
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import MagicMock, patch

# Import app
from sentinel_service.main import app

client = TestClient(app)

@pytest.fixture
def mock_celery():
    with patch("sentinel_service.celery_app.process_url_task") as mock_task:
        mock_task.delay.return_value.id = "test-task-id"
        yield mock_task

@pytest.fixture
def mock_graph_manager():
    with patch("sentinel_service.main.get_graph_manager") as mock_get:
        mock_manager = MagicMock()
        mock_get.return_value = mock_manager
        yield mock_manager

def test_submit_job(mock_celery):
    """Test POST /job endpoint."""
    response = client.post("/job", json={"url": "https://example.com"})
    
    assert response.status_code == 202
    data = response.json()
    assert data["task_id"] == "test-task-id"
    assert data["status"] == "submitted"
    
    # Verify Celery task was called
    mock_celery.delay.assert_called_once_with("https://example.com")

def test_get_graph_history(mock_graph_manager):
    """Test GET /graph/history endpoint."""
    # Mock return data
    mock_graph_manager.get_graph_snapshot.return_value = {
        "nodes": [{"id": "A", "label": "Test"}],
        "links": [{"source": "A", "target": "B", "relation": "TEST"}],
        "metadata": {"count": 1}
    }
    
    timestamp = datetime.utcnow().isoformat()
    response = client.get(f"/graph/history?timestamp={timestamp}")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) == 1
    assert len(data["links"]) == 1
    
    # Verify manager method was called
    mock_graph_manager.get_graph_snapshot.assert_called_once()
