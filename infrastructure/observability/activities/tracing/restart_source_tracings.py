import logging
import time
from typing import Dict, Any
from temporalio import activity
import docker

logger = logging.getLogger(__name__)

@activity.defn
async def restart_source_tracings(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(
        "restart_source_tracings_start params_keys=%s timeout_seconds=%s",
        list(params.keys()),
        params.get("timeout_seconds", 60),
    )

    container_name = params.get("container_name")
    timeout_seconds = int(params.get("timeout_seconds", 60))

    if not container_name:
        logger.error("restart_source_tracings_error error=missing_container_name")
        return {"success": False, "data": None, "error": "missing_container_name"}

    try:
        client = docker.from_env()
        logger.info("docker_client_created status=success")
    except Exception as e:
        logger.error(
            "restart_source_tracings_error error=docker_client_error exception=%s",
            e,
            exc_info=True,
        )
        return {"success": False, "data": None, "error": "docker_client_error"}

    try:
        container = None
        try:
            container = client.containers.get(container_name)
            logger.info(
                "container_found method=get name=%s", container_name
            )
        except Exception:
            logger.info("container_get_failed name=%s searching=list", container_name)
            for c in client.containers.list(all=True):
                if c.name == container_name:
                    container = c
                    logger.info(
                        "container_found method=list name=%s", container_name
                    )
                    break

        if container is None:
            logger.error(
                "restart_source_tracings_error error=container_not_found name=%s",
                container_name,
            )
            return {"success": False, "data": None, "error": "container_not_found"}

        logger.info(
            "container_restart_initiated name=%s current_status=%s",
            container_name,
            container.status,
        )

        try:
            container.restart(timeout=10)
            logger.info("container_restart_called name=%s", container_name)
        except Exception as e:
            logger.warning(
                "container_restart_failed name=%s fallback=stop_start exception=%s",
                container_name,
                e,
            )
            try:
                container.stop(timeout=10)
                logger.info("container_stopped name=%s", container_name)
            except Exception as e2:
                logger.warning(
                    "container_stop_failed name=%s exception=%s",
                    container_name,
                    e2,
                )
            try:
                container.start()
                logger.info("container_started name=%s", container_name)
            except Exception as e3:
                logger.error(
                    "container_start_failed name=%s exception=%s",
                    container_name,
                    e3,
                    exc_info=True,
                )
                return {"success": False, "data": None, "error": "restart_failed"}

        start_time = time.time()
        ready = False

        for attempt in range(1, 6):
            time.sleep(2)
            try:
                container.reload()
                status = container.status

                logger.info(
                    "container_status_check name=%s status=%s attempt=%d elapsed=%.1f",
                    container_name,
                    status,
                    attempt,
                    time.time() - start_time,
                )

                if status == "running":
                    try:
                        health = container.attrs.get("State", {}).get("Health", {}).get("Status")
                    except Exception:
                        health = None

                    logger.info(
                        "container_health_check name=%s health=%s",
                        container_name,
                        health,
                    )

                    if health in (None, "healthy", "starting"):
                        ready = True
                        logger.info(
                            "container_ready name=%s attempt=%d",
                            container_name,
                            attempt,
                        )
                        break
                else:
                    logger.warning(
                        "container_not_running name=%s status=%s",
                        container_name,
                        status,
                    )

            except Exception as e:
                logger.warning(
                    "container_reload_error name=%s exception=%s",
                    container_name,
                    e,
                )

        if not ready:
            logger.error("container_not_ready_after_checks name=%s", container_name)

        try:
            logs = container.logs(tail=200).decode("utf-8", errors="ignore")
            logger.info(
                "container_logs_sample name=%s length=%d",
                container_name,
                len(logs),
            )

            lowered = logs.lower()

            if "invalid keys" in lowered or "cannot unmarshal" in lowered:
                logger.error(
                    "config_error_detected name=%s error=otel_config_invalid",
                    container_name,
                )
                return {
                    "success": False,
                    "data": {
                        "status": "config_invalid",
                        "error": "otel_config_error",
                        "logs": logs[-1000:],
                    },
                    "error": "config_error",
                }

            if "bind: address already in use" in lowered:
                logger.error(
                    "port_conflict_detected name=%s error=address_in_use",
                    container_name,
                )

            if "failed to create" in lowered or "error" in lowered:
                logger.warning(
                    "container_warning_logs_detected name=%s",
                    container_name,
                )

        except Exception as e:
            logger.warning(
                "container_logs_fetch_failed name=%s exception=%s",
                container_name,
                e,
            )

        logger.info(
            "post_restart_settle_wait name=%s wait_seconds=10",
            container_name,
        )
        time.sleep(10)

        try:
            container.reload()
            final_status = container.status
            logger.info(
                "final_container_status name=%s status=%s",
                container_name,
                final_status,
            )

            if final_status != "running":
                logger.error(
                    "container_final_not_running name=%s status=%s",
                    container_name,
                    final_status,
                )
                return {
                    "success": False,
                    "data": {"status": final_status},
                    "error": "container_not_running",
                }
        except Exception as e:
            logger.error(
                "final_status_check_failed name=%s exception=%s",
                container_name,
                e,
                exc_info=True,
            )

        elapsed = time.time() - start_time
        logger.info(
            "restart_source_tracings_complete name=%s status=running elapsed=%.2f",
            container_name,
            elapsed,
        )

        return {"success": True, "data": {"status": "running", "elapsed": elapsed}, "error": None}

    except Exception as e:
        logger.error(
            "restart_source_tracings_fatal error=unexpected_error exception=%s",
            e,
            exc_info=True,
        )
        return {"success": False, "data": None, "error": "unexpected_error"}
