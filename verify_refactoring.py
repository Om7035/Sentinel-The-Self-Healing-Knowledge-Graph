"""
Quick verification script to test the refactored Sentinel structure.
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all sentinel_core imports work."""
    print("Testing sentinel_core imports...")
    
    try:
        from sentinel_core import (
            # Main components
            Sentinel,
            GraphManager,
            InfoExtractor,
            SentinelScraper,
            # Models
            GraphNode,
            TemporalEdge,
            GraphTriple,
            ScrapedContent,
            HealingResult,
            # Exceptions
            GraphException,
            ExtractionException,
            ScraperException,
        )
        print("✅ All sentinel_core imports successful!")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_service_imports():
    """Test that sentinel_service imports work."""
    print("\nTesting sentinel_service imports...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / "sentinel_service"))
        from schemas import (
            IngestRequest,
            QueryRequest,
            GraphSnapshotResponse,
            HealthResponse,
        )
        print("✅ All sentinel_service imports successful!")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def check_structure():
    """Verify the new directory structure exists."""
    print("\nChecking directory structure...")
    
    required_dirs = [
        "sentinel_core",
        "sentinel_service",
        "sentinel_ui",
        "examples",
        "tests",
    ]
    
    required_files = [
        "sentinel_core/__init__.py",
        "sentinel_core/models.py",
        "sentinel_core/graph_store.py",
        "sentinel_core/extractor.py",
        "sentinel_core/scraper.py",
        "sentinel_core/orchestrator.py",
        "sentinel_service/main.py",
        "sentinel_service/schemas.py",
        "sentinel_service/worker.py",
        "sentinel_service/query_engine.py",
        "examples/basic_bot.py",
        "README.md",
        "docker-compose.yml",
        "pyproject.toml",
    ]
    
    project_root = Path(__file__).parent
    all_good = True
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"✅ {dir_name}/ exists")
        else:
            print(f"❌ {dir_name}/ missing")
            all_good = False
    
    for file_name in required_files:
        file_path = project_root / file_name
        if file_path.exists():
            print(f"✅ {file_name} exists")
        else:
            print(f"❌ {file_name} missing")
            all_good = False
    
    return all_good

def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Sentinel Refactoring Verification")
    print("=" * 60)
    
    results = []
    
    # Test imports
    results.append(test_imports())
    results.append(test_service_imports())
    
    # Check structure
    results.append(check_structure())
    
    # Summary
    print("\n" + "=" * 60)
    if all(results):
        print("🎉 All verification tests passed!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Start infrastructure: docker-compose up -d")
        print("2. Run tests: pytest tests/ -v")
        print("3. Start API: cd sentinel_service && python main.py")
        print("4. Start UI: cd sentinel_ui && npm run dev")
        return 0
    else:
        print("⚠️  Some verification tests failed!")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
