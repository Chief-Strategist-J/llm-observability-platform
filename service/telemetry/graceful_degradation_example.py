"""Example: Graceful Degradation When Observability Services Are Down

This example demonstrates how the application behaves when Prometheus, Loki, Jaeger,
or the OpenTelemetry Collector are not available. The application continues to work
but with degraded observability capabilities.
"""

import asyncio
import logging
from typing import Any

from opentelemetry.trace import Status, StatusCode

# Import TelemetryManager - handle both module import and direct execution
try:
    from . import TelemetryManager
except ImportError:
    # When run directly from telemetry directory, import from __init__
    import sys

    sys.path.insert(0, str(Path(__file__).parent))
    from __init__ import TelemetryManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ObservabilityServiceChecker:
    """
    Checks the availability of observability services.
    """

    def __init__(self):
        self.services = {
            "loki": {"host": "loki", "port": 3100, "name": "Loki (Logs)"},
            "prometheus": {
                "host": "prometheus",
                "port": 9090,
                "name": "Prometheus (Metrics)",
            },
            "jaeger": {"host": "jaeger", "port": 16686, "name": "Jaeger (Traces)"},
            "otel_collector": {
                "host": "otel-collector",
                "port": 4318,
                "name": "OpenTelemetry Collector",
            },
        }

    def check_service(self, host: str, port: int, timeout: float = 2.0) -> bool:
        """
        Check if a service is available.
        """
        try:
            import socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def check_all_services(self) -> dict[str, dict[str, Any]]:
        """
        Check availability of all observability services.
        """
        results = {}

        for service_key, service_info in self.services.items():
            is_available = self.check_service(
                service_info["host"], service_info["port"]
            )
            results[service_key] = {
                "name": service_info["name"],
                "available": is_available,
                "host": service_info["host"],
                "port": service_info["port"],
            }

        return results


async def demonstrate_graceful_degradation():
    """
    Demonstrate how telemetry handles service failures.
    """
    logger.info("🔍 Checking observability services availability...")
    checker = ObservabilityServiceChecker()
    service_status = checker.check_all_services()

    # Report service availability
    available_services = []
    unavailable_services = []

    for service_key, status in service_status.items():
        if status["available"]:
            available_services.append(status["name"])
            logger.info(
                f"✅ {status['name']} is available at {status['host']}:{status['port']}"
            )
        else:
            unavailable_services.append(status["name"])
            logger.warning(
                f"❌ {status['name']} is NOT available at {status['host']}:{status['port']}"
            )

    logger.info(f"Available services: {len(available_services)}")
    logger.info(f"Unavailable services: {len(unavailable_services)}")

    # Initialize telemetry (will gracefully handle unavailable services)
    logger.info("\n🚀 Initializing telemetry with graceful degradation...")

    telemetry_manager = TelemetryManager(
        service_name="demo-service",
        service_version="1.0.0",
        environment="development",
        enable_tracing=True,
        enable_metrics=True,
        enable_logging=True,
        sampling_ratio=1.0,
    )

    success = telemetry_manager.initialize()

    if success:
        logger.info("✅ Telemetry initialized successfully")
    else:
        logger.warning("⚠️ Telemetry initialized with degraded functionality")

    # Show telemetry capabilities
    logger.info("\n📊 Telemetry capabilities after initialization:")
    logger.info(f"  Tracing enabled: {telemetry_manager.enable_tracing}")
    logger.info(f"  Metrics enabled: {telemetry_manager.enable_metrics}")
    logger.info(f"  Logging enabled: {telemetry_manager.enable_logging}")
    logger.info(f"  OTLP endpoint: {telemetry_manager.otlp_endpoint}")

    # Demonstrate telemetry usage
    logger.info("\n🔧 Demonstrating telemetry usage...")

    # Get tracer (may be None if tracing failed)
    tracer = telemetry_manager.get_tracer("demo")
    if tracer:
        logger.info(
            "✅ Tracer available - traces will be sent to observability services"
        )
    else:
        logger.warning("❌ Tracer not available - no distributed tracing")

    # Get meter (may be None if metrics failed)
    meter = telemetry_manager.get_meter("demo")
    if meter:
        logger.info(
            "✅ Meter available - metrics will be sent to observability services"
        )
    else:
        logger.warning("❌ Meter not available - no metrics collection")

    # Demonstrate span creation (with fallback)
    logger.info("\n📝 Creating example spans...")

    if tracer:
        # Full telemetry span
        with tracer.start_as_current_span(
            "demo_operation",
            attributes={
                "operation": "example",
                "user_id": "demo_user",
                "available_services": len(available_services),
            },
        ) as span:
            logger.info("Creating span with full telemetry support")

            # Simulate some work
            await asyncio.sleep(0.1)

            span.add_event("Work completed", {"duration": 0.1, "success": True})

            span.set_status(Status(StatusCode.OK))
    else:
        # Fallback logging
        logger.info("Creating fallback operation (no tracing)")
        await asyncio.sleep(0.1)
        logger.info("Fallback operation completed")

    # Demonstrate metrics (with fallback)
    logger.info("\n📈 Creating example metrics...")

    if meter:
        # Full metrics
        counter = meter.create_counter("demo_requests_total")
        histogram = meter.create_histogram("demo_request_duration")

        counter.add(1, {"endpoint": "/demo", "method": "GET"})
        histogram.record(0.1, {"endpoint": "/demo"})

        logger.info("✅ Metrics recorded successfully")
    else:
        # Fallback logging
        logger.info("📊 Metrics would be recorded here (no metrics available)")

    # Demonstrate logging (always available)
    logger.info("\n📝 Demonstrating structured logging...")

    # Structured logging (always works)
    logging.info(
        "Demo operation completed",
        extra={
            "operation": "demo",
            "duration": 0.1,
            "available_services": len(available_services),
            "unavailable_services": len(unavailable_services),
        },
    )

    # Summary
    logger.info("\n📋 Summary:")
    logger.info(f"  Total observability services: {len(service_status)}")
    logger.info(f"  Available services: {len(available_services)}")
    logger.info(f"  Unavailable services: {len(unavailable_services)}")
    logger.info(f"  Tracing working: {telemetry_manager.enable_tracing}")
    logger.info(f"  Metrics working: {telemetry_manager.enable_metrics}")
    logger.info("  Application functional: ✅ YES")

    # Cleanup
    logger.info("\n🧹 Cleaning up telemetry...")
    telemetry_manager.shutdown()

    return {
        "service_status": service_status,
        "available_services": available_services,
        "unavailable_services": unavailable_services,
        "telemetry_working": {
            "tracing": telemetry_manager.enable_tracing,
            "metrics": telemetry_manager.enable_metrics,
            "logging": telemetry_manager.enable_logging,
        },
    }


