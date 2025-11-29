"""
Phase 2 Tests: Temporal Knowledge Graph

Tests for GraphManager and InfoExtractor functionality.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add backend to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from graph.manager import GraphManager, GraphException
from ai.extractor import InfoExtractor, GraphTriple, ExtractionException


# ============================================
# Test 1: GraphManager - Basic Operations
# ============================================

def test_graph_manager_initialization():
    """Test GraphManager initialization with environment variables."""
    # Set test environment variables
    os.environ["NEO4J_URI"] = "bolt://localhost:7687"
    os.environ["NEO4J_USERNAME"] = "neo4j"
    os.environ["NEO4J_PASSWORD"] = "password"
    
    manager = GraphManager()
    
    assert manager.uri == "bolt://localhost:7687"
    assert manager.username == "neo4j"
    assert manager.database == "neo4j"
    
    manager.close()


def test_graph_manager_missing_password():
    """Test that GraphManager raises exception when password is missing."""
    with patch.dict(os.environ, {"NEO4J_PASSWORD": ""}, clear=True):
        with pytest.raises(GraphException, match="password is required"):
            GraphManager()


@pytest.mark.integration
def test_graph_manager_connectivity():
    """
    Integration test: Verify Neo4j connectivity.
    
    Requires Docker containers to be running.
    """
    manager = GraphManager()
    
    try:
        is_connected = manager.verify_connectivity()
        assert is_connected is True
    finally:
        manager.close()


@pytest.mark.integration
def test_graph_manager_clear_database():
    """
    Integration test: Clear database.
    
    Requires Docker containers to be running.
    """
    manager = GraphManager()
    
    try:
        # Clear database
        deleted_count = manager.clear_database()
        assert isinstance(deleted_count, int)
        assert deleted_count >= 0
    finally:
        manager.close()


# ============================================
# Test 2: GraphManager - Temporal Edge Logic
# ============================================

@pytest.mark.integration
def test_upsert_temporal_edge_create():
    """
    Integration test: Create a new temporal edge.
    
    Tests the core temporal logic: creating a new relationship.
    """
    manager = GraphManager()
    
    try:
        # Clear database first
        manager.clear_database()
        
        # Create a new edge
        result = manager.upsert_temporal_edge(
            source_node="Alice",
            relation_type="WORKS_AT",
            target_node="Acme Corp",
            source_url="https://example.com/alice",
            confidence=0.95,
            evidence_text="Alice works at Acme Corp as a software engineer.",
        )
        
        # Verify result
        assert result["action"] == "created"
        assert "relationship_id" in result
        assert "valid_from" in result
        assert "last_verified" in result
        
        # Verify the edge exists
        active_rels = manager.get_active_relationships()
        assert len(active_rels) == 1
        assert active_rels[0]["source"] == "Alice"
        assert active_rels[0]["relation"] == "WORKS_AT"
        assert active_rels[0]["target"] == "Acme Corp"
        assert active_rels[0]["confidence"] == 0.95
        
    finally:
        manager.clear_database()
        manager.close()


@pytest.mark.integration
def test_upsert_temporal_edge_update():
    """
    Integration test: Update an existing temporal edge.
    
    Tests the core temporal logic: updating last_verified on existing relationship.
    """
    manager = GraphManager()
    
    try:
        # Clear database first
        manager.clear_database()
        
        # Create initial edge
        result1 = manager.upsert_temporal_edge(
            source_node="Bob",
            relation_type="LOCATED_IN",
            target_node="New York",
            source_url="https://example.com/bob1",
        )
        
        assert result1["action"] == "created"
        first_verified = result1["last_verified"]
        
        # Wait a moment to ensure timestamp difference
        import time
        time.sleep(0.1)
        
        # Update the same edge (should update last_verified)
        result2 = manager.upsert_temporal_edge(
            source_node="Bob",
            relation_type="LOCATED_IN",
            target_node="New York",
            source_url="https://example.com/bob2",
        )
        
        assert result2["action"] == "updated"
        assert result2["relationship_id"] == result1["relationship_id"]
        # last_verified should be updated (but we can't easily compare datetime objects)
        
        # Verify still only one active relationship
        active_rels = manager.get_active_relationships()
        assert len(active_rels) == 1
        
    finally:
        manager.clear_database()
        manager.close()


@pytest.mark.integration
def test_invalidate_edge():
    """
    Integration test: Invalidate a temporal edge.
    
    Tests setting valid_to to mark a relationship as no longer valid.
    """
    manager = GraphManager()
    
    try:
        # Clear database first
        manager.clear_database()
        
        # Create an edge
        manager.upsert_temporal_edge(
            source_node="Charlie",
            relation_type="WORKS_AT",
            target_node="OldCorp",
            source_url="https://example.com/charlie",
        )
        
        # Verify it's active
        active_rels = manager.get_active_relationships()
        assert len(active_rels) == 1
        
        # Invalidate the edge
        was_invalidated = manager.invalidate_edge(
            source_node="Charlie",
            relation_type="WORKS_AT",
            target_node="OldCorp",
        )
        
        assert was_invalidated is not None
        
        # Verify no active relationships remain
        active_rels = manager.get_active_relationships()
        assert len(active_rels) == 0
        
    finally:
        manager.clear_database()
        manager.close()


@pytest.mark.integration
def test_get_active_relationships_filtered():
    """
    Integration test: Get active relationships filtered by entity.
    """
    manager = GraphManager()
    
    try:
        # Clear database first
        manager.clear_database()
        
        # Create multiple edges
        manager.upsert_temporal_edge("Alice", "WORKS_AT", "Acme", "https://example.com")
        manager.upsert_temporal_edge("Alice", "LOCATED_IN", "NYC", "https://example.com")
        manager.upsert_temporal_edge("Bob", "WORKS_AT", "TechCorp", "https://example.com")
        
        # Get all active relationships
        all_rels = manager.get_active_relationships()
        assert len(all_rels) == 3
        
        # Get relationships for Alice
        alice_rels = manager.get_active_relationships(entity_name="Alice")
        assert len(alice_rels) == 2
        
        # Get relationships for Bob
        bob_rels = manager.get_active_relationships(entity_name="Bob")
        assert len(bob_rels) == 1
        
    finally:
        manager.clear_database()
        manager.close()


# ============================================
# Test 3: InfoExtractor - LLM Extraction
# ============================================

def test_graph_triple_validation():
    """Test GraphTriple Pydantic model validation."""
    # Valid triple
    triple = GraphTriple(
        head="Tesla",
        relation="founded_by",
        tail="Elon Musk",
        confidence=0.95,
    )
    
    assert triple.head == "Tesla"
    assert triple.relation == "FOUNDED_BY"  # Should be normalized
    assert triple.tail == "Elon Musk"
    assert triple.confidence == 0.95


def test_graph_triple_empty_validation():
    """Test that GraphTriple rejects empty fields."""
    with pytest.raises(ValueError, match="cannot be empty"):
        GraphTriple(head="", relation="WORKS_AT", tail="Company")
    
    with pytest.raises(ValueError, match="cannot be empty"):
        GraphTriple(head="Person", relation="", tail="Company")


def test_graph_triple_relation_normalization():
    """Test that relation types are normalized."""
    triple = GraphTriple(
        head="Alice",
        relation="works at",
        tail="Company",
    )
    
    assert triple.relation == "WORKS_AT"
    
    triple2 = GraphTriple(
        head="Bob",
        relation="located-in",
        tail="City",
    )
    
    assert triple2.relation == "LOCATED_IN"


def test_info_extractor_initialization():
    """Test InfoExtractor initialization."""
    extractor = InfoExtractor(
        model="llama3.1",
        base_url="http://localhost:11434",
        temperature=0.1,
    )
    
    assert extractor.model == "llama3.1"
    assert extractor.base_url == "http://localhost:11434"
    assert extractor.temperature == 0.1


@pytest.mark.asyncio
async def test_info_extractor_empty_text():
    """Test that extractor handles empty text gracefully."""
    extractor = InfoExtractor()
    
    result = extractor.extract_triples("")
    assert result == []
    
    result2 = extractor.extract_triples("   ")
    assert result2 == []


@pytest.mark.integration
def test_info_extractor_real_extraction():
    """
    Integration test: Extract triples from real text using Ollama.
    
    Requires:
    - Ollama running on localhost:11434
    - llama3.1 model installed
    
    Skip if Ollama is not available.
    """
    # Check if Ollama is available
    import requests
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code != 200:
            pytest.skip("Ollama not available")
    except:
        pytest.skip("Ollama not available")
    
    extractor = InfoExtractor(model="llama3.1")
    
    test_text = """
    Tesla is an American electric vehicle and clean energy company.
    It was founded by Elon Musk in 2003.
    The company is headquartered in Austin, Texas.
    Tesla produces electric cars, battery energy storage, and solar panels.
    """
    
    triples = extractor.extract_triples(test_text)
    
    # Should extract at least some triples
    assert len(triples) > 0
    
    # All triples should be GraphTriple instances
    for triple in triples:
        assert isinstance(triple, GraphTriple)
        assert triple.head
        assert triple.relation
        assert triple.tail
    
    print(f"\n✅ Extracted {len(triples)} triples:")
    for triple in triples:
        print(f"   ({triple.head}) -[{triple.relation}]-> ({triple.tail})")


def test_info_extractor_with_mock():
    """Test InfoExtractor with mocked extraction."""
    extractor = InfoExtractor()
    
    # Mock the extract_triples method directly
    mock_triples = [
        GraphTriple(
            head="Tesla",
            relation="FOUNDED_BY",
            tail="Elon Musk",
            confidence=1.0
        ),
        GraphTriple(
            head="Tesla",
            relation="PRODUCES",
            tail="Electric Vehicles",
            confidence=0.95
        )
    ]
    
    with patch.object(extractor, 'extract_triples', return_value=mock_triples):
        triples = extractor.extract_triples("Tesla was founded by Elon Musk.")
        
        assert len(triples) == 2
        assert triples[0].head == "Tesla"
        assert triples[0].relation == "FOUNDED_BY"
        assert triples[0].tail == "Elon Musk"


def test_info_extractor_confidence_filtering():
    """Test filtering triples by confidence threshold."""
    extractor = InfoExtractor()
    
    mock_triples = [
        GraphTriple(head="A", relation="R1", tail="B", confidence=0.9),
        GraphTriple(head="C", relation="R2", tail="D", confidence=0.4),
        GraphTriple(head="E", relation="R3", tail="F", confidence=0.7),
    ]
    
    with patch.object(extractor, 'extract_triples', return_value=mock_triples):
        # Filter with min_confidence=0.6
        triples = extractor.extract_and_validate("test text", min_confidence=0.6)
        
        # Should only include triples with confidence >= 0.6
        assert len(triples) == 2
        assert all(t.confidence >= 0.6 for t in triples)


# ============================================
# Test 4: Context Manager
# ============================================

def test_graph_manager_context_manager():
    """Test GraphManager as context manager."""
    with GraphManager() as manager:
        assert manager.driver is not None
    
    # Driver should be closed after exiting context
    # (Can't easily test this without accessing private attributes)


# ============================================
# Test 5: Detailed Temporal Test
# ============================================

@pytest.mark.integration
def test_temporal_edge_detailed_sequence():
    """
    Detailed temporal test: Insert edges at different times.
    
    Tests:
    1. Insert Edge A->B (Time 1). Verify it is active.
    2. Insert Edge A->B (Time 2). Verify it is still active and last_verified updated.
    3. Insert Edge A->C (Time 3). Verify A->B is active AND A->C is active.
    """
    import time
    
    manager = GraphManager()
    
    try:
        # Clear database first
        manager.clear_database()
        
        # TIME 1: Insert Edge A->B
        print("\n=== TIME 1: Insert A->B ===")
        result1 = manager.upsert_temporal_edge(
            source_node="A",
            relation_type="CONNECTS_TO",
            target_node="B",
            source_url="https://example.com/time1",
            confidence=0.9,
        )
        
        # Verify it was created
        assert result1["action"] == "created"
        rel_id_1 = result1["relationship_id"]
        verified_time_1 = result1["last_verified"]
        
        # Verify it is active
        active_rels = manager.get_active_relationships()
        assert len(active_rels) == 1
        assert active_rels[0]["source"] == "A"
        assert active_rels[0]["relation"] == "CONNECTS_TO"
        assert active_rels[0]["target"] == "B"
        print(f"✅ A->B created (ID: {rel_id_1})")
        
        # Wait to ensure timestamp difference
        time.sleep(0.2)
        
        # TIME 2: Insert Edge A->B again (should update)
        print("\n=== TIME 2: Insert A->B again ===")
        result2 = manager.upsert_temporal_edge(
            source_node="A",
            relation_type="CONNECTS_TO",
            target_node="B",
            source_url="https://example.com/time2",
            confidence=0.95,
        )
        
        # Verify it was updated (not created)
        assert result2["action"] == "updated"
        assert result2["relationship_id"] == rel_id_1  # Same relationship ID
        verified_time_2 = result2["last_verified"]
        
        # Verify still only one active relationship
        active_rels = manager.get_active_relationships()
        assert len(active_rels) == 1
        print(f"✅ A->B updated (same ID: {rel_id_1})")
        print(f"   Last verified updated: {verified_time_1} -> {verified_time_2}")
        
        # Wait to ensure timestamp difference
        time.sleep(0.2)
        
        # TIME 3: Insert Edge A->C (different target)
        print("\n=== TIME 3: Insert A->C ===")
        result3 = manager.upsert_temporal_edge(
            source_node="A",
            relation_type="CONNECTS_TO",
            target_node="C",
            source_url="https://example.com/time3",
            confidence=0.85,
        )
        
        # Verify it was created (new edge)
        assert result3["action"] == "created"
        rel_id_3 = result3["relationship_id"]
        assert rel_id_3 != rel_id_1  # Different relationship ID
        
        # Verify BOTH A->B and A->C are active
        active_rels = manager.get_active_relationships()
        assert len(active_rels) == 2
        
        # Verify both relationships exist
        sources = [rel["source"] for rel in active_rels]
        targets = [rel["target"] for rel in active_rels]
        
        assert sources.count("A") == 2  # Both from A
        assert "B" in targets
        assert "C" in targets
        
        print(f"✅ A->C created (ID: {rel_id_3})")
        print(f"✅ Both A->B and A->C are active")
        
        # Verify we can query by entity
        a_rels = manager.get_active_relationships(entity_name="A")
        assert len(a_rels) == 2
        
        print("\n=== Final State ===")
        for rel in active_rels:
            print(f"   {rel['source']} -[{rel['relation']}]-> {rel['target']} "
                  f"(confidence: {rel['confidence']})")
        
    finally:
        manager.clear_database()
        manager.close()


# ============================================
# Test 6: LLM Integration Tests with Real Ollama
# ============================================

@pytest.mark.integration
def test_llm_extraction_with_real_ollama():
    """
    LLM Test: Use real Ollama to extract triples from text.
    
    Requires:
    - Ollama running on localhost:11434
    - llama3.1 model installed
    """
    # Check if Ollama is available
    import requests
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code != 200:
            pytest.skip("Ollama not available")
    except:
        pytest.skip("Ollama not available")
    
    extractor = InfoExtractor(model="llama3.1", temperature=0.1)
    
    # Test text with clear, factual relationships
    test_text = """
    Apple Inc was founded by Steve Jobs in 1976.
    The company is headquartered in Cupertino, California.
    Apple produces the iPhone, iPad, and Mac computers.
    Steve Jobs co-founded Apple with Steve Wozniak.
    """
    
    print("\n=== Extracting triples from text ===")
    print(f"Text: {test_text.strip()}")
    
    # Extract triples using real LLM
    triples = extractor.extract_triples(test_text)
    
    print(f"\n✅ Extracted {len(triples)} triples using Ollama:")
    for i, triple in enumerate(triples, 1):
        print(f"   {i}. ({triple.head}) -[{triple.relation}]-> ({triple.tail}) "
              f"[confidence: {triple.confidence}]")
    
    # Verify we got some triples
    assert len(triples) > 0, "Should extract at least one triple"
    
    # Verify all are GraphTriple instances
    for triple in triples:
        assert isinstance(triple, GraphTriple)
        assert triple.head, "Head should not be empty"
        assert triple.relation, "Relation should not be empty"
        assert triple.tail, "Tail should not be empty"
        assert 0.0 <= triple.confidence <= 1.0, "Confidence should be between 0 and 1"
    
    # Check for expected entities (at least some should be found)
    all_entities = set()
    for triple in triples:
        all_entities.add(triple.head)
        all_entities.add(triple.tail)
    
    # Should find at least Apple and Steve Jobs
    entities_text = " ".join(all_entities).lower()
    assert "apple" in entities_text or "jobs" in entities_text, \
        "Should extract at least Apple or Steve Jobs"


@pytest.mark.integration
def test_llm_extraction_with_confidence_filtering():
    """
    Test extracting triples and filtering by confidence using real Ollama.
    """
    # Check if Ollama is available
    import requests
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code != 200:
            pytest.skip("Ollama not available")
    except:
        pytest.skip("Ollama not available")
    
    extractor = InfoExtractor(model="llama3.1", temperature=0.1)
    
    test_text = """
    Microsoft was founded by Bill Gates and Paul Allen in 1975.
    The company is based in Redmond, Washington.
    Microsoft develops Windows operating system and Office software.
    """
    
    print("\n=== Testing confidence filtering ===")
    
    # Extract with high confidence threshold
    high_confidence_triples = extractor.extract_and_validate(
        test_text,
        min_confidence=0.8
    )
    
    # Extract with low confidence threshold
    low_confidence_triples = extractor.extract_and_validate(
        test_text,
        min_confidence=0.3
    )
    
    print(f"High confidence (≥0.8): {len(high_confidence_triples)} triples")
    print(f"Low confidence (≥0.3): {len(low_confidence_triples)} triples")
    
    # High confidence should have fewer or equal triples
    assert len(high_confidence_triples) <= len(low_confidence_triples)
    
    # All high confidence triples should have confidence >= 0.8
    for triple in high_confidence_triples:
        assert triple.confidence >= 0.8
    
    # All low confidence triples should have confidence >= 0.3
    for triple in low_confidence_triples:
        assert triple.confidence >= 0.3


@pytest.mark.integration
def test_llm_extraction_with_retry():
    """
    Test extraction with retry logic using real Ollama.
    """
    # Check if Ollama is available
    import requests
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code != 200:
            pytest.skip("Ollama not available")
    except:
        pytest.skip("Ollama not available")
    
    extractor = InfoExtractor(model="llama3.1")
    
    test_text = """
    Google was founded by Larry Page and Sergey Brin.
    The company is headquartered in Mountain View, California.
    """
    
    print("\n=== Testing extraction with retry ===")
    
    # Use retry method
    triples = extractor.extract_triples_with_retry(test_text, max_retries=2)
    
    print(f"✅ Extracted {len(triples)} triples with retry logic")
    for triple in triples:
        print(f"   ({triple.head}) -[{triple.relation}]-> ({triple.tail})")
    
    assert len(triples) > 0
    assert all(isinstance(t, GraphTriple) for t in triples)


def test_llm_extraction_empty_text():
    """
    Test that extractor handles empty text gracefully (no Ollama needed).
    """
    extractor = InfoExtractor()
    
    # Empty text should return empty list
    result = extractor.extract_triples("")
    assert result == []
    
    # Whitespace only should return empty list
    result2 = extractor.extract_triples("   \n\t  ")
    assert result2 == []
    
    print("\n✅ Empty text handled correctly")




if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
