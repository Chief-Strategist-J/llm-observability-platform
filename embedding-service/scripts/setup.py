"""Setup script for development."""
import subprocess
import sys

def install_dependencies():
    """Install Python dependencies."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def run_tests():
    """Run test suite."""
    subprocess.check_call([sys.executable, "-m", "pytest", "tests/"])

if __name__ == "__main__":
    print("Setting up embedding service...")
    install_dependencies()
    print("Setup complete!")
