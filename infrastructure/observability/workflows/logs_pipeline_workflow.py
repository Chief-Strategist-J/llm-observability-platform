from __future__ import annotations

from pathlib import Path
from datetime import timedelta
from typing import Dict, Any, List

from temporalio import workflow
from infrastructure.observability.config.constants import OBSERVABILITY_CONFIG
from infrastructure.orchestrator.base.base_workflow import BaseWorkflow


@workflow.defn
class LogsPipelineWorkflow(BaseWorkflow):

    async def allocate_virtual_ips(self, trace_id: str) -> Dict[str, Any]:
        payload = {
            "trace_id": trace_id,
            "hostnames": ["scaibu.traefik"],
            "requested_ips": {"scaibu.traefik": "127.0.1.1"},
        }

        result = await workflow.execute_activity(
            "allocate_virtual_ips_activity",
            payload,
            start_to_close_timeout=timedelta(seconds=30),
        )

        workflow.logger.info({
            "stage": "virtual_ip_allocation",
            "trace_id": trace_id,
            "result": result,
        })

        return result

    async def add_required_hosts(self, trace_id: str, allocated_ips: Dict[str, Any]) -> Dict[str, Any]:
        entries: List[Dict[str, str]] = []
        for hostname, result in allocated_ips.items():
            if result.get("allocated"):
                entries.append({
                    "ip": result["ip"],
                    "hostname": hostname
                })

        payload = {
            "trace_id": trace_id,
            "force_replace": True,
            "entries": entries,
        }

        result = await workflow.execute_activity(
            "add_hosts_entries_activity",
            payload,
            start_to_close_timeout=timedelta(seconds=30),
        )

        workflow.logger.info({
            "stage": "hosts_update",
            "trace_id": trace_id,
            "result": result,
        })

        return result

    async def verify_hosts(self, trace_id: str) -> Dict[str, Any]:
        payload = {
            "trace_id": trace_id,
            "hostnames": ["scaibu.traefik"],
        }

        result = await workflow.execute_activity(
            "verify_hosts_entries_activity",
            payload,
            start_to_close_timeout=timedelta(seconds=20),
        )

        workflow.logger.info({
            "stage": "hosts_verify",
            "trace_id": trace_id,
            "result": result,
        })

        return result

    async def verify_virtual_ips(self, trace_id: str) -> Dict[str, Any]:
        payload = {
            "trace_id": trace_id,
            "hostnames": ["scaibu.traefik"],
        }

        result = await workflow.execute_activity(
            "verify_virtual_ips_activity",
            payload,
            start_to_close_timeout=timedelta(seconds=20),
        )

        workflow.logger.info({
            "stage": "virtual_ip_verify",
            "trace_id": trace_id,
            "result": result,
        })

        return result

    async def start_traefik(self, trace_id: str) -> Dict[str, Any]:
        result = await workflow.execute_activity(
            "start_traefik_activity",
            {"instance_id": 0, "trace_id": trace_id},
            start_to_close_timeout=timedelta(seconds=120),
        )

        workflow.logger.info({
            "stage": "start_traefik",
            "trace_id": trace_id,
            "result": result,
        })

        return result

    @workflow.run
    async def run(self, params: Dict[str, Any] = None, *args, **kwargs) -> str:
        params = params or {}
        trace_id = params.get("trace_id", "logs-pipeline")
        continue_on_vip_failure: bool = bool(params.get("continue_on_vip_failure", False))

        workflow.logger.info({
            "pipeline": "logs",
            "event": "workflow_start",
            "trace_id": trace_id
        })

        vip_result = await self.allocate_virtual_ips(trace_id)

        # vip_result structure expected: {"success": bool, "results": { hostname: { "ip": ..., "allocated": bool, "ip_added": bool, ... } }, ...}
        vip_success = bool(vip_result.get("success", False))
        vip_results = vip_result.get("results", {})

        ip_add_failures = [
            hostname for hostname, r in vip_results.items()
            if r.get("allocated") and not r.get("ip_added", False)
        ]

        if ip_add_failures:
            workflow.logger.warning({
                "pipeline": "logs",
                "stage": "virtual_ip_addition_partial_failure",
                "trace_id": trace_id,
                "failed_hostnames": ip_add_failures,
                "vip_result": vip_result,
            })

            if not continue_on_vip_failure:
                workflow.logger.error({
                    "pipeline": "logs",
                    "stage": "virtual_ip_allocation_failed",
                    "trace_id": trace_id,
                    "error": vip_result,
                    "remediation": [
                        "Run worker as root so it can add loopback IPs (e.g. `sudo python ...`), or",
                        "Allow the worker user to run ip without a password via sudoers: "
                        "`your_worker_user ALL=(root) NOPASSWD: /sbin/ip, /bin/ip`",
                        "Or set `continue_on_vip_failure` to True when starting the workflow to proceed without OS-level IPs (testing only)."
                    ]
                })
                return "logs_pipeline_failed_vip_allocation"

            workflow.logger.warning({
                "pipeline": "logs",
                "stage": "continuing_despite_vip_add_failures",
                "trace_id": trace_id,
                "note": "Continuing because continue_on_vip_failure=True. Traefik may not bind correctly until the loopback IPs are added on the host."
            })

        if not vip_success and not continue_on_vip_failure:
            workflow.logger.error({
                "pipeline": "logs",
                "stage": "virtual_ip_allocation_error",
                "trace_id": trace_id,
                "error": vip_result
            })
            return "logs_pipeline_failed_vip_allocation"

        # Proceed to add hosts using the allocated_ips (even if ip_added was false)
        hosts_result = await self.add_required_hosts(trace_id, vip_results)
        if not hosts_result.get("success"):
            workflow.logger.error({
                "pipeline": "logs",
                "stage": "hosts_add_failed",
                "trace_id": trace_id,
                "error": hosts_result
            })
            return "logs_pipeline_failed_hosts_add"

        verify_result = await self.verify_hosts(trace_id)
        if not verify_result.get("success"):
            workflow.logger.error({
                "pipeline": "logs",
                "stage": "hosts_verify_failed",
                "trace_id": trace_id,
                "error": verify_result
            })
            # if host verification fails but continue flag is set, we will proceed with warning
            if not continue_on_vip_failure:
                return "logs_pipeline_failed_hosts_verify"
            workflow.logger.warning({
                "pipeline": "logs",
                "stage": "hosts_verify_failed_but_continuing",
                "trace_id": trace_id
            })

        vip_verify_result = await self.verify_virtual_ips(trace_id)
        if not vip_verify_result.get("success"):
            workflow.logger.warning({
                "pipeline": "logs",
                "stage": "virtual_ip_verify_failed",
                "trace_id": trace_id,
                "error": vip_verify_result
            })
            if not continue_on_vip_failure:
                return "logs_pipeline_failed_vip_verify"
            workflow.logger.warning({
                "pipeline": "logs",
                "stage": "virtual_ip_verify_failed_but_continuing",
                "trace_id": trace_id
            })

        traefik_result = await self.start_traefik(trace_id)
        if not traefik_result.get("success"):
            workflow.logger.error({
                "pipeline": "logs",
                "stage": "traefik_start_failed",
                "trace_id": trace_id,
                "error": traefik_result
            })
            return "logs_pipeline_failed_traefik_start"

        workflow.logger.info({
            "pipeline": "logs",
            "event": "workflow_completed",
            "trace_id": trace_id,
            "traefik_access": "https://scaibu.traefik/dashboard/"
        })

        return "logs_pipeline_completed"
    