import sys
# Clean sys.path of other workspace packages during alert-engine tests to prevent namespace conflicts
sys.path = [p for p in sys.path if "quality-engine" not in p and "nli-worker" not in p]
