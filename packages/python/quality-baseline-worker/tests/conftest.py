import sys
from pathlib import Path

# Add src/ folder to sys.path so tests can resolve local modules cleanly
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