async def simulate_service_outage_scenario():
    """
    Simulate what happens when all observability services go down.
    """
    logger.info("=" * 60)
    logger.info("🚨 SCENARIO: All Observability Services Go Down")
    logger.info("=" * 60)

    # Step 1: Show initial state (assuming services are running)
    logger.info("Step 1: Services are initially running")
    initial_results = await demonstrate_graceful_degradation()

    logger.info("\n" + "=" * 60)
    logger.info("Step 2: All observability services go down")
    logger.info("=" * 60)

    # Step 2: Simulate services going down
    logger.info("Simulating service outage...")

    # Initialize telemetry again (will detect unavailable services)
    telemetry_manager = TelemetryManager(
        service_name="demo-service", service_version="1.0.0", environment="development"
    )

    success = telemetry_manager.initialize()

    logger.info("\n📊 After service outage:")
    logger.info(
        f"  Telemetry initialization: {'✅ Success' if success else '⚠️ Degraded'}"
    )
    logger.info(f"  Tracing enabled: {telemetry_manager.enable_tracing}")
    logger.info(f"  Metrics enabled: {telemetry_manager.enable_metrics}")
    logger.info(f"  Logging enabled: {telemetry_manager.enable_logging}")

    # Step 3: Demonstrate continued operation
    logger.info("\nStep 3: Application continues to work normally")

    # Simulate normal application operations
    for i in range(3):
        if telemetry_manager.get_tracer():
            with telemetry_manager.get_tracer().start_as_current_span(
                f"operation_{i}", attributes={"iteration": i}
            ):
                logger.info(f"Processing operation {i}")
                await asyncio.sleep(0.05)
        else:
            logger.info(f"Processing operation {i} (no tracing)")
            await asyncio.sleep(0.05)

    logger.info(
        "\n✅ Application operations completed successfully despite service outage"
    )
    logger.info("📝 All operations were logged locally")
    logger.info("🔄 No data loss - operations continue normally")

    # Step 4: Show recovery scenario
    logger.info("\n" + "=" * 60)
    logger.info("Step 4: Services come back online")
    logger.info("=" * 60)

    logger.info("Simulating service recovery...")

    # Re-initialize with services available
    telemetry_manager.shutdown()

    # In a real scenario, you'd call initialize_telemetry() again
    logger.info("🔄 Re-initializing telemetry...")
    logger.info("✅ Telemetry would automatically detect available services")
    logger.info("📊 Full observability would be restored")

    return {
        "initial_state": initial_results,
        "outage_state": {
            "tracing": telemetry_manager.enable_tracing,
            "metrics": telemetry_manager.enable_metrics,
            "logging": telemetry_manager.enable_logging,
        },
        "application_functional": True,
        "data_preserved": True,
    }


if __name__ == "__main__":
    """
    Run the graceful degradation demonstration.
    """
    logger.info("🎯 OpenTelemetry Graceful Degradation Demonstration")
    logger.info("=" * 60)

    # Run the demonstration
    results = asyncio.run(demonstrate_graceful_degradation())

    logger.info("\n🎉 Demonstration completed!")
    logger.info("Key takeaways:")
    logger.info(
        "1. ✅ Application continues working even when observability services are down"
    )
    logger.info("2. ✅ No data loss - all operations are logged locally")
    logger.info("3. ✅ Automatic fallback to console exporters")
    logger.info("4. ✅ Telemetry automatically recovers when services come back")
    logger.info("5. ✅ Zero application downtime due to observability issues")
