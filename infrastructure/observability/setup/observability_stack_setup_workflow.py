from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


@workflow.defn(name="ObservabilityStackSetupWorkflow")
class ObservabilityStackSetupWorkflow:
    @workflow.run
    async def run(self, params: dict) -> dict:
        trace_id = f"obs-setup-{workflow.uuid4()}"
        certs_dir = params.get("certs_dir", str(project_root / "infrastructure/orchestrator/config/docker/traefik/certs"))
        config_dir = params.get("config_dir", str(project_root / "infrastructure/orchestrator/config/docker/traefik/config"))
        logger = workflow.logger

        def _format_fields(**fields: object) -> str:
            if not fields:
                return ""
            parts = [f"{key}={fields[key]}" for key in sorted(fields)]
            return " " + " ".join(parts)

        def log_info(message: str, **fields: object) -> None:
            logger.info(f"{message}{_format_fields(**fields)}")

        def log_warning(message: str, **fields: object) -> None:
            logger.warning(f"{message}{_format_fields(**fields)}")

        def log_error(message: str, **fields: object) -> None:
            logger.error(f"{message}{_format_fields(**fields)}")

        log_info(
            "observability_setup_start",
            trace_id=trace_id,
            certs_dir=certs_dir,
            config_dir=config_dir,
        )

        workflow_start = workflow.now()
        results = {}
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
            backoff_coefficient=2.0,
        )

        def _step_failure(step: str, error_code: str) -> dict:
            log_error(
                "observability_setup_step_failed",
                trace_id=trace_id,
                step=step,
                error_code=error_code,
                step_result=results.get(step),
            )
            return {
                "success": False,
                "error": error_code,
                "trace_id": trace_id,
                "results": results,
                "failed_step": step,
            }

        log_info("observability_step_start", step="network", trace_id=trace_id)
        network_result = await workflow.execute_activity(
            "create_observability_network_activity",
            {"trace_id": trace_id, "network_name": "observability-network"},
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )
        results["network"] = network_result
        if not network_result.get("success"):
            return _step_failure("network", "network_creation_failed")
        log_info(
            "observability_step_complete",
            step="network",
            trace_id=trace_id,
            created=network_result.get("created"),
        )
        
        service_hostnames = [
            "scaibu.otel", "scaibu.prometheus", "scaibu.loki",
            "scaibu.jaeger", "scaibu.alertmanager", "scaibu.grafana",
            "scaibu.traefik"
        ]
        log_info(
            "observability_step_start",
            step="certificates",
            trace_id=trace_id,
            hostnames=len(service_hostnames),
        )
        certs_result = await workflow.execute_activity(
            "generate_certificates_activity",
            {"trace_id": trace_id, "hostnames": service_hostnames, "certs_dir": certs_dir},
            start_to_close_timeout=timedelta(seconds=120),
            retry_policy=retry_policy,
        )
        results["certificates"] = certs_result
        if not certs_result.get("success"):
            return _step_failure("certificates", "certificate_generation_failed")
        logger.info(
            f"observability_step_complete step=certificates trace_id={trace_id} generated={sum(1 for details in (certs_result.get('results') or {}).values() if details.get('generated'))}"
        )
        
        logger.info(f"observability_step_start step=traefik_config trace_id={trace_id}")
        traefik_config_result = await workflow.execute_activity(
            "generate_traefik_tls_config_activity",
            {
                "trace_id": trace_id,
                "hostnames": service_hostnames,
                "certs_dir": "/certs",
                "output_file": f"{config_dir}/traefik_dynamic_tls.yaml"
            },
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )
        results["traefik_config"] = traefik_config_result
        if not traefik_config_result.get("success"):
            return _step_failure("traefik_config", "traefik_config_generation_failed")
        log_info(
            "observability_step_complete",
            step="traefik_config",
            trace_id=trace_id,
            certificates_count=traefik_config_result.get("certificates_count"),
        )
        
        service_ips = {
            "scaibu.otel": "172.28.0.10",
            "scaibu.prometheus": "172.28.0.20",
            "scaibu.loki": "172.28.0.30",
            "scaibu.jaeger": "172.28.0.40",
            "scaibu.alertmanager": "172.28.0.50",
            "scaibu.grafana": "172.28.0.60",
        }
        
        host_loopback_ip = params.get("host_loopback_ip", "127.0.2.1")
        if not host_loopback_ip:
            return _step_failure("virtual_ips", "invalid_loopback_ip")
        log_info(
            "observability_step_start",
            step="virtual_ips",
            trace_id=trace_id,
            loopback_ip=host_loopback_ip,
        )

        vip_result = await workflow.execute_activity(
            "allocate_virtual_ips_activity",
            {
                "trace_id": trace_id,
                "hostnames": list(service_ips.keys()),
                "requested_ips": service_ips
            },
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=retry_policy,
        )
        results["virtual_ips"] = vip_result
        if not vip_result.get("success"):
            return _step_failure("virtual_ips", "virtual_ip_allocation_failed")

        missing_vips = [
            hostname
            for hostname, details in (vip_result.get("results") or {}).items()
            if not details.get("ip_added")
        ]
        if missing_vips:
            logger.warning(
                f"observability_virtual_ip_warn trace_id={trace_id} missing_hosts={missing_vips}"
            )

        logger.info(
            f"observability_step_complete step=virtual_ips trace_id={trace_id} allocated={len(vip_result.get('results', {}))}"
        )
        
        hosts_entries = [{"hostname": hostname, "ip": host_loopback_ip} for hostname in service_ips.keys()]
        logger.info(
            f"observability_step_start step=hosts trace_id={trace_id} entries={len(hosts_entries)}"
        )
        hosts_result = await workflow.execute_activity(
            "add_hosts_entries_activity",
            {"trace_id": trace_id, "entries": hosts_entries, "force_replace": True},
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )
        results["hosts"] = hosts_result
        if not hosts_result.get("success"):
            return _step_failure("hosts", "hosts_update_failed")
        log_info(
            "observability_step_complete",
            step="hosts",
            trace_id=trace_id,
            backup_path=hosts_result.get("backup_path"),
        )

        log_info("observability_step_start", step="traefik", trace_id=trace_id)
        traefik_result = await workflow.execute_activity(
            "start_traefik_activity",
            {"trace_id": trace_id},
            start_to_close_timeout=timedelta(seconds=120),
            retry_policy=retry_policy,
        )
        results["traefik"] = traefik_result
        if not traefik_result.get("success"):
            return _step_failure("traefik", "traefik_start_failed")
        log_info(
            "observability_step_complete",
            step="traefik",
            trace_id=trace_id,
            status=traefik_result.get("status"),
        )

        log_info("observability_step_start", step="stack_start", trace_id=trace_id)
        stack_result = await workflow.execute_activity(
            "start_observability_stack_activity",
            {
                "trace_id": trace_id,
                "timeout_seconds": params.get("stack_start_timeout", 300),
            },
            start_to_close_timeout=timedelta(seconds=180),
            retry_policy=retry_policy,
        )
        results["stack"] = stack_result
        
        if not stack_result.get("success"):
            return _step_failure("stack", "stack_start_failed")
        log_info(
            "observability_step_complete",
            step="stack_start",
            trace_id=trace_id,
        )
        
        await workflow.sleep(10)
        
        log_info("observability_step_start", step="verification", trace_id=trace_id)
        verify_result = await workflow.execute_activity(
            "verify_observability_stack_activity",
            {"trace_id": trace_id},
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=retry_policy,
        )
        results["verification"] = verify_result
        if not verify_result.get("success"):
            return _step_failure("verification", "stack_verification_failed")
        log_info(
            "observability_step_complete",
            step="verification",
            trace_id=trace_id,
        )
        
        duration = workflow.now() - workflow_start
        duration_ms = int(duration.total_seconds() * 1000)
         
        final_success = (
            network_result.get("success") and
            certs_result.get("success") and
            traefik_config_result.get("success") and
            traefik_result.get("success") and
            stack_result.get("success") and
            verify_result.get("success")
        )
        
        log_info(
            "observability_setup_complete",
            trace_id=trace_id,
            success=final_success,
            duration_ms=duration_ms,
        )
        return {
            "success": final_success,
            "trace_id": trace_id,
            "duration_ms": duration_ms,
            "results": results
        }


