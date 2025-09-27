"""Utility functions."""
import logging

def setup_logging():
    """Setup application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

def validate_vector_dim(vector, expected_dim):
    """Validate vector dimensions."""
    return len(vector) == expected_dim
