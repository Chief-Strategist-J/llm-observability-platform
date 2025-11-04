"""Orchestrator base package.

This package contains the core components for container orchestration,
including protocols, base classes, and common utilities.
"""

from .base_container_activity import BaseContainerManager
from .base_container_activity import ContainerConfig

__all__ = [
    'BaseContainerManager',
    'ContainerConfig',
]
