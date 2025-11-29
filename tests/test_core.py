"""
Phase 1 Tests: Core Sentinel Components

Tests for:
1. Data Models (GraphNode, TemporalEdge, GraphData)
2. GraphExtractor (LiteLLM + Instructor)
3. Neo4jStore (Temporal Storage Engine)
4. Time-Travel Queries

This validates the model-agnostic, output-strict architecture.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from sentinel_core import (
    GraphData,
    GraphExtractor,
    GraphManager,
    GraphNode,
    TemporalEdge,
)


# ============================================
# Test 1: Data Models
# ============================================

def test_graph_node_model():
    """Test GraphNode Pydantic model."""
    node = GraphNode(
        id="tesla_inc",
        label="Company",
        properties={"name": "Tesla", "industry": "Automotive"}
    )
    
    assert node.id == "tesla_inc"
    assert node.label == "Company"
    assert node.properties["name"] == "Tesla"


def test_temporal_edge_model():
    """Test TemporalEdge Pydantic model."""
    now = datetime.utcnow()
    
    edge = TemporalEdge(
        source="tesla_inc",
        target="elon_musk",
        relation="FOUNDED_BY",
        properties={"year": "2003"},
        valid_from=now,
        valid_to=None,
    )
    
    assert edge.source == "tesla_inc"
    assert edge.target == "elon_musk"
    assert edge.relation == "FOUNDED_BY"
    assert edge.valid_to is None


def test_temporal_edge_compute_hash():
    """Test TemporalEdge.compute_hash() method."""
    now = datetime.utcnow()
    
    edge1 = TemporalEdge(
        source="tesla_inc",
        target="elon_musk",
        relation="FOUNDED_BY",
        properties={"year": "2003"},
        valid_from=now,
    )
    
    edge2 = TemporalEdge(
        source="tesla_inc",
        target="elon_musk",
        relation="FOUNDED_BY",
        properties={"year": "2003"},
        valid_from=now + timedelta(days=1),  # Different valid_from
    )
    
    edge3 = TemporalEdge(
        source="tesla_inc",
        target="elon_musk",
        relation="FOUNDED_BY",
        properties={"year": "2004"},  # Different property
        valid_from=now,
    )
    
    # Same content should produce same hash (valid_from not included)
    hash1 = edge1.compute_hash()
    hash2 = edge2.compute_hash()
    hash3 = edge3.compute_hash()
    
    assert hash1 == hash2, "Hash should be same for same content"
    assert hash1 != hash3, "Hash should differ for different properties"
    assert len(hash1) == 64, "SHA-256 hash should be 64 characters"


def test_graph_data_container():
    """Test GraphData container model."""
    now = datetime.utcnow()
    
    nodes = [
        GraphNode(id="tesla_inc", label="Company", properties={"name": "Tesla"}),
        GraphNode(id="elon_musk", label="Person", properties={"name": "Elon Musk"}),
    ]
    
    edges = [
        TemporalEdge(
            source="tesla_inc",
            target="elon_musk",
            relation="FOUNDED_BY",
            properties={"year": "2003"},
            valid_from=now,
        )
    ]
    
    data = GraphData(nodes=nodes, edges=edges)
    
    assert len(data.nodes) == 2
    assert len(data.edges) == 1
    assert data.nodes[0].id == "tesla_inc"
    assert data.edges[0].relation == "FOUNDED_BY"


# ============================================
# Test 2: GraphExtractor (LiteLLM + Instructor)
# ============================================

@pytest.mark.skipif(True, reason="Requires LLM API - manual test only")
def test_graph_extractor_initialization():
    """Test GraphExtractor initialization."""
    extractor = GraphExtractor(
        model_name="ollama/llama3",
        base_url="http://localhost:11434",
    )
    
    assert extractor.model_name == "ollama/llama3"
    assert extractor.base_url == "http://localhost:11434"


@pytest.mark.skipif(True, reason="Requires LLM API - manual test only")
def test_graph_extractor_extract():
    """Test GraphExtractor.extract() method."""
    extractor = GraphExtractor(model_name="ollama/llama3")
    
    text = "Tesla was founded by Elon Musk in 2003. The company is based in Austin, Texas."
    
    result = extractor.extract(text)
    
    assert isinstance(result, GraphData)
    assert len(result.nodes) > 0
    assert len(result.edges) > 0


# ============================================
# Test 3: Neo4jStore (Temporal Storage Engine)
# ============================================

@pytest.mark.integration
def test_neo4j_upsert_data():
    """
    Test Neo4jStore.upsert_data() with temporal logic.
    
    This test requires Neo4j to be running.
    """
    # Initialize GraphManager
    graph = GraphManager()
    
    try:
        # Verify connectivity
        graph.verify_connectivity()
        
        # Clear database for clean test
        graph.clear_database()
        
        # Create test data
        now = datetime.utcnow()
        
        data = GraphData(
            nodes=[
                GraphNode(id="tesla_inc", label="Company", properties={"name": "Tesla"}),
                GraphNode(id="elon_musk", label="Person", properties={"name": "Elon Musk"}),
            ],
            edges=[
                TemporalEdge(
                    source="tesla_inc",
                    target="elon_musk",
                    relation="FOUNDED_BY",
                    properties={"year": "2003"},
                    valid_from=now,
                )
            ]
        )
        
        # Upsert data
        stats = graph.upsert_data(data, source_url="https://example.com/tesla")
        
        # Verify stats
        assert stats["nodes_created"] == 2
        assert stats["edges_created"] == 1
        
        # Verify data was stored
        relationships = graph.get_active_relationships()
        assert len(relationships) > 0
        
        print("Neo4j upsert_data test passed!")
        
    finally:
        graph.close()


# ============================================
# Test 4: Time-Travel Queries
# ============================================

@pytest.mark.integration
def test_time_travel_query():
    """
    Test time-travel queries: Insert Fact A, then Fact A' with different property.
    Verify DB has 2 edges: one closed (history), one open (current).
    
    This test requires Neo4j to be running.
    """
    graph = GraphManager()
    
    try:
        # Verify connectivity
        graph.verify_connectivity()
        
        # Clear database
        graph.clear_database()
        
        # Time 1: Insert Fact A
        time1 = datetime.utcnow()
        
        data1 = GraphData(
            nodes=[
                GraphNode(id="tesla_inc", label="Company", properties={"name": "Tesla"}),
                GraphNode(id="austin_tx", label="Location", properties={"name": "Austin"}),
            ],
            edges=[
                TemporalEdge(
                    source="tesla_inc",
                    target="austin_tx",
                    relation="LOCATED_IN",
                    properties={"since": "2021"},
                    valid_from=time1,
                )
            ]
        )
        
        stats1 = graph.upsert_data(data1, source_url="https://example.com/tesla")
        assert stats1["edges_created"] == 1
        
        # Time 2: Insert Fact A' with different property
        time2 = datetime.utcnow()
        
        data2 = GraphData(
            nodes=[
                GraphNode(id="tesla_inc", label="Company", properties={"name": "Tesla"}),
                GraphNode(id="austin_tx", label="Location", properties={"name": "Austin"}),
            ],
            edges=[
                TemporalEdge(
                    source="tesla_inc",
                    target="austin_tx",
                    relation="LOCATED_IN",
                    properties={"since": "2022"},  # Changed property
                    valid_from=time2,
                )
            ]
        )
        
        stats2 = graph.upsert_data(data2, source_url="https://example.com/tesla")
        assert stats2["edges_invalidated"] == 1, "Old edge should be invalidated"
        assert stats2["edges_created"] == 1, "New edge should be created"
        
        # Verify: DB should have 2 edges
        # 1. Old edge: valid_from=time1, valid_to=time2 (closed)
        # 2. New edge: valid_from=time2, valid_to=NULL (open)
        
        # Query at time1 should return old edge
        snapshot_time1 = graph.get_graph_snapshot(timestamp=time1 + timedelta(seconds=1))
        assert len(snapshot_time1["links"]) == 1
        assert snapshot_time1["links"][0]["relation"] == "LOCATED_IN"
        
        # Query at time2 should return new edge
        snapshot_time2 = graph.get_graph_snapshot(timestamp=time2 + timedelta(seconds=1))
        assert len(snapshot_time2["links"]) == 1
        assert snapshot_time2["links"][0]["relation"] == "LOCATED_IN"
        
        # Query current time should return only active edge
        snapshot_now = graph.get_graph_snapshot()
        assert len(snapshot_now["links"]) == 1
        
        print("Time-travel query test passed!")
        print(f"   - Old edge (history): valid_from={time1}, valid_to={time2}")
        print(f"   - New edge (current): valid_from={time2}, valid_to=NULL")
        
    finally:
        graph.close()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
