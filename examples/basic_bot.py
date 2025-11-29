"""
Quick Start Script for Sentinel Phase 1

This script helps you get started with the Sentinel infrastructure.
"""

import os
import sys
from pathlib import Path


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")


def check_docker() -> bool:
    """Check if Docker is installed and running."""
    import subprocess
    
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ Docker found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker not found. Please install Docker Desktop.")
        return False


def check_docker_compose() -> bool:
    """Check if Docker Compose is available."""
    import subprocess
    
    try:
        result = subprocess.run(
            ["docker-compose", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ Docker Compose found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker Compose not found. Please install Docker Compose.")
        return False


def create_env_file() -> None:
    """Create .env file from template if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path("config/.env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
    else:
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print("✅ Created .env file from template")
            print("⚠️  Please edit .env and add your FIRECRAWL_API_KEY")
        else:
            print("❌ config/.env.example not found")


def start_infrastructure() -> bool:
    """Start Docker containers."""
    import subprocess
    
    print("Starting Docker containers...")
    try:
        subprocess.run(
            ["docker-compose", "up", "-d"],
            check=True
        )
        print("✅ Docker containers started")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start containers: {e}")
        return False


def check_infrastructure() -> None:
    """Check if infrastructure is running."""
    import subprocess
    import time
    
    print("\nWaiting for services to be ready...")
    time.sleep(5)
    
    try:
        result = subprocess.run(
            ["docker-compose", "ps"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
    except subprocess.CalledProcessError:
        print("❌ Could not check container status")


def install_dependencies() -> bool:
    """Install Python dependencies."""
    import subprocess
    
    print("Installing Python dependencies...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True
        )
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def run_tests() -> None:
    """Run Phase 1 tests."""
    import subprocess
    
    print("\nRunning Phase 1 tests (excluding integration tests)...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_phase1.py", "-v", "-m", "not integration"],
            check=True
        )
        print("✅ Tests passed!")
    except subprocess.CalledProcessError:
        print("⚠️  Some tests failed. Check the output above.")


def print_next_steps() -> None:
    """Print next steps for the user."""
    print_header("Setup Complete!")
    
    print("🎉 Phase 1 infrastructure is ready!\n")
    print("Next steps:")
    print("1. Edit .env and add your FIRECRAWL_API_KEY")
    print("2. Access Neo4j Browser: http://localhost:7474")
    print("   - Username: neo4j")
    print("   - Password: password")
    print("3. Run integration tests:")
    print("   pytest tests/test_phase1.py -v")
    print("4. Try the scraper:")
    print("   python -c 'from sentinel_core import SentinelScraper'")
    print("\n📚 See PHASE1_COMPLETE.md for detailed documentation")
    print("\n🐛 Troubleshooting:")
    print("   - View logs: docker-compose logs -f")
    print("   - Restart: docker-compose restart")
    print("   - Stop: docker-compose down")


def main() -> None:
    """Main setup function."""
    print_header("Sentinel Phase 1 Quick Start")
    
    # Check prerequisites
    print("Checking prerequisites...\n")
    if not check_docker():
        return
    if not check_docker_compose():
        return
    
    # Create .env file
    print_header("Environment Setup")
    create_env_file()
    
    # Start infrastructure
    print_header("Starting Infrastructure")
    if not start_infrastructure():
        return
    
    check_infrastructure()
    
    # Install dependencies
    print_header("Installing Dependencies")
    if not install_dependencies():
        return
    
    # Run tests
    print_header("Running Tests")
    run_tests()
    
    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
