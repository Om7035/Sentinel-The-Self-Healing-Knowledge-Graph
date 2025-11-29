"""
Phase 4 Tests: Retrieval & Visualization

Tests for time-travel queries and API endpoints.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add backend to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from graph.manager import GraphManager, GraphException
from api.main import app, get_graph_manager


# Create test client
client = TestClient(app)


# ============================================
# Test 1: Time-Travel Queries
# ============================================

@pytest.mark.integration
def test_get_graph_snapshot_current_time():
    """
    Test getting a graph snapshot at current time.
    """
    manager = GraphManager()
    
    try:
        # Clear database
        manager.clear_database()
        
        # Create some test data
        manager.upsert_temporal_edge(
            source_node="Company A",
            relation_type="LOCATED_IN",
            target_node="City X",
            source_url="https://example.com/a",
        )
        
        manager.upsert_temporal_edge(
            source_node="Company A",
            relation_type="FOUNDED_BY",
            target_node="Person B",
            source_url="https://example.com/a",
        )
        
        # Get snapshot at current time
        snapshot = manager.get_graph_snapshot()
        
        print(f"\n✅ Retrieved snapshot:")
        print(f"   Nodes: {len(snapshot['nodes'])}")
        print(f"   Links: {len(snapshot['links'])}")
        
        # Verify structure
        assert "nodes" in snapshot
        assert "links" in snapshot
        assert "metadata" in snapshot
        
        # Verify data
        assert len(snapshot["nodes"]) == 3  # Company A, City X, Person B
        assert len(snapshot["links"]) == 2  # Two relationships
        
        # Verify node structure
        for node in snapshot["nodes"]:
            assert "id" in node
            assert "name" in node
            assert "val" in node
        
        # Verify link structure
        for link in snapshot["links"]:
            assert "source" in link
            assert "target" in link
            assert "relation" in link
            assert "confidence" in link
        
        print("\n✅ Snapshot structure is correct")
        
    finally:
        manager.clear_database()
        manager.close()


@pytest.mark.integration
def test_get_graph_snapshot_past_time():
    """
    Test time-travel query: get snapshot from the past.
    """
    manager = GraphManager()
    
    try:
        # Clear database
        manager.clear_database()
        
        # Create old relationship (10 days ago)
        ten_days_ago = datetime.utcnow() - timedelta(days=10)
        
        with manager.driver.session(database=manager.database) as session:
            query = """
            MERGE (s:Entity {name: "OldCompany"})
            MERGE (t:Entity {name: "OldCEO"})
            CREATE (s)-[r:LED_BY]->(t)
            SET r.valid_from = datetime($old_date),
                r.valid_to = NULL,
                r.source_url = $url,
                r.confidence = 1.0,
                r.last_verified = datetime($old_date),
                r.verification_count = 1
            """
            session.run(
                query,
                old_date=ten_days_ago.isoformat(),
                url="https://example.com/old",
            )
        
        # Create new relationship (today)
        manager.upsert_temporal_edge(
            source_node="NewCompany",
            relation_type="LOCATED_IN",
            target_node="NewCity",
            source_url="https://example.com/new",
        )
        
        # Get snapshot from 5 days ago (should include old, not new)
        five_days_ago = datetime.utcnow() - timedelta(days=5)
        snapshot_past = manager.get_graph_snapshot(timestamp=five_days_ago)
        
        # Get snapshot from now (should include both)
        snapshot_now = manager.get_graph_snapshot()
        
        print(f"\n✅ Past snapshot (5 days ago):")
        print(f"   Nodes: {len(snapshot_past['nodes'])}")
        print(f"   Links: {len(snapshot_past['links'])}")
        
        print(f"\n✅ Current snapshot:")
        print(f"   Nodes: {len(snapshot_now['nodes'])}")
        print(f"   Links: {len(snapshot_now['links'])}")
        
        # Past snapshot should have the old relationship
        assert len(snapshot_past["links"]) >= 1
        
        # Current snapshot should have both
        assert len(snapshot_now["links"]) >= 2
        
        print("\n✅ Time-travel query works correctly")
        
    finally:
        manager.clear_database()
        manager.close()


# ============================================
# Test 2: API Endpoint Tests
# ============================================

def test_api_health_endpoint():
    """
    Test the health check endpoint.
    """
    response = client.get("/api/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert "timestamp" in data
    assert data["status"] == "healthy"
    
    print("\n✅ Health endpoint works")


def test_api_graph_snapshot_endpoint():
    """
    Test the graph snapshot API endpoint.
    
    Verify:
    1. Endpoint returns JSON
    2. Payload structure matches frontend expectations (nodes: [], links: [])
    """
    response = client.get("/api/graph-snapshot")
    
    print(f"\n✅ API Response Status: {response.status_code}")
    
    # Verify response is successful
    assert response.status_code == 200
    
    # Verify response is JSON
    assert response.headers["content-type"] == "application/json"
    
    # Parse JSON
    data = response.json()
    
    print(f"✅ Response structure:")
    print(f"   Keys: {list(data.keys())}")
    
    # Verify structure matches frontend expectations
    assert "nodes" in data, "Response must have 'nodes' field"
    assert "links" in data, "Response must have 'links' field"
    assert "metadata" in data, "Response must have 'metadata' field"
    
    # Verify types
    assert isinstance(data["nodes"], list), "'nodes' must be a list"
    assert isinstance(data["links"], list), "'links' must be a list"
    assert isinstance(data["metadata"], dict), "'metadata' must be a dict"
    
    # Verify metadata structure
    assert "timestamp" in data["metadata"]
    assert "node_count" in data["metadata"]
    assert "link_count" in data["metadata"]
    
    print(f"✅ Nodes: {len(data['nodes'])}")
    print(f"✅ Links: {len(data['links'])}")
    print(f"✅ Timestamp: {data['metadata']['timestamp']}")
    
    # If there are nodes, verify their structure
    if data["nodes"]:
        node = data["nodes"][0]
        assert "id" in node, "Node must have 'id' field"
        assert "name" in node, "Node must have 'name' field"
        assert "val" in node, "Node must have 'val' field"
        print(f"✅ Node structure is correct: {list(node.keys())}")
    
    # If there are links, verify their structure
    if data["links"]:
        link = data["links"][0]
        assert "source" in link, "Link must have 'source' field"
        assert "target" in link, "Link must have 'target' field"
        assert "relation" in link, "Link must have 'relation' field"
        print(f"✅ Link structure is correct: {list(link.keys())}")
    
    print("\n✅ API endpoint structure matches frontend expectations!")


def test_api_graph_snapshot_with_timestamp():
    """
    Test graph snapshot endpoint with timestamp parameter.
    """
    # Test with ISO timestamp
    timestamp = "2024-01-15T12:00:00Z"
    response = client.get(f"/api/graph-snapshot?timestamp={timestamp}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "nodes" in data
    assert "links" in data
    
    print(f"\n✅ Timestamp parameter works: {timestamp}")


def test_api_graph_snapshot_invalid_timestamp():
    """
    Test that API returns 400 for invalid timestamp.
    """
    response = client.get("/api/graph-snapshot?timestamp=invalid")
    
    assert response.status_code == 400
    
    print("\n✅ Invalid timestamp correctly rejected")


def test_api_stats_endpoint():
    """
    Test the stats endpoint.
    """
    response = client.get("/api/stats")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "total_nodes" in data
    assert "total_edges" in data
    assert "stale_urls_count" in data
    assert "timestamp" in data
    
    print(f"\n✅ Stats endpoint works:")
    print(f"   Nodes: {data['total_nodes']}")
    print(f"   Edges: {data['total_edges']}")
    print(f"   Stale URLs: {data['stale_urls_count']}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
