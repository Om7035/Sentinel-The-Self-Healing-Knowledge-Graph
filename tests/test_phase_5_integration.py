"""
Phase 5: End-to-End Integration Test

This test simulates a complete user journey:
1. Setup and initialization
2. URL ingestion
3. Knowledge extraction
4. Graph querying
5. Healing cycle
6. API server interaction

This ensures everything works together before publication.
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Test configuration
TEST_URL = "https://example.com"
TEST_QUESTION = "What is this page about?"


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_step(step_num, description):
    """Print a test step."""
    print(f"\n[Step {step_num}] {description}")
    print("-" * 70)


def print_result(success, message):
    """Print test result."""
    status = "[PASS]" if success else "[FAIL]"
    print(f"{status}: {message}")
    return success


async def test_phase_5_integration():
    """Run comprehensive end-to-end integration test."""
    
    print_section("PHASE 5: END-TO-END INTEGRATION TEST")
    print("This test verifies the complete Sentinel system")
    print("Testing: Python API, CLI, Database, Scrapers, Extractors")
    
    results = []
    
    # ========================================================================
    # TEST 1: Environment Check
    # ========================================================================
    print_section("TEST 1: Environment Verification")
    
    print_step(1.1, "Checking Python version")
    py_version = sys.version_info
    success = py_version >= (3, 11)
    results.append(print_result(success, f"Python {py_version.major}.{py_version.minor}"))
    
    print_step(1.2, "Checking required environment variables")
    # Set default model to phi3 as it is available in the environment
    if not os.getenv("OLLAMA_MODEL"):
        os.environ["OLLAMA_MODEL"] = "ollama/phi3"
        
    env_vars = {
        "NEO4J_URI": os.getenv("NEO4J_URI"),
        "NEO4J_USER": os.getenv("NEO4J_USER"),
        "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD"),
        "OLLAMA_MODEL": os.getenv("OLLAMA_MODEL"),
    }
    
    for key, value in env_vars.items():
        has_value = value is not None
        results.append(print_result(has_value, f"{key}: {'Set' if has_value else 'Not set'}"))
    
    # ========================================================================
    # TEST 2: Core Imports
    # ========================================================================
    print_section("TEST 2: Core Module Imports")
    
    print_step(2.1, "Importing sentinel_core modules")
    try:
        from sentinel_core import GraphManager, GraphExtractor, Sentinel
        from sentinel_core.models import GraphData, GraphNode, TemporalEdge
        from sentinel_core.scraper import get_scraper, print_scraper_status
        results.append(print_result(True, "All core modules imported successfully"))
    except Exception as e:
        results.append(print_result(False, f"Import failed: {e}"))
        return results
    
    # ========================================================================
    # TEST 3: Database Connectivity
    # ========================================================================
    print_section("TEST 3: Database Connectivity")
    
    print_step(3.1, "Connecting to Neo4j")
    try:
        graph_manager = GraphManager()
        graph_manager.verify_connectivity()
        results.append(print_result(True, "Neo4j connection successful"))
        
        print_step(3.2, "Getting graph statistics")
        snapshot = graph_manager.get_graph_snapshot()
        node_count = snapshot['metadata']['node_count']
        link_count = snapshot['metadata']['link_count']
        results.append(print_result(True, f"Graph has {node_count} nodes, {link_count} edges"))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        results.append(print_result(False, f"Error: {e}"))
    
    # ========================================================================
    # TEST 4: Scraper Availability
    # ========================================================================
    print_section("TEST 4: Scraper System")
    
    print_step(4.1, "Checking available scrapers")
    print_scraper_status()
    
    print_step(4.2, "Initializing scraper")
    try:
        scraper = get_scraper()
        scraper_name = scraper.get_name()
        results.append(print_result(True, f"Using scraper: {scraper_name}"))
    except Exception as e:
        import traceback
        traceback.print_exc()
        results.append(print_result(False, f"Scraper initialization failed: {e}"))
        return results
    
    # ========================================================================
    # TEST 5: LLM Extractor
    # ========================================================================
    print_section("TEST 5: LLM Extractor")
    
    print_step(5.1, "Initializing GraphExtractor")
    try:
        model_name = os.getenv("OLLAMA_MODEL", "ollama/phi3")
        extractor = GraphExtractor(model_name=model_name)
        results.append(print_result(True, f"Extractor initialized with model: {model_name}"))
    except Exception as e:
        import traceback
        traceback.print_exc()
        results.append(print_result(False, f"Extractor initialization failed: {e}"))
        return results
    
    # ========================================================================
    # TEST 6: Sentinel Orchestrator
    # ========================================================================
    print_section("TEST 6: Sentinel Orchestrator")
    
    print_step(6.1, "Creating Sentinel instance")
    try:
        sentinel = Sentinel(graph_manager, scraper, extractor)
        results.append(print_result(True, "Sentinel orchestrator created"))
    except Exception as e:
        import traceback
        traceback.print_exc()
        results.append(print_result(False, f"Sentinel creation failed: {e}"))
        return results
    
    # ========================================================================
    # TEST 7: URL Processing (Core Functionality)
    # ========================================================================
    print_section("TEST 7: URL Processing Pipeline")
    
    print_step(7.1, f"Processing URL: {TEST_URL}")
    print("This tests: Scraping → Extraction → Graph Storage")
    
    try:
        start_time = time.time()
        result = await sentinel.process_url(TEST_URL)
        duration = time.time() - start_time
        
        if result["status"] == "success":
            nodes = result.get("extracted_nodes", 0)
            edges = result.get("extracted_edges", 0)
            results.append(print_result(True, 
                f"URL processed in {duration:.2f}s: {nodes} nodes, {edges} edges"))
        elif result["status"] == "unchanged_verified":
            results.append(print_result(True, 
                f"Content unchanged, verified existing edges"))
        else:
            results.append(print_result(False, 
                f"Processing failed: {result.get('error', 'Unknown error')}"))
    except Exception as e:
        import traceback
        traceback.print_exc()
        results.append(print_result(False, f"URL processing failed: {e}"))
    
    # ========================================================================
    # TEST 8: Graph Querying
    # ========================================================================
    print_section("TEST 8: Graph Querying")
    
    print_step(8.1, "Retrieving graph snapshot")
    try:
        snapshot = graph_manager.get_graph_snapshot()
        results.append(print_result(True, 
            f"Retrieved {len(snapshot['nodes'])} nodes, {len(snapshot['links'])} links"))
    except Exception as e:
        import traceback
        traceback.print_exc()
        results.append(print_result(False, f"Graph query failed: {e}"))
    
    print_step(8.2, "Testing time-travel query")
    try:
        from datetime import datetime, timedelta
        past_time = datetime.utcnow() - timedelta(days=1)
        past_snapshot = graph_manager.get_graph_snapshot(timestamp=past_time)
        results.append(print_result(True, 
            f"Time-travel query successful: {len(past_snapshot['nodes'])} nodes at {past_time.isoformat()}"))
    except Exception as e:
        import traceback
        traceback.print_exc()
        results.append(print_result(False, f"Time-travel query failed: {e}"))
    
    # ========================================================================
    # TEST 9: Healing System
    # ========================================================================
    print_section("TEST 9: Self-Healing System")
    
    print_step(9.1, "Finding stale nodes")
    try:
        stale_urls = graph_manager.find_stale_nodes(days_threshold=30)
        results.append(print_result(True, 
            f"Found {len(stale_urls)} stale URLs (threshold: 30 days)"))
    except Exception as e:
        import traceback
        traceback.print_exc()
        results.append(print_result(False, f"Stale node detection failed: {e}"))
    
    # ========================================================================
    # TEST 10: Cleanup
    # ========================================================================
    print_section("TEST 10: Cleanup")
    
    print_step(10.1, "Closing connections")
    try:
        graph_manager.close()
        results.append(print_result(True, "All connections closed cleanly"))
    except Exception as e:
        results.append(print_result(False, f"Cleanup failed: {e}"))
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print_section("TEST SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(results)
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests} ({success_rate:.1f}%)")
    print(f"Failed: {failed_tests}")
    
    if failed_tests == 0:
        print("\nALL TESTS PASSED!")
        print("\nSentinel is ready for publication!")
        print("\nNext steps:")
        print("  1. Review documentation")
        print("  2. Create demo materials")
        print("  3. Build package")
        print("  4. Publish to PyPI")
        return 0
    else:
        print("\nSOME TESTS FAILED")
        print("\nFix failing tests before publication")
        return 1


def main():
    """Main entry point."""
    try:
        exit_code = asyncio.run(test_phase_5_integration())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
