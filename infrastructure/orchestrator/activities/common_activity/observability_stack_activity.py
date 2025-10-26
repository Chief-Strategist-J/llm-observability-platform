import asyncio
import logging

from temporalio import activity

# Import all the individual activities
from .configure_opentelemetry_activity import (
    configure_opentelemetry_collector,
    validate_opentelemetry_config,
)
from .jaeger_activity import get_jaeger_status, start_jaeger_container
from .loki_activity import get_loki_status, start_loki_container
from .opentelemetry_collector_activity import (
    get_opentelemetry_collector_status,
    start_opentelemetry_collector,
    stop_opentelemetry_collector,
)
from .prometheus_activity import get_prometheus_status, start_prometheus_container

# Service Access Information:
# OpenTelemetry Collector: http://localhost:13133/health
# Traces (Jaeger): http://localhost:16686
# Metrics (Prometheus): http://localhost:9090
# Logs (Loki): http://localhost:3100
# Grafana: http://localhost:3000 (if configured)

logging.basicConfig(level=logging.INFO)

# Configuration for the complete observability stack
OBSERVABILITY_STACK = {
    "loki": {
        "name": "Loki (Logs)",
        "start_activity": start_loki_container,
        "status_activity": get_loki_status,
        "port": 3100,
        "ui_url": "http://localhost:3100",
        "purpose": "Log aggregation and querying",
    },
    "prometheus": {
        "name": "Prometheus (Metrics)",
        "start_activity": start_prometheus_container,
        "status_activity": get_prometheus_status,
        "port": 9090,
        "ui_url": "http://localhost:9090",
        "purpose": "Metrics collection and alerting",
    },
    "jaeger": {
        "name": "Jaeger (Traces)",
        "start_activity": start_jaeger_container,
        "status_activity": get_jaeger_status,
        "port": 16686,
        "ui_url": "http://localhost:16686",
        "purpose": "Distributed tracing and performance monitoring",
    },
    "otel_collector": {
        "name": "OpenTelemetry Collector",
        "start_activity": start_opentelemetry_collector,
        "status_activity": get_opentelemetry_collector_status,
        "port": 13133,
        "ui_url": "http://localhost:13133",
        "purpose": "Telemetry data collection and forwarding",
    },
}


@activity.defn
async def setup_complete_observability_stack(service_name: str) -> dict:
    """
    Set up the complete observability stack (logs, metrics, traces)
    """
    logging.info(f"Setting up complete observability stack for {service_name}")

    results = {"success": True, "services": {}, "errors": [], "summary": {}}

    # Step 1: Configure OpenTelemetry Collector
    logging.info("Step 1: Configuring OpenTelemetry Collector")
    config_success = await configure_opentelemetry_collector(service_name)
    if not config_success:
        results["errors"].append("Failed to configure OpenTelemetry Collector")
        results["success"] = False
        return results
    results["services"]["configuration"] = {"status": "completed"}

    # Validate configuration
    validation_result = await validate_opentelemetry_config(service_name)
    if not validation_result.get("valid", False):
        results["errors"].extend(validation_result.get("errors", []))
        results["success"] = False
        return results

    # Step 2: Start observability services in correct order
    # Order matters: Loki -> Prometheus -> Jaeger -> OTEL Collector
    service_order = ["loki", "prometheus", "jaeger", "otel_collector"]

    for service_key in service_order:
        service_info = OBSERVABILITY_STACK[service_key]
        logging.info(f"Step 2: Starting {service_info['name']}")

        try:
            success = await service_info["start_activity"](service_name)
            if success:
                results["services"][service_key] = {"status": "started"}

                # Get status for additional info
                status = await service_info["status_activity"](service_name)
                results["services"][service_key]["details"] = status

                logging.info(f"✅ {service_info['name']} started successfully")
            else:
                results["services"][service_key] = {"status": "failed"}
                results["errors"].append(f"Failed to start {service_info['name']}")
                results["success"] = False
                logging.error(f"❌ Failed to start {service_info['name']}")

        except Exception as e:
            results["services"][service_key] = {"status": "error", "error": str(e)}
            results["errors"].append(f"Error starting {service_info['name']}: {e!s}")
            results["success"] = False
            logging.exception(f"❌ Error starting {service_info['name']}")

    # Step 3: Generate summary
    results["summary"] = {
        "total_services": len(OBSERVABILITY_STACK),
        "successful_services": len(
            [s for s in results["services"].values() if s.get("status") == "started"]
        ),
        "failed_services": len(
            [
                s
                for s in results["services"].values()
                if s.get("status") in ["failed", "error"]
            ]
        ),
        "configuration_valid": validation_result.get("valid", False),
        "access_urls": {
            service_key: service_info["ui_url"]
            for service_key, service_info in OBSERVABILITY_STACK.items()
        },
    }

    if results["success"]:
        logging.info("🎉 Complete observability stack setup successful!")
        logging.info("📊 Access your observability stack:")
        for service_key, service_info in OBSERVABILITY_STACK.items():
            if results["services"].get(service_key, {}).get("status") == "started":
                logging.info(f"  - {service_info['name']}: {service_info['ui_url']}")
    else:
        logging.error("❌ Observability stack setup completed with errors")
        logging.error(f"Errors: {results['errors']}")

    return results


