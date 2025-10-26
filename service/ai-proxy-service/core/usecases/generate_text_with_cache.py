"""
Example: Redis-Cached LLM Text Generation

This example shows how to integrate Redis caching with LLM text generation
to improve performance and reduce API costs.
"""

import logging
import time
from typing import Optional

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from ..domain.models import LLMRequest, LLMResponse
from ..ports.llm_provider import LLMProviderPort
from ...telemetry import get_tracer, get_meter
from ...redis_service import get_redis_service

# Get telemetry instances
tracer = get_tracer(__name__)
meter = get_meter(__name__)

# Set up metrics (if available)
cache_hits_counter = None
cache_misses_counter = None
llm_requests_saved_counter = None

if meter:
    # Cache metrics
    cache_hits_counter = meter.create_counter(
        name="cache_hits_total",
        description="Total number of cache hits",
        unit="1"
    )

    cache_misses_counter = meter.create_counter(
        name="cache_misses_total",
        description="Total number of cache misses",
        unit="1"
    )

    llm_requests_saved_counter = meter.create_counter(
        name="llm_requests_saved_total",
        description="Total number of LLM requests saved by caching",
        unit="1"
    )


async def generate_text_with_cache(
    request: LLMRequest,
    provider: LLMProviderPort,
    default_max_tokens: int,
    default_temperature: float,
    use_cache: bool = True,
    cache_ttl: Optional[int] = None,
) -> LLMResponse:
    """
    Generate text using LLM with Redis caching for performance optimization

    Args:
        request: LLM request with prompt and parameters
        provider: LLM provider to use for generation
        default_max_tokens: Default max tokens if not specified in request
        default_temperature: Default temperature if not specified in request
        use_cache: Whether to use caching (default: True)
        cache_ttl: Cache time-to-live in seconds (default: 1 hour)

    Returns:
        LLMResponse with generated text and metadata
    """
    start_time = time.time()

    # Create cache key based on request parameters
    cache_key = generate_cache_key(request, provider, default_max_tokens, default_temperature)

    # Check cache first (if caching enabled)
    if use_cache:
        cached_response = await get_cached_response(cache_key)
        if cached_response:
            if cache_hits_counter:
                cache_hits_counter.add(1, {"provider": provider.__class__.__name__})

            logging.info("Cache hit - returning cached response", extra={
                "cache_key": cache_key,
                "provider": provider.__class__.__name__,
            })
            return cached_response

    # Cache miss - generate new response
    if cache_misses_counter:
        cache_misses_counter.add(1, {"provider": provider.__class__.__name__})

    # Generate response with telemetry
    if tracer:
        with tracer.start_as_current_span(
            "llm.generate_with_cache",
            attributes={
                "llm.provider": provider.__class__.__name__,
                "llm.model": getattr(request, 'model', 'unknown'),
                "cache.enabled": use_cache,
                "cache.key": cache_key,
                "user.id": getattr(request, 'user_id', 'anonymous'),
            }
        ) as span:
            return await _generate_with_cache_and_tracing(
                request, provider, default_max_tokens, default_temperature,
                cache_key, start_time, span, use_cache, cache_ttl
            )
    else:
        return await _generate_with_cache_fallback(
            request, provider, default_max_tokens, default_temperature,
            cache_key, start_time, use_cache, cache_ttl
        )


def generate_cache_key(
    request: LLMRequest,
    provider: LLMProviderPort,
    default_max_tokens: int,
    default_temperature: float,
) -> str:
    """Generate a cache key based on request parameters"""
    # Create deterministic key based on request parameters
    key_data = {
        "provider": provider.__class__.__name__,
        "model": getattr(request, 'model', 'default'),
        "prompt": request.prompt,
        "max_tokens": request.max_tokens or default_max_tokens,
        "temperature": request.temperature or default_temperature,
    }

    # Create a hash of the key data for a fixed-length key
    import hashlib
    key_string = str(sorted(key_data.items()))
    cache_key = hashlib.md5(key_string.encode()).hexdigest()

    return f"llm_response:{cache_key}"


