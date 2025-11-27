# Python Observability Client
__version__ = "1.0.0"

from .client import (
    ObservabilityClient,
    init_observability,
    get_client,
)

__all__ = [
    "ObservabilityClient",
    "init_observability",
    "get_client",
]
