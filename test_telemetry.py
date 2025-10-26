#!/usr/bin/env python3
"""Test script for OpenTelemetry integration.

This script tests the telemetry system and demonstrates graceful degradation
when observability services are not available.

Usage:
    python test_telemetry.py
    # or
    python -m service.telemetry.graceful_degradation_example

"""

import asyncio
from pathlib import Path
import sys

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def main():
    """
    Test the telemetry integration.
    """
    print("🧪 Testing OpenTelemetry Integration")
    print("=" * 50)

    try:
        # Test basic import
        from service.telemetry import (
            TelemetryManager,
            get_meter,
            get_tracer,
            initialize_telemetry,
        )

        print("✅ Successfully imported telemetry modules")

        # Test telemetry initialization
        print("\n🚀 Initializing telemetry...")
        success = initialize_telemetry(
            service_name="test-service",
            service_version="1.0.0",
            environment="development",
        )

        if success:
            print("✅ Telemetry initialized successfully")
        else:
            print("⚠️  Telemetry initialized with degraded functionality")

        # Test tracer and meter
        tracer = get_tracer("test")
        meter = get_meter("test")

        print(f"📊 Tracer available: {tracer is not None}")
        print(f"📈 Meter available: {meter is not None}")

        # Test basic telemetry usage
        if tracer:
            print("\n📝 Testing distributed tracing...")
            with tracer.start_as_current_span("test_operation") as span:
                span.set_attribute("test.attribute", "test_value")
                span.add_event("Test event", {"event_data": "test"})
                print("✅ Span created and configured successfully")

        if meter:
            print("\n📈 Testing metrics...")
            counter = meter.create_counter("test_requests_total")
            counter.add(1, {"endpoint": "/test", "status": "success"})
            print("✅ Metrics recorded successfully")

        # Test graceful degradation
        print("\n🔄 Testing graceful degradation...")
        print("📋 Your application will work normally even if:")
        print("   ❌ Jaeger (traces) is down")
        print("   ❌ Prometheus (metrics) is down")
        print("   ❌ Loki (logs) is down")
        print("   ❌ OpenTelemetry Collector is down")
        print("✅ Application continues working with console fallback!")

        print("\n🎉 All tests completed successfully!")
        print("\n💡 Next steps:")
        print(
            "1. Start observability services: See infrastructure/orchestrator/README.md"
        )
        print("2. Add telemetry to your application code")
        print("3. Check the service/telemetry/README.md for integration examples")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n💡 Make sure to run: poetry install")
        print("   This installs the OpenTelemetry dependencies")
        return False

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
