"""
Final cleanup script to remove legacy directories and files.

Run this script to complete the cleanup:
    python cleanup_legacy.py
"""

import shutil
from pathlib import Path

def cleanup():
    """Remove legacy directories and files."""
    project_root = Path(__file__).parent
    
    items_to_remove = [
        "frontend",  # Old frontend (replaced by sentinel_ui)
        "test_data",  # Test artifacts
        "config",  # Old config directory
    ]
    
    print("=" * 60)
    print("Cleaning up legacy files and directories...")
    print("=" * 60)
    
    for item_name in items_to_remove:
        item_path = project_root / item_name
        
        if item_path.exists():
            try:
                if item_path.is_dir():
                    print(f"\n🗑️  Removing directory: {item_name}/")
                    shutil.rmtree(item_path)
                    print(f"✅ Removed: {item_name}/")
                else:
                    print(f"\n🗑️  Removing file: {item_name}")
                    item_path.unlink()
                    print(f"✅ Removed: {item_name}")
            except Exception as e:
                print(f"⚠️  Could not remove {item_name}: {e}")
                print(f"   Please manually delete: {item_path}")
        else:
            print(f"ℹ️  Already removed: {item_name}")
    
    print("\n" + "=" * 60)
    print("Cleanup complete!")
    print("=" * 60)
    print("\nRemaining structure:")
    print("  ✅ sentinel_core/      - Core library")
    print("  ✅ sentinel_service/   - API service")
    print("  ✅ sentinel_ui/        - Frontend")
    print("  ✅ examples/           - Usage examples")
    print("  ✅ tests/              - Test suite")
    print("  ✅ docker-compose.yml  - Infrastructure")
    print("  ✅ pyproject.toml      - Package config")
    print("  ✅ README.md           - Documentation")
    
    print("\n🎉 Your Sentinel project is now clean and ready!")

if __name__ == "__main__":
    cleanup()