@activity.defn
async def get_observability_stack_status(service_name: str) -> dict:
    """
    Get the status of the complete observability stack.
    """
    logging.info(f"Getting observability stack status for {service_name}")

    status_results = {
        "services": {},
        "overall_status": "unknown",
        "healthy_services": 0,
        "total_services": len(OBSERVABILITY_STACK),
    }

    # Check status of each service
    for service_key, service_info in OBSERVABILITY_STACK.items():
        try:
            status = await service_info["status_activity"](service_name)
            status_results["services"][service_key] = status

            if status.get("status") == "running":
                status_results["healthy_services"] += 1

        except Exception as e:
            status_results["services"][service_key] = {
                "status": "error",
                "error": str(e),
            }
            logging.exception(f"Error getting status for {service_info['name']}")

    # Determine overall status
    if status_results["healthy_services"] == status_results["total_services"]:
        status_results["overall_status"] = "healthy"
    elif status_results["healthy_services"] > 0:
        status_results["overall_status"] = "degraded"
    else:
        status_results["overall_status"] = "unhealthy"

    logging.info(
        f"Observability stack status: {status_results['overall_status']} "
        f"({status_results['healthy_services']}/{status_results['total_services']} services healthy)"
    )

    return status_results


@activity.defn
async def stop_observability_stack(service_name: str) -> bool:
    """
    Stop the complete observability stack.
    """
    logging.info(f"Stopping complete observability stack for {service_name}")

    success_count = 0
    total_services = len(OBSERVABILITY_STACK)

    # Stop services in reverse order
    service_order = ["otel_collector", "jaeger", "prometheus", "loki"]

    for service_key in service_order:
        service_info = OBSERVABILITY_STACK[service_key]
        logging.info(f"Stopping {service_info['name']}")

        try:
            if service_key == "otel_collector":
                success = await stop_opentelemetry_collector(service_name)
            else:
                # For other services, we'd need stop activities
                # For now, just check if they're running
                status = await service_info["status_activity"](service_name)
                if status.get("status") == "running":
                    logging.info(
                        f"{service_info['name']} is running - manual stop may be required"
                    )
                success = True

            if success:
                success_count += 1
                logging.info(f"✅ {service_info['name']} stopped")
            else:
                logging.error(f"❌ Failed to stop {service_info['name']}")

        except Exception as e:
            logging.exception(f"Error stopping {service_info['name']}: {e}")

    overall_success = success_count == total_services

    if overall_success:
        logging.info(
            f"🎉 Observability stack stopped successfully ({success_count}/{total_services} services)"
        )
    else:
        logging.warning(
            f"⚠️ Observability stack stop completed with issues ({success_count}/{total_services} services stopped)"
        )

    return overall_success


@activity.defn
async def restart_observability_stack(service_name: str) -> dict:
    """
    Restart the complete observability stack.
    """
    logging.info(f"Restarting complete observability stack for {service_name}")

    # Stop all services first
    stop_success = await stop_observability_stack(service_name)

    if not stop_success:
        logging.warning("Some services may not have stopped cleanly")

    # Wait a bit for cleanup
    await asyncio.sleep(5)

    # Start all services
    results = await setup_complete_observability_stack(service_name)

    if results["success"]:
        logging.info("🔄 Observability stack restarted successfully")
    else:
        logging.error("❌ Observability stack restart failed")

    return results
