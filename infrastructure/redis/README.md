# Redis Integration Guide

This guide explains how to integrate Redis caching into your LLM chatbot application for improved performance and reduced API costs.

## 🚀 Quick Start

### 1. Start Redis Container

```python
from infrastructure.orchestrator.activities.common_activity.redis_activity import start_redis_container

# Start Redis container
success = await start_redis_container("my-service")
print(f"Redis started: {success}")
```

### 2. Configure Redis (Optional)

```python
from infrastructure.orchestrator.activities.common_activity.configure_redis_activity import configure_redis_container

# Configure Redis with custom settings
await configure_redis_container("my-service")
```

### 3. Use Redis in Your Application

```python
from service.redis_service import initialize_redis, get_redis_service

# Initialize Redis connection
await initialize_redis(
    host="localhost",
    port=6379,
    db=0,
    password=None  # Set for production
)

# Get Redis service instance
redis_service = get_redis_service()

# Cache data
await redis_service.set_cache("user:123", {"name": "John", "email": "john@example.com"})

# Retrieve cached data
user_data = await redis_service.get_cache("user:123")
```

## 🏗️ Architecture Overview

### Redis Service Components

#### 1. **Container Management** (`redis_activity.py`)
- **Purpose**: Docker container lifecycle management for Redis
- **Features**: Start, stop, status monitoring with health checks
- **Configuration**: Ports (6379), volumes, memory limits, persistence

#### 2. **Configuration Management** (`configure_redis_activity.py`)
- **Purpose**: Redis configuration file generation and updates
- **Features**: Custom memory policies, security settings, performance tuning
- **Validation**: Configuration syntax checking

#### 3. **Service Layer** (`redis_service.py`)
- **Purpose**: High-level Redis operations with caching logic
- **Features**: Connection management, telemetry integration, error handling
- **Caching**: TTL support, JSON serialization, cache statistics

#### 4. **Application Integration** (`generate_text_with_cache.py`)
- **Purpose**: LLM response caching with Redis
- **Features**: Cache hit/miss tracking, performance metrics, cost optimization

## 📁 Configuration Files

### Redis Configuration (`redis.conf`)
```ini
# Network
bind 0.0.0.0
port 6379
timeout 0

# Memory management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence
appendonly yes
save 900 1
save 300 10

# Security (uncomment for production)
# requirepass your_secure_password

# Performance
tcp-keepalive 300
```

## 🚀 Usage Examples

### Basic Redis Operations

```python
from service.redis_service import get_redis_service

# Get Redis service
redis_service = get_redis_service()

# Connect to Redis
await redis_service.connect()

# Basic operations
await redis_service.set_cache("key", "value", ttl=3600)
value = await redis_service.get_cache("key")
await redis_service.delete_cache("key")

# Check connection status
if redis_service.is_connected():
    print("Redis is connected and ready")
```

### LLM Response Caching

```python
from service.ai_proxy_service.core.usecases.generate_text_with_cache import generate_text_with_cache

# Generate text with caching
response = await generate_text_with_cache(
    request=llm_request,
    provider=openai_provider,
    default_max_tokens=1000,
    default_temperature=0.7,
    use_cache=True,
    cache_ttl=3600  # 1 hour cache
)
```

### Cache Management

```python
# Clear all LLM cache
from service.ai_proxy_service.core.usecases.generate_text_with_cache import clear_llm_cache
cleared_count = await clear_llm_cache("llm_response:*")

# Get cache statistics
from service.ai_proxy_service.core.usecases.generate_text_with_cache import get_cache_stats
stats = await get_cache_stats()
print(f"Cache hit ratio: {stats['cache_stats']['cache_hit_ratio']}")
```

## 📊 Telemetry Integration

### Automatic Metrics Collection

When Redis is integrated with OpenTelemetry, the following metrics are automatically collected:

- **Connection Status**: Connected/disconnected state
- **Operation Count**: Total Redis operations by type
- **Operation Duration**: Response time for Redis operations
- **Cache Performance**: Hit/miss ratios and cache efficiency

### Custom Metrics Example

```python
from service.redis_service import get_redis_service

redis_service = get_redis_service()

# Operations are automatically instrumented
await redis_service.set_cache("user:123", {"name": "John"})
user_data = await redis_service.get_cache("user:123")

# Metrics automatically recorded:
# - redis_operations_total{operation="set", success="true"}
# - redis_operations_total{operation="get", success="true"}
# - redis_operation_duration_seconds{operation="set"}
# - redis_connection_status{status="connected"}
```

## 🔧 Activities

### Container Management Activities

#### `redis_activity.py`
```python
# Start Redis container
await start_redis_container("my-service")

# Stop Redis container
await stop_redis_container("my-service")

# Get Redis status
status = await get_redis_status("my-service")
```

#### `configure_redis_activity.py`
```python
# Configure Redis settings
await configure_redis_container("my-service")

# Validate configuration
validation = await validate_redis_config("my-service")

# Update configuration
await update_redis_config("my-service", {
    "maxmemory": "512mb",
    "maxmemory_policy": "allkeys-lfu"
})
```

## 📈 Performance Optimization

### 1. **Memory Management**
```python
# Configure Redis memory limits
CONFIG = {
    "environment": {
        "REDIS_MAXMEMORY": "512mb",  # Adjust based on your needs
        "REDIS_MAXMEMORY_POLICY": "allkeys-lru",  # LRU eviction
    }
}
```

### 2. **Persistence Settings**
```python
# Enable append-only file for durability
"appendonly": "yes",
"appendfsync": "everysec",  # Balance performance and durability

# Snapshot settings
"save": ["900 1", "300 10", "60 10000"]  # Save conditions
```

