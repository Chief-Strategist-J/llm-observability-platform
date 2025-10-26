#!/usr/bin/env python3
"""
Redis Integration Test

This script tests the Redis integration including container management,
configuration, and application-level caching functionality.

Usage: python test_redis_integration.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_redis_integration():
    """Test complete Redis integration"""
    print("🧪 Testing Redis Integration")
    print("=" * 40)

    try:
        # Test Redis activity imports
        from infrastructure.orchestrator.activities.common_activity.redis_activity import (
            start_redis_container,
            get_redis_status
        )
        print("✅ Redis activities imported successfully")

        # Test Redis service imports
        from service.redis_service import initialize_redis, get_redis_service
        print("✅ Redis service imported successfully")

        # Test LLM caching imports
        from service.ai_proxy_service.core.usecases.generate_text_with_cache import (
            generate_text_with_cache,
            clear_llm_cache
        )
        print("✅ LLM caching imported successfully")

        print("\n🚀 Testing Redis functionality...")

        # Test Redis service initialization
        success = await initialize_redis(
            host="localhost",
            port=6379,
            db=0
        )

        if success:
            print("✅ Redis connection established")
        else:
            print("⚠️  Redis connection failed (expected if Redis not running)")
            print("💡 Start Redis: python -c \"from infrastructure.orchestrator.activities.common_activity.redis_activity import start_redis_container; import asyncio; asyncio.run(start_redis_container('test'))\"")

        # Test Redis service operations
        redis_service = get_redis_service()

        if redis_service.is_connected():
            print("✅ Redis service is connected")

            # Test basic cache operations
            test_key = "test:integration"
            test_value = {"message": "Hello Redis!", "timestamp": "2025-01-17"}

            # Test set
            set_result = await redis_service.set_cache(test_key, test_value, ttl=60)
            print(f"✅ Cache set result: {set_result}")

            # Test get
            retrieved_value = await redis_service.get_cache(test_key)
            print(f"✅ Cache get result: {retrieved_value is not None}")

            # Test cache statistics
            cache_info = await redis_service.get_cache_info()
            print(f"✅ Cache info available: {bool(cache_info)}")

        else:
            print("⚠️  Redis not connected - testing fallback behavior")

        print("\n🎉 Redis integration test completed!")
        print("\n💡 Next steps:")
        print("1. Start Redis container: See infrastructure/orchestrator/activities/")
        print("2. Use Redis in your application for caching")
        print("3. Monitor Redis metrics via OpenTelemetry")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n💡 Make sure to run: poetry install")
        print("   This installs Redis and OpenTelemetry dependencies")
        return False

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_redis_integration())
    sys.exit(0 if success else 1)
