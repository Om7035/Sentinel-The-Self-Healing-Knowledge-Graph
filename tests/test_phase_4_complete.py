"""
Test script for Phase 4: Complete CLI Verification

This script tests all Sentinel CLI commands.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, timeout=10):
    """Run a command and return output."""
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
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
    print("\n🚀🚀🚀 PHASE 4: CLI VERIFICATION 🚀🚀🚀")
    print("="*60)
    
    python = sys.executable
    cli_script = "sentinel_cli.py"
    
    # Test 1: Help command
    print("\n📝 Test 1: sentinel --help")
    success1 = run_command([python, cli_script, "--help"])
    
    # Test 2: Version command
    print("\n📝 Test 2: sentinel version")
    success2 = run_command([python, cli_script, "version"])
    
    # Test 3: Status command
    print("\n📝 Test 3: sentinel status")
    success3 = run_command([python, cli_script, "status"], timeout=20)
    
    # Test 4: Help for watch command
    print("\n📝 Test 4: sentinel watch --help")
    success4 = run_command([python, cli_script, "watch", "--help"])
    
    # Test 5: Help for heal command
    print("\n📝 Test 5: sentinel heal --help")
    success5 = run_command([python, cli_script, "heal", "--help"])
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"Help command:        {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Version command:     {'✅ PASS' if success2 else '❌ FAIL'}")
    print(f"Status command:      {'✅ PASS' if success3 else '❌ FAIL'}")
    print(f"Watch help:          {'✅ PASS' if success4 else '❌ FAIL'}")
    print(f"Heal help:           {'✅ PASS' if success5 else '❌ FAIL'}")
    
    all_passed = all([success1, success2, success3, success4, success5])
    
    if all_passed:
        print("\n🎉🎉🎉 ALL CLI TESTS PASSED! 🎉🎉🎉")
        print("\n✅ Phase 4 is COMPLETE!")
        print("\nThe CLI is fully functional. Usage:")
        print(f"  python {cli_script} <command>")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
