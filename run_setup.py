"""
Complete setup verification script for Sentinel project.
This script runs all the setup steps to verify everything works.
"""

import subprocess
import sys
import time
from pathlib import Path

def print_step(step_num, description):
    """Print a formatted step header."""
    print("\n" + "=" * 70)
    print(f"STEP {step_num}: {description}")
    print("=" * 70)

def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def check_docker():
    """Check if Docker is running."""
    success, stdout, stderr = run_command("docker --version", check=False)
    if success:
        print(f"✅ Docker found: {stdout.strip()}")
        return True
    else:
        print("❌ Docker not found or not running")
        print("   Please start Docker Desktop and try again")
        return False

def start_infrastructure():
    """Start Docker containers."""
    print_step(1, "Starting Infrastructure (Neo4j, Postgres)")
    
    if not check_docker():
        return False
    
    print("\n🚀 Starting docker-compose...")
    success, stdout, stderr = run_command("docker-compose up -d", check=False)
    
    if success:
        print("✅ Docker containers started successfully")
        print("\nWaiting for services to be ready...")
        time.sleep(5)
        
        # Check container status
        success, stdout, stderr = run_command("docker-compose ps", check=False)
        if success:
            print(stdout)
        return True
    else:
        print("⚠️  Docker containers may already be running or Docker Desktop is not started")
        print(f"   Error: {stderr}")
        return False

def install_package():
    """Install the Sentinel package."""
    print_step(2, "Installing the Package")
    
    print("\n📦 Installing sentinel package in editable mode...")
    success, stdout, stderr = run_command(f"{sys.executable} -m pip install -e .", check=False)
    
    if success or "Successfully installed" in stdout:
        print("✅ Package installed successfully")
        
        # Verify imports
        print("\n🔍 Verifying imports...")
        success, stdout, stderr = run_command(
            f'{sys.executable} -c "from sentinel_core import Sentinel, GraphManager, InfoExtractor, SentinelScraper; print(\'✅ All imports working!\')"',
            check=False
        )
        if success:
            print(stdout.strip())
            return True
        else:
            print("❌ Import verification failed")
            print(f"   Error: {stderr}")
            return False
    else:
        print("❌ Package installation failed")
        print(f"   Error: {stderr}")
        return False

def run_tests():
    """Run the test suite."""
    print_step(3, "Running Tests")
    
    print("\n🧪 Running pytest...")
    success, stdout, stderr = run_command(
        f"{sys.executable} -m pytest tests/ -v --tb=short",
        check=False
    )
    
    if success:
        print("✅ All tests passed!")
        # Print last 20 lines of output
        lines = stdout.split('\n')
        print('\n'.join(lines[-20:]))
        return True
    else:
        print("⚠️  Some tests failed or pytest not found")
        print("   This is OK if you haven't configured Neo4j yet")
        # Print last 30 lines of output
        lines = (stdout + stderr).split('\n')
        print('\n'.join(lines[-30:]))
        return False

def check_api_service():
    """Check if API service files exist."""
    print_step(4, "Checking API Service")
    
    api_main = Path("sentinel_service/main.py")
    if api_main.exists():
        print(f"✅ API service found: {api_main}")
        print("\n📝 To start the API service, run:")
        print("   cd sentinel_service")
        print("   python main.py")
        print("\n   The API will be available at: http://localhost:8000")
        return True
    else:
        print(f"❌ API service not found: {api_main}")
        return False

def check_ui():
    """Check if UI files exist."""
    print_step(5, "Checking UI")
    
    ui_package = Path("sentinel_ui/package.json")
    if ui_package.exists():
        print(f"✅ UI found: {ui_package}")
        print("\n📝 To start the UI, run (in a new terminal):")
        print("   cd sentinel_ui")
        print("   npm install")
        print("   npm run dev")
        print("\n   The UI will be available at: http://localhost:3000")
        return True
    else:
        print(f"❌ UI not found: {ui_package}")
        return False

def print_summary(results):
    """Print final summary."""
    print("\n" + "=" * 70)
    print("SETUP VERIFICATION SUMMARY")
    print("=" * 70)
    
    steps = [
        ("Infrastructure (Docker)", results.get("infrastructure", False)),
        ("Package Installation", results.get("package", False)),
        ("Tests", results.get("tests", False)),
        ("API Service", results.get("api", False)),
        ("UI", results.get("ui", False)),
    ]
    
    all_passed = True
    for step_name, passed in steps:
        status = "✅" if passed else "⚠️"
        print(f"{status} {step_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 70)
    
    if all_passed:
        print("🎉 ALL CHECKS PASSED!")
        print("\nYour Sentinel project is ready to use!")
        print("\nNext steps:")
        print("1. Start the API: cd sentinel_service && python main.py")
        print("2. Start the UI: cd sentinel_ui && npm install && npm run dev")
        print("3. Visit http://localhost:3000 to use the dashboard")
    else:
        print("⚠️  SOME CHECKS FAILED")
        print("\nThis is normal if:")
        print("- Docker Desktop is not running (start it and run again)")
        print("- Neo4j is not configured yet (check .env file)")
        print("- You haven't installed npm packages yet")
        print("\nRefer to SETUP_GUIDE.md for detailed instructions")
    
    print("=" * 70)

def main():
    """Run all verification steps."""
    print("=" * 70)
    print("SENTINEL PROJECT - COMPLETE SETUP VERIFICATION")
    print("=" * 70)
    
    results = {}
    
    # Step 1: Infrastructure
    results["infrastructure"] = start_infrastructure()
    
    # Step 2: Package installation
    results["package"] = install_package()
    
    # Step 3: Tests
    results["tests"] = run_tests()
    
    # Step 4: API service
    results["api"] = check_api_service()
    
    # Step 5: UI
    results["ui"] = check_ui()
    
    # Print summary
    print_summary(results)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
