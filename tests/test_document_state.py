
import pytest
from sentinel_core import GraphManager
from datetime import datetime

@pytest.mark.integration
def test_document_state_management():
    """
    Test get_document_state and update_document_state methods.
    
    This test requires Neo4j to be running.
    """
    graph = GraphManager()
    test_url = "https://example.com/test-doc"
    initial_hash = "hash_v1"
    updated_hash = "hash_v2"
    
    try:
        # Verify connectivity
        graph.verify_connectivity()
        
        # Clear database for clean test
        graph.clear_database()
        
        # 1. Test get_document_state for new URL
        state = graph.get_document_state(test_url)
        assert state is None, "New URL should have no state"
        
        # 2. Test update_document_state
        graph.update_document_state(test_url, initial_hash)
        
        # 3. Verify state was saved
        state = graph.get_document_state(test_url)
        assert state == initial_hash, "Should retrieve saved hash"
        
        # 4. Test updating existing state
        graph.update_document_state(test_url, updated_hash)
        
        # 5. Verify state was updated
        state = graph.get_document_state(test_url)
        assert state == updated_hash, "Should retrieve updated hash"
        
        print("Document state management test passed!")
        
    finally:
        graph.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
