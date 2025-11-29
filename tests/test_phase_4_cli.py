"""
Test script for Phase 4: CLI Verification

This script tests the Sentinel CLI commands.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd):
    """Run a command and return output."""
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    print("\n🚀 Testing Sentinel CLI (Phase 4)")
    print("="*60)
    
    # Get python executable
    python = sys.executable
    
    # Test 1: Help command
    print("\n📝 Test 1: sentinel --help")
    success1 = run_command([python, "-m", "sentinel_core.cli", "--help"])
    
    # Test 2: Version command
    print("\n📝 Test 2: sentinel version")
    success2 = run_command([python, "-m", "sentinel_core.cli", "version"])
    
    # Test 3: Status command (might fail if Neo4j not running)
    print("\n📝 Test 3: sentinel status")
    print("(This might fail if Neo4j is not running - that's OK)")
    run_command([python, "-m", "sentinel_core.cli", "status"])
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    print(f"Help command: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Version command: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("\n🎉 Core CLI tests PASSED!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