async def get_cached_response(cache_key: str) -> Optional[LLMResponse]:
    """Get cached LLM response from Redis"""
    redis_service = get_redis_service()

    if not redis_service.is_connected():
        await redis_service.connect()

    cached_data = await redis_service.get_cache(cache_key)

    if cached_data:
        try:
            # Deserialize cached response
            response_data = json.loads(cached_data)
            response = LLMResponse(
                text=response_data["text"],
                model=response_data["model"],
                tokens=response_data.get("tokens", 0),
                usage=response_data.get("usage", {}),
                cached=True,
                cache_timestamp=response_data.get("timestamp"),
            )
            return response
        except (json.JSONDecodeError, KeyError) as e:
            logging.warning(f"Failed to deserialize cached response: {e}")
            # Remove corrupted cache entry
            await redis_service.delete_cache(cache_key)
            return None

    return None


async def _generate_with_cache_and_tracing(
    request: LLMRequest,
    provider: LLMProviderPort,
    default_max_tokens: int,
    default_temperature: float,
    cache_key: str,
    start_time: float,
    span: trace.Span,
    use_cache: bool,
    cache_ttl: Optional[int],
) -> LLMResponse:
    """Generate response with full telemetry support"""

    try:
        # Add cache miss event
        span.add_event("Cache miss - generating new response", {
            "cache_key": cache_key,
            "provider": provider.__class__.__name__,
        })

        # Generate the response
        response = await provider.generate(
            prompt=request.prompt,
            max_tokens=request.max_tokens or default_max_tokens,
            temperature=request.temperature or default_temperature,
        )

        # Calculate total duration
        duration = time.time() - start_time

        # Cache the response (if caching enabled)
        if use_cache:
            await cache_response(cache_key, response, cache_ttl or 3600)

            if llm_requests_saved_counter:
                llm_requests_saved_counter.add(1, {
                    "provider": provider.__class__.__name__,
                    "cache_ttl": cache_ttl or 3600,
                })

        # Add success events
        span.add_event("Response generated and cached", {
            "response_length": len(response.text),
            "duration_seconds": duration,
            "tokens_used": getattr(response, 'tokens', 0),
            "cached": use_cache,
        })

        span.set_attribute("response.length", len(response.text))
        span.set_attribute("response.tokens", getattr(response, 'tokens', 0))
        span.set_attribute("response.duration_seconds", duration)
        span.set_attribute("cache.enabled", use_cache)
        span.set_status(Status(StatusCode.OK))

        # Record metrics
        if meter:
            request_counter = meter.create_counter("llm_requests_with_cache_total")
            request_counter.add(1, {
                "provider": provider.__class__.__name__,
                "cache_enabled": "true" if use_cache else "false",
                "status": "success"
            })

            duration_histogram = meter.create_histogram("llm_request_with_cache_duration_seconds")
            duration_histogram.record(duration, {
                "provider": provider.__class__.__name__,
                "cache_enabled": "true" if use_cache else "false",
            })

        # Structured logging
        logging.info("LLM response generated with caching", extra={
            "provider": provider.__class__.__name__,
            "model": getattr(request, 'model', 'unknown'),
            "duration_seconds": duration,
            "cache_enabled": use_cache,
            "cache_key": cache_key,
            "tokens_used": getattr(response, 'tokens', 0),
            "response_length": len(response.text),
        })

        return response

    except Exception as e:
        duration = time.time() - start_time

        # Add error event
        span.add_event("Response generation failed", {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "duration_seconds": duration,
        })
        span.set_status(Status(StatusCode.ERROR, str(e)))

        # Record error metrics
        if meter:
            request_counter = meter.create_counter("llm_requests_with_cache_total")
            request_counter.add(1, {
                "provider": provider.__class__.__name__,
                "cache_enabled": "true" if use_cache else "false",
                "status": "error"
            })

        # Error logging
        logging.error("LLM response generation failed", extra={
            "provider": provider.__class__.__name__,
            "model": getattr(request, 'model', 'unknown'),
            "duration_seconds": duration,
            "cache_enabled": use_cache,
            "error_type": type(e).__name__,
        }, exc_info=True)

        raise