@workflow.defn(name="ObservabilityStackTeardownWorkflow")
class ObservabilityStackTeardownWorkflow:
    @workflow.run
    async def run(self, params: dict) -> dict:
        trace_id = f"obs-teardown-{workflow.uuid4()}"
        certs_dir = params.get("certs_dir", str(Path(__file__).parent / "certs"))
        
        workflow_start = workflow.now()
        results = {}
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
            backoff_coefficient=2.0,
        )
        
        stack_result = await workflow.execute_activity(
            "stop_observability_stack_activity",
            {"trace_id": trace_id},
            start_to_close_timeout=timedelta(seconds=180),
            retry_policy=retry_policy,
        )
        results["stack"] = stack_result
        
        service_hostnames = [
            "scaibu.otel", "scaibu.prometheus", "scaibu.loki",
            "scaibu.jaeger", "scaibu.alertmanager", "scaibu.grafana"
        ]
        
        vip_result = await workflow.execute_activity(
            "deallocate_virtual_ips_activity",
            {"trace_id": trace_id, "hostnames": service_hostnames, "remove_ip": True},
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=retry_policy,
        )
        results["virtual_ips"] = vip_result
        
        hosts_result = await workflow.execute_activity(
            "remove_hosts_entries_activity",
            {"trace_id": trace_id, "hostnames": service_hostnames},
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )
        results["hosts"] = hosts_result
        
        certs_result = await workflow.execute_activity(
            "delete_certificates_activity",
            {"trace_id": trace_id, "hostnames": service_hostnames, "certs_dir": certs_dir},
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=retry_policy,
        )
        results["certificates"] = certs_result
        
        duration = workflow.now() - workflow_start
        duration_ms = int(duration.total_seconds() * 1000)
        
        return {
            "success": stack_result.get("success", False),
            "trace_id": trace_id,
            "duration_ms": duration_ms,
            "results": results
        }
