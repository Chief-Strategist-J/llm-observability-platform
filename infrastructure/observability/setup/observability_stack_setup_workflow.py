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
        
        workflow_start = workflow.now()
        results = {}
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
            backoff_coefficient=2.0,
        )
        
        network_result = await workflow.execute_activity(
            "create_observability_network_activity",
            {"trace_id": trace_id, "network_name": "observability-network"},
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )
        results["network"] = network_result
        
        if not network_result.get("success"):
            return {
                "success": False,
                "error": "network_creation_failed",
                "trace_id": trace_id,
                "results": results
            }
        
        service_hostnames = [
            "scaibu.otel", "scaibu.prometheus", "scaibu.loki",
            "scaibu.jaeger", "scaibu.alertmanager", "scaibu.grafana",
            "scaibu.traefik"
        ]
        
        certs_result = await workflow.execute_activity(
            "generate_certificates_activity",
            {"trace_id": trace_id, "hostnames": service_hostnames, "certs_dir": certs_dir},
            start_to_close_timeout=timedelta(seconds=120),
            retry_policy=retry_policy,
        )
        results["certificates"] = certs_result
        
        if not certs_result.get("success"):
            return {
                "success": False,
                "error": "certificate_generation_failed",
                "trace_id": trace_id,
                "results": results
            }
        
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
        
        service_ips = {
            "scaibu.otel": "172.28.0.10",
            "scaibu.prometheus": "172.28.0.20",
            "scaibu.loki": "172.28.0.30",
            "scaibu.jaeger": "172.28.0.40",
            "scaibu.alertmanager": "172.28.0.50",
            "scaibu.grafana": "172.28.0.60",
        }
        
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
        
        hosts_entries = [{"hostname": h, "ip": "127.0.1.1"} for h, ip in service_ips.items()]
        hosts_result = await workflow.execute_activity(
            "add_hosts_entries_activity",
            {"trace_id": trace_id, "entries": hosts_entries, "force_replace": True},
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )
        results["hosts"] = hosts_result
        
        stack_result = await workflow.execute_activity(
            "start_observability_stack_activity",
            {"trace_id": trace_id},
            start_to_close_timeout=timedelta(seconds=180),
            retry_policy=retry_policy,
        )
        results["stack"] = stack_result
        
        if not stack_result.get("success"):
            return {
                "success": False,
                "error": "stack_start_failed",
                "trace_id": trace_id,
                "results": results
            }
        
        await workflow.sleep(10)
        
        verify_result = await workflow.execute_activity(
            "verify_observability_stack_activity",
            {"trace_id": trace_id},
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=retry_policy,
        )
        results["verification"] = verify_result
        
        duration = workflow.now() - workflow_start
        duration_ms = int(duration.total_seconds() * 1000)
        
        final_success = (
            network_result.get("success") and
            certs_result.get("success") and
            traefik_config_result.get("success") and
            stack_result.get("success") and
            verify_result.get("success")
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
