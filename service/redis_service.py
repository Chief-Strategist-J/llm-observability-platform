"""
Redis Service Implementation for LLM Chatbot

This module provides Redis-based caching and data storage functionality
for the LLM chatbot application with proper instrumentation.
"""

import json
import logging
import time
from typing import Any, Dict, Optional

import redis
from opentelemetry import trace

from ...telemetry import get_tracer, get_meter

# Get telemetry instances
tracer = get_tracer(__name__)
meter = get_meter(__name__)

# Set up metrics (if available)
redis_operations_counter = None
redis_operation_duration = None
redis_connection_status = None

if meter:
    # Redis operation counter
    redis_operations_counter = meter.create_counter(
        name="redis_operations_total",
        description="Total number of Redis operations",
        unit="1"
    )

    # Redis operation duration histogram
    redis_operation_duration = meter.create_histogram(
        name="redis_operation_duration_seconds",
        description="Redis operation duration in seconds",
        unit="s"
    )

    # Redis connection status gauge
    redis_connection_status = meter.create_gauge(
        name="redis_connection_status",
        description="Redis connection status (1=connected, 0=disconnected)",
        unit="1"
    )


class RedisService:
    """Redis service with caching and telemetry"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        decode_responses: bool = True,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
        retry_on_timeout: bool = True,
        max_connections: int = 10,
    ):
        """Initialize Redis service

        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number
            password: Redis password (if required)
            decode_responses: Whether to decode responses as strings
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Connection timeout in seconds
            retry_on_timeout: Whether to retry on timeout
            max_connections: Maximum number of connections
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.decode_responses = decode_responses

        # Connection pool configuration
        self.pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=decode_responses,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            retry_on_timeout=retry_on_timeout,
            max_connections=max_connections,
            health_check_interval=30,
        )

        # Redis client
        self.client: Optional[redis.Redis] = None
        self._connected = False

        # Cache configuration
        self.default_ttl = 3600  # 1 hour default TTL
        self.cache_prefix = "llm_chatbot:"

        # Initialize telemetry
        self._initialize_telemetry()

    def _initialize_telemetry(self) -> None:
        """Initialize telemetry metrics"""
        if redis_connection_status:
            redis_connection_status.set(0, {"status": "disconnected"})

    def _record_operation(self, operation: str, success: bool = True, duration: float = 0.0) -> None:
        """Record Redis operation metrics"""
        if redis_operations_counter:
            redis_operations_counter.add(1, {
                "operation": operation,
                "success": "true" if success else "false"
            })

        if redis_operation_duration and duration > 0:
            redis_operation_duration.record(duration, {
                "operation": operation,
                "success": "true" if success else "false"
            })

    def _update_connection_status(self, connected: bool) -> None:
        """Update connection status metric"""
        if redis_connection_status:
            redis_connection_status.set(1 if connected else 0, {
                "status": "connected" if connected else "disconnected"
            })
        self._connected = connected

    async def connect(self) -> bool:
        """Connect to Redis server"""
        if tracer:
            with tracer.start_as_current_span(
                "redis.connect",
                attributes={
                    "redis.host": self.host,
                    "redis.port": self.port,
                    "redis.db": self.db,
                }
            ) as span:
                return await self._connect_with_tracing(span)
        else:
            return await self._connect_fallback()

    async def _connect_with_tracing(self, span: trace.Span) -> bool:
        """Connect to Redis with full tracing"""
        start_time = time.time()

        try:
            self.client = redis.Redis(connection_pool=self.pool)
            self.client.ping()

            duration = time.time() - start_time
            self._update_connection_status(True)

            span.add_event("Redis connection established", {
                "duration_seconds": duration,
                "host": self.host,
                "port": self.port,
            })
            span.set_attribute("connection.duration_seconds", duration)
            span.set_status(trace.Status(trace.StatusCode.OK))

            self._record_operation("connect", success=True, duration=duration)

            logging.info(f"Redis connected successfully to {self.host}:{self.port}")
            return True

        except Exception as e:
            duration = time.time() - start_time
            self._update_connection_status(False)

            span.add_event("Redis connection failed", {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "duration_seconds": duration,
            })
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))

            self._record_operation("connect", success=False, duration=duration)

            logging.error(f"Redis connection failed: {e}")
            return False

    async def _connect_fallback(self) -> bool:
        """Connect to Redis without tracing"""
        start_time = time.time()

        try:
            self.client = redis.Redis(connection_pool=self.pool)
            self.client.ping()

            duration = time.time() - start_time
            self._update_connection_status(True)

            self._record_operation("connect", success=True, duration=duration)

            logging.info(f"Redis connected successfully to {self.host}:{self.port}")
            return True

        except Exception as e:
            duration = time.time() - start_time
            self._update_connection_status(False)

            self._record_operation("connect", success=False, duration=duration)

            logging.error(f"Redis connection failed: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from Redis server"""
        operation = "disconnect"
        start_time = time.time()

        try:
            if self.client:
                self.client.connection_pool.disconnect()
                self.client = None

            self._update_connection_status(False)
            duration = time.time() - start_time

            self._record_operation(operation, success=True, duration=duration)

            logging.info("Redis disconnected successfully")

        except Exception as e:
            duration = time.time() - start_time

            self._record_operation(operation, success=False, duration=duration)

            logging.error(f"Redis disconnect failed: {e}")

    def is_connected(self) -> bool:
        """Check if Redis connection is active"""
        try:
            if self.client:
                self.client.ping()
                return True
            return False
        except Exception:
            self._update_connection_status(False)
            return False

    async def set_cache(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache with optional TTL"""
        operation = "set"
        start_time = time.time()
        full_key = f"{self.cache_prefix}{key}"

        if tracer:
            with tracer.start_as_current_span(
                "redis.set_cache",
                attributes={
                    "redis.key": full_key,
                    "redis.ttl": ttl or self.default_ttl,
                    "cache.operation": "set",
                }
            ) as span:
                return await self._set_cache_with_tracing(full_key, value, ttl, start_time, span)
        else:
            return await self._set_cache_fallback(full_key, value, ttl, start_time)

    async def _set_cache_with_tracing(self, key: str, value: Any, ttl: Optional[int], start_time: float, span: trace.Span) -> bool:
        """Set cache with full tracing"""
        try:
            serialized_value = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            result = self.client.set(key, serialized_value, ex=ttl or self.default_ttl)

            duration = time.time() - start_time
            success = result is True

            span.add_event("Cache set completed", {
                "success": success,
                "duration_seconds": duration,
                "ttl_seconds": ttl or self.default_ttl,
            })
            span.set_attribute("cache.duration_seconds", duration)

            if success:
                span.set_status(trace.Status(trace.StatusCode.OK))
            else:
                span.set_status(trace.Status(trace.StatusCode.ERROR, "Cache set failed"))

            self._record_operation("set", success=success, duration=duration)

            return success

        except Exception as e:
            duration = time.time() - start_time

            span.add_event("Cache set failed", {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "duration_seconds": duration,
            })
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))

            self._record_operation("set", success=False, duration=duration)

            logging.error(f"Redis set failed: {e}")
            return False

    async def _set_cache_fallback(self, key: str, value: Any, ttl: Optional[int], start_time: float) -> bool:
        """Set cache without tracing"""
        try:
            serialized_value = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            result = self.client.set(key, serialized_value, ex=ttl or self.default_ttl)

            duration = time.time() - start_time
            success = result is True

            self._record_operation("set", success=success, duration=duration)

            return success

        except Exception as e:
            duration = time.time() - start_time

            self._record_operation("set", success=False, duration=duration)

            logging.error(f"Redis set failed: {e}")
            return False

    async def get_cache(self, key: str) -> Optional[Any]:
        """Get a value from cache"""
        operation = "get"
        start_time = time.time()
        full_key = f"{self.cache_prefix}{key}"

        if tracer:
            with tracer.start_as_current_span(
                "redis.get_cache",
                attributes={
                    "redis.key": full_key,
                    "cache.operation": "get",
                }
            ) as span:
                return await self._get_cache_with_tracing(full_key, start_time, span)
        else:
            return await self._get_cache_fallback(full_key, start_time)

    async def _get_cache_with_tracing(self, key: str, start_time: float, span: trace.Span) -> Optional[Any]:
        """Get cache with full tracing"""
        try:
            value = self.client.get(key)

            duration = time.time() - start_time

            if value is not None:
                span.add_event("Cache hit", {
                    "duration_seconds": duration,
                })
                span.set_attribute("cache.result", "hit")
                span.set_status(trace.Status(trace.StatusCode.OK))

                # Try to deserialize JSON
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            else:
                span.add_event("Cache miss", {
                    "duration_seconds": duration,
                })
                span.set_attribute("cache.result", "miss")
                span.set_status(trace.Status(trace.StatusCode.OK))

            self._record_operation("get", success=True, duration=duration)

            return None

        except Exception as e:
            duration = time.time() - start_time

            span.add_event("Cache get failed", {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "duration_seconds": duration,
            })
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))

            self._record_operation("get", success=False, duration=duration)

            logging.error(f"Redis get failed: {e}")
            return None

    async def _get_cache_fallback(self, key: str, start_time: float) -> Optional[Any]:
        """Get cache without tracing"""
        try:
            value = self.client.get(key)

            duration = time.time() - start_time

            if value is not None:
                # Try to deserialize JSON
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value

            self._record_operation("get", success=True, duration=duration)

            return None

        except Exception as e:
            duration = time.time() - start_time

            self._record_operation("get", success=False, duration=duration)

            logging.error(f"Redis get failed: {e}")
            return None

    async def delete_cache(self, key: str) -> bool:
        """Delete a value from cache"""
        operation = "delete"
        start_time = time.time()
        full_key = f"{self.cache_prefix}{key}"

        try:
            result = self.client.delete(full_key)

            duration = time.time() - start_time
            success = result > 0

            self._record_operation(operation, success=success, duration=duration)

            return success

        except Exception as e:
            duration = time.time() - start_time

            self._record_operation(operation, success=False, duration=duration)

            logging.error(f"Redis delete failed: {e}")
            return False

    async def clear_cache(self, pattern: str = "*") -> int:
        """Clear cache entries matching pattern"""
        operation = "clear"
        start_time = time.time()
        full_pattern = f"{self.cache_prefix}{pattern}"

        try:
            keys = self.client.keys(full_pattern)
            if keys:
                result = self.client.delete(*keys)
            else:
                result = 0

            duration = time.time() - start_time
            success = True

            self._record_operation(operation, success=success, duration=duration)

            logging.info(f"Cleared {result} cache entries matching pattern: {pattern}")
            return result

        except Exception as e:
            duration = time.time() - start_time

            self._record_operation(operation, success=False, duration=duration)

            logging.error(f"Redis clear failed: {e}")
            return 0

    async def get_cache_info(self) -> Dict[str, Any]:
        """Get Redis cache information and statistics"""
        operation = "info"
        start_time = time.time()

        try:
            info = self.client.info()

            duration = time.time() - start_time

            self._record_operation(operation, success=True, duration=duration)

            return {
                "connected": self.is_connected(),
                "host": self.host,
                "port": self.port,
                "db": self.db,
                "redis_info": info,
                "cache_prefix": self.cache_prefix,
                "default_ttl": self.default_ttl,
            }

        except Exception as e:
            duration = time.time() - start_time

            self._record_operation(operation, success=False, duration=duration)

            logging.error(f"Redis info failed: {e}")
            return {
                "connected": False,
                "error": str(e),
                "host": self.host,
                "port": self.port,
            }


# Global Redis service instance
_redis_service: Optional[RedisService] = None


def get_redis_service() -> RedisService:
    """Get the global Redis service instance"""
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
    return _redis_service


async def initialize_redis(
    host: str = "localhost",
    port: int = 6379,
    db: int = 0,
    password: Optional[str] = None,
    **kwargs
) -> bool:
    """Initialize Redis service with connection"""
    global _redis_service
    _redis_service = RedisService(
        host=host,
        port=port,
        db=db,
        password=password,
        **kwargs
    )

    return await _redis_service.connect()


async def shutdown_redis() -> None:
    """Shutdown Redis service"""
    global _redis_service
    if _redis_service:
        await _redis_service.disconnect()
        _redis_service = None