async def _generate_with_cache_fallback(
    request: LLMRequest,
    provider: LLMProviderPort,
    default_max_tokens: int,
    default_temperature: float,
    cache_key: str,
    start_time: float,
    use_cache: bool,
    cache_ttl: Optional[int],
) -> LLMResponse:
    """Generate response without telemetry"""

    try:
        # Generate the response
        response = await provider.generate(
            prompt=request.prompt,
            max_tokens=request.max_tokens or default_max_tokens,
            temperature=request.temperature or default_temperature,
        )

        # Calculate duration
        duration = time.time() - start_time

        # Cache the response (if caching enabled)
        if use_cache:
            await cache_response(cache_key, response, cache_ttl or 3600)

        # Simple logging
        logging.info("LLM response generated with caching", extra={
            "provider": provider.__class__.__name__,
            "duration_seconds": duration,
            "cache_enabled": use_cache,
        })

        return response

    except Exception as e:
        duration = time.time() - start_time

        logging.error("LLM response generation failed", extra={
            "provider": provider.__class__.__name__,
            "duration_seconds": duration,
            "cache_enabled": use_cache,
            "error_type": type(e).__name__,
        }, exc_info=True)

        raise


async def cache_response(cache_key: str, response: LLMResponse, ttl: int) -> bool:
    """Cache LLM response in Redis"""
    redis_service = get_redis_service()

    if not redis_service.is_connected():
        await redis_service.connect()

    try:
        # Serialize response for caching
        response_data = {
            "text": response.text,
            "model": getattr(response, 'model', 'unknown'),
            "tokens": getattr(response, 'tokens', 0),
            "usage": getattr(response, 'usage', {}),
            "timestamp": time.time(),
        }

        return await redis_service.set_cache(cache_key, response_data, ttl)

    except Exception as e:
        logging.error(f"Failed to cache response: {e}")
        return False


async def clear_llm_cache(pattern: str = "llm_response:*") -> int:
    """Clear LLM response cache"""
    redis_service = get_redis_service()

    if not redis_service.is_connected():
        await redis_service.connect()

    cleared_count = await redis_service.clear_cache(pattern)
    logging.info(f"Cleared {cleared_count} LLM cache entries")

    return cleared_count


async def get_cache_stats() -> dict:
    """Get cache statistics and performance metrics"""
    redis_service = get_redis_service()

    if not redis_service.is_connected():
        await redis_service.connect()

    cache_info = await redis_service.get_cache_info()

    # Add cache-specific metrics
    cache_info.update({
        "cache_stats": {
            "total_llm_responses_cached": await get_cache_count("llm_response:*"),
            "cache_hit_ratio": await calculate_cache_hit_ratio(),
        }
    })

    return cache_info


async def get_cache_count(pattern: str = "*") -> int:
    """Get count of cache entries matching pattern"""
    redis_service = get_redis_service()

    if not redis_service.is_connected():
        await redis_service.connect()

    try:
        full_pattern = f"{redis_service.cache_prefix}{pattern}"
        keys = redis_service.client.keys(full_pattern)
        return len(keys) if keys else 0
    except Exception as e:
        logging.error(f"Failed to get cache count: {e}")
        return 0


async def calculate_cache_hit_ratio() -> float:
    """Calculate cache hit ratio (simplified version)"""
    # This would need more sophisticated tracking in a real implementation
    # For now, return a placeholder value
    return 0.75  # 75% hit ratio as example
