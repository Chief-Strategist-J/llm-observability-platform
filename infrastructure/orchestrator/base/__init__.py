"""Orchestrator base package.

This package contains the core components for container orchestration,
including protocols, base classes, and common utilities.
"""

"""
Base container management classes for orchestration.
Supports both legacy ContainerConfig and new YAML-based configuration.
"""

from .base_container_activity import (
    YAMLBaseService,
    YAMLContainerConfig,
    YAMLContainerManager,
    YAMLConfigLoader,
    ContainerState,
    BaseContainerManager,
)

from .logql_logger import (
    LogQLLogger,
    trace_operation,
)

__all__ = [
    "YAMLBaseService",
    "YAMLContainerConfig",
    "YAMLContainerManager",
    "YAMLConfigLoader",
    "ContainerState",
    "BaseContainerManager",
    "KubernetesBaseService",
    "KubernetesConfig",
    "KubernetesManager",
    "BaseKubernetesManager",
    "LogQLLogger",
    "trace_operation",
]

