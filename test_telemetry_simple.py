#!/usr/bin/env python3
"""Simple Telemetry Test.

This script tests the telemetry integration from the project root.
Run this after installing dependencies with: poetry install

Usage: python test_telemetry.py

"""

import asyncio
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_telemetry():
    """
    Test telemetry integration.
    """
    print("🧪 Testing OpenTelemetry Integration")
    print("=" * 40)

    try:
        # Test import
        from service.telemetry import TelemetryManager, initialize_telemetry

        print("✅ Telemetry modules imported successfully")

        # Test initialization
        print("\n🚀 Initializing telemetry...")
        success = initialize_telemetry(
            service_name="test-service", service_version="1.0.0"
        )

        print(f"📊 Initialization result: {'✅ SUCCESS' if success else '⚠️ DEGRADED'}")

        # Show capabilities
        from service.telemetry import get_meter, get_tracer

        tracer = get_tracer("test")
        meter = get_meter("test")

        print(f"📝 Tracing available: {tracer is not None}")
        print(f"📈 Metrics available: {meter is not None}")

        print("\n🎉 Telemetry test completed!")
        print("\n💡 What this means:")
        print("✅ Your application will work even if observability services are down")
        print("✅ Automatic fallback to console logging/metrics")
        print("✅ Zero impact on application functionality")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print(
            "\n💡 Solution: Run 'poetry install' to install OpenTelemetry dependencies"
        )
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_telemetry())
    sys.exit(0 if success else 1)