### 3. **Connection Pooling**
```python
# Redis service automatically configures connection pooling
redis_service = RedisService(
    max_connections=20,  # Adjust based on load
    socket_timeout=5,
    retry_on_timeout=True,
)
```

## 🔍 Monitoring and Health Checks

### Redis Health Monitoring

```python
# Check Redis health
status = await get_redis_status("my-service")
print(f"Redis status: {status['status']}")
print(f"Connection URL: {status['connection_url']}")

# Get detailed cache information
cache_info = await get_cache_stats()
print(f"Cache hit ratio: {cache_info['cache_stats']['cache_hit_ratio']}")
```

### Observability Integration

Redis metrics are automatically integrated with your observability stack:

- **Prometheus**: Redis metrics exported via OpenTelemetry
- **Grafana**: Redis dashboards with performance metrics
- **Jaeger**: Redis operation traces in distributed tracing
- **Loki**: Structured logs for Redis operations

## 🎯 Production Considerations

### 1. **Security Configuration**

```python
# Enable authentication for production
await update_redis_config("my-service", {
    "password": "your_secure_password_here"
})

# Disable dangerous commands
# requirepass and rename-command configurations
```

### 2. **Performance Tuning**

```python
# Adjust for high-load scenarios
CONFIG = {
    "environment": {
        "REDIS_MAXMEMORY": "1gb",
        "REDIS_MAXMEMORY_POLICY": "allkeys-lfu",  # Frequency-based eviction
    },
    "resources": {
        "mem_limit": "1g",  # Increase memory limit
        "cpus": 1.0,       # Increase CPU allocation
    }
}
```

### 3. **Backup and Recovery**

```python
# Enable Redis persistence
"appendonly": "yes",      # Append-only file
"save": ["900 1"],        # RDB snapshots

# Volume configuration for data persistence
"volumes": {
    "redis-data": {"bind": "/data", "mode": "rw"},
}
```

## 🧪 Testing

### 1. **Unit Tests**

```python
# Test Redis service
from service.redis_service import RedisService

async def test_redis():
    redis_service = RedisService()
    await redis_service.connect()

    # Test basic operations
    await redis_service.set_cache("test_key", "test_value")
    value = await redis_service.get_cache("test_key")
    assert value == "test_value"

    await redis_service.disconnect()
```

### 2. **Integration Tests**

```python
# Test LLM caching
from service.ai_proxy_service.core.usecases.generate_text_with_cache import generate_text_with_cache

async def test_llm_caching():
    response1 = await generate_text_with_cache(request, provider, use_cache=True)
    response2 = await generate_text_with_cache(request, provider, use_cache=True)

    # Should be cache hit for second request
    assert response1.text == response2.text
    assert response2.cached == True
```

## 📚 Advanced Usage

### Custom Cache Keys

```python
def generate_custom_cache_key(request, provider, **kwargs):
    """Generate custom cache key based on your requirements"""
    import hashlib

    key_data = {
        "provider": provider.__class__.__name__,
        "model": request.model,
        "prompt_hash": hashlib.md5(request.prompt.encode()).hexdigest(),
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
    }

    key_string = str(sorted(key_data.items()))
    return hashlib.md5(key_string.encode()).hexdigest()
```

### Cache Invalidation Strategies

```python
# Time-based expiration (TTL)
await redis_service.set_cache("user_data", data, ttl=3600)  # 1 hour

# Pattern-based clearing
await clear_llm_cache("llm_response:*")  # Clear all LLM responses

# Manual deletion
await redis_service.delete_cache("specific_key")
```

### Redis Clustering (Advanced)

```python
# For high availability and scaling
from service.redis_service import RedisClusterService

redis_cluster = RedisClusterService(
    startup_nodes=[
        {"host": "redis-node-1", "port": 6379},
        {"host": "redis-node-2", "port": 6379},
        {"host": "redis-node-3", "port": 6379},
    ]
)
```

## 🚨 Troubleshooting

### Common Issues

#### 1. **Connection Refused**
```bash
# Check if Redis container is running
docker ps | grep redis

# Check Redis logs
docker logs redis-development

# Test connection manually
redis-cli ping
```

#### 2. **Memory Issues**
```bash
# Check Redis memory usage
redis-cli info memory

# Adjust memory limits in configuration
await update_redis_config("my-service", {"maxmemory": "1gb"})
```

#### 3. **Cache Misses**
```python
# Check cache statistics
stats = await get_cache_stats()
print(f"Hit ratio: {stats['cache_stats']['cache_hit_ratio']}")

# Verify cache key generation
print(f"Cache key: {generate_cache_key(request, provider)}")
```

### Performance Monitoring

```python
# Monitor Redis performance
info = await redis_service.get_cache_info()
print(f"Connected clients: {info['redis_info']['connected_clients']}")
print(f"Memory usage: {info['redis_info']['used_memory_human']}")
print(f"Keyspace hits: {info['redis_info']['keyspace_hits']}")
print(f"Keyspace misses: {info['redis_info']['keyspace_misses']}")
```

## 📞 Support

For Redis integration issues:

1. **Check container status**: `docker logs redis-development`
2. **Verify connection**: `redis-cli ping`
3. **Review metrics**: Check Prometheus/Grafana dashboards
4. **Check configuration**: Validate Redis config syntax
5. **Monitor performance**: Use Redis CLI info command

## 🎉 Summary

**Redis integration provides:**

✅ **High-Performance Caching** for LLM responses and application data  
✅ **Cost Optimization** by reducing redundant LLM API calls  
✅ **Graceful Degradation** when Redis is unavailable  
✅ **Comprehensive Monitoring** with OpenTelemetry integration  
✅ **Production Ready** with proper security and persistence  

Your LLM chatbot now has enterprise-grade caching capabilities that will significantly improve performance and reduce operational costs! 🚀
