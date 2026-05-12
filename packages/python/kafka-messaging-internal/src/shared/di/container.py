"""Dependency Injection Container."""

import os
from typing import Dict, Type, TypeVar, Optional
from dataclasses import dataclass

T = TypeVar('T')


@dataclass
class DIConfig:
    """DI Configuration from environment"""
    database_type: str
    schema_registry_url: str
    kafka_bootstrap_servers: str
    redis_host: Optional[str] = None
    redis_port: Optional[int] = None


class DIContainer:
    """Simple dependency injection container"""
    
    def __init__(self):
        self._services: Dict[Type, object] = {}
        self._singletons: Dict[Type, object] = {}
        self._config = self._load_config()
    
    def _load_config(self) -> DIConfig:
        """Load configuration from environment"""
        return DIConfig(
            database_type=os.getenv('DATABASE_TYPE', 'postgresql'),
            schema_registry_url=os.getenv('SCHEMA_REGISTRY_URL', 'http://localhost:8081'),
            kafka_bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            redis_host=os.getenv('REDIS_HOST'),
            redis_port=int(os.getenv('REDIS_PORT', '6379')) if os.getenv('REDIS_PORT') else None
        )
    
    def register_singleton(self, interface: Type[T], implementation: T):
        """Register a singleton service"""
        self._singletons[interface] = implementation
    
    def register_transient(self, interface: Type[T], factory):
        """Register a transient service (created each time)"""
        self._services[interface] = factory
    
    def get(self, interface: Type[T]) -> T:
        """Get service instance"""
        if interface in self._singletons:
            return self._singletons[interface]
        
        if interface in self._services:
            return self._services[interface](self._config)
        
        raise ValueError(f"Service {interface} not registered")
    
    def get_config(self) -> DIConfig:
        """Get configuration"""
        return self._config


# Global container instance
_container = DIContainer()


def get_container() -> DIContainer:
    """Get global DI container"""
    return _container


def register_services():
    """Register all services with container"""
    # This would be called during application startup
    # Adapters would be registered based on configuration
    pass
