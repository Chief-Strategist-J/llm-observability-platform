from __future__ import annotations

import logging
from datetime import timedelta
from typing import Dict, List, Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from infrastructure.orchestrator.base.activities import (
        check_image_exists_activity,
        pull_image_activity,
        check_container_exists_activity,
        stop_container_activity,
        remove_container_activity,
        start_compose_activity,
        stop_compose_activity,
        restart_container_activity,
        verify_container_running_activity,
        check_network_exists_activity,
        delete_network_activity,
        create_network_activity,
        inspect_network_activity,
        attach_container_to_network_activity,
        verify_network_attachment_activity,
        create_tls_directories_activity,
        create_tls_directories_activity,
        create_root_ca_activity,
        install_root_ca_activity,
        generate_certificate_activity,
        create_tls_configuration_activity,
        configure_traefik_activity,
        add_labels_to_compose_activity,
        health_check_activity,
        diagnostic_container_inspect_activity,
        diagnostic_network_inspect_activity,
        diagnostic_host_configuration_activity,
        diagnostic_full_inspection_activity,
    )

logger = logging.getLogger(__name__)


@workflow.defn(name="ServiceSetupWorkflow")
class ServiceSetupWorkflow:
    @workflow.run
    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        workflow.logger.info("event=service_setup_workflow_start service=%s", params.get("service_name"))
        compose_file: str = params["compose_file"]
        hostname: str = params["hostname"]
        service_name: str = params["service_name"]
        network_name: str = params["network_name"]
        ip_address: str = params["ip_address"]
        port: str = params["port"]
        subnet: str = params.get("subnet", "172.29.0.0/16")
        gateway: str = params.get("gateway", "172.29.0.1")
        health_check_command: List[str] = params.get("health_check_command", [])
        traefik_compose_path: str = params.get("traefik_compose_path", "infrastructure/orchestrator/config/docker/traefik/config/traefik-dynamic-docker.yaml")
        tls_config_dir: str = params.get("tls_config_dir", "infrastructure/orchestrator/config/docker/traefik/config/tls")
        certs_dir: str = params.get("certs_dir", "infrastructure/orchestrator/config/docker/traefik/certs")
        additional_networks: List[str] = params.get("additional_networks", [])
        target_service: str = params.get("target_service", None)
        image_name: Optional[str] = params.get("image_name", None)
        retry_policy = RetryPolicy(maximum_attempts=3, initial_interval=timedelta(seconds=2), maximum_interval=timedelta(seconds=30), backoff_coefficient=2.0)
        try:
            workflow.logger.info("event=step_additional_networks_setup_start count=%d", len(additional_networks))
            for net in additional_networks:
                if net != network_name:
                    net_check = await workflow.execute_activity(check_network_exists_activity, {"network_name": net}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)
                    if not net_check.get("exists"):
                        workflow.logger.info("event=creating_additional_network network=%s", net)
                        await workflow.execute_activity(create_network_activity, {"network_name": net}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)

            workflow.logger.info("event=step_traefik_setup_start")
            traefik_image = "traefik:latest"
            traefik_container = "traefik-scaibu"
            image_check = await workflow.execute_activity(check_image_exists_activity, {"image_name": traefik_image}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)
            if not image_check.get("exists"):
                workflow.logger.info("event=pulling_traefik_image")
                await workflow.execute_activity(pull_image_activity, {"image_name": traefik_image}, start_to_close_timeout=timedelta(seconds=600), retry_policy=retry_policy)
            container_check = await workflow.execute_activity(check_container_exists_activity, {"container_name": traefik_container}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)
            if container_check.get("exists"):
                workflow.logger.info("event=stopping_existing_traefik")
                await workflow.execute_activity(stop_container_activity, {"container_name": traefik_container}, start_to_close_timeout=timedelta(seconds=60), retry_policy=retry_policy)
                await workflow.execute_activity(remove_container_activity, {"container_name": traefik_container}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)
            await workflow.execute_activity(start_compose_activity, {"compose_path": traefik_compose_path, "project_name": "traefik"}, start_to_close_timeout=timedelta(seconds=300), retry_policy=retry_policy)
            await workflow.execute_activity(configure_traefik_activity, {"traefik_compose_path": traefik_compose_path, "tls_strategy": params.get("tls_strategy", "local")}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)
            await workflow.execute_activity(restart_container_activity, {"container_name": traefik_container}, start_to_close_timeout=timedelta(seconds=60), retry_policy=retry_policy)
            traefik_running = await workflow.execute_activity(verify_container_running_activity, {"container_name": traefik_container, "max_retries": 5, "retry_delay": 3}, start_to_close_timeout=timedelta(seconds=60), retry_policy=retry_policy)
            if not traefik_running.get("running"):
                return {"success": False, "error": "Traefik failed to start", "step": "traefik_setup"}
            workflow.logger.info("event=traefik_setup_complete")
            await workflow.execute_activity(diagnostic_container_inspect_activity, {"container_name": traefik_container}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)
            workflow.logger.info("event=step_network_setup_start network=%s", network_name)
            network_check = await workflow.execute_activity(check_network_exists_activity, {"network_name": network_name}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)
            if network_check.get("exists"):
                workflow.logger.info("event=deleting_existing_network network=%s", network_name)
                await workflow.execute_activity(delete_network_activity, {"network_name": network_name}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)
            await workflow.execute_activity(create_network_activity, {"network_name": network_name, "subnet": subnet, "gateway": gateway}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)
            network_inspect = await workflow.execute_activity(inspect_network_activity, {"network_name": network_name}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)
            if not network_inspect.get("success"):
                return {"success": False, "error": "Network creation failed", "step": "network_setup"}
            workflow.logger.info("event=network_setup_complete network=%s", network_name)
            await workflow.execute_activity(diagnostic_network_inspect_activity, {"network_name": network_name}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)
            
            tls_strategy = params.get("tls_strategy", "local")
            hostnames = [hostname] + params.get("additional_hostnames", [])
            workflow.logger.info("event=step_tls_setup_start hostnames=%s strategy=%s", hostnames, tls_strategy)
            
            if tls_strategy == "local":
                await workflow.execute_activity(create_tls_directories_activity, {"tls_config_dir": tls_config_dir, "certs_dir": certs_dir}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)
                await workflow.execute_activity(create_root_ca_activity, {"certs_dir": certs_dir}, start_to_close_timeout=timedelta(seconds=60), retry_policy=retry_policy)
                await workflow.execute_activity(install_root_ca_activity, {"certs_dir": certs_dir}, start_to_close_timeout=timedelta(seconds=60), retry_policy=retry_policy)
                for h in hostnames:
                    await workflow.execute_activity(generate_certificate_activity, {"hostname": h, "certs_dir": certs_dir}, start_to_close_timeout=timedelta(seconds=60), retry_policy=retry_policy)
                    await workflow.execute_activity(create_tls_configuration_activity, {"hostname": h, "tls_config_dir": tls_config_dir}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)
            
            workflow.logger.info("event=tls_setup_complete hostnames=%s", hostnames)
            await workflow.execute_activity(diagnostic_host_configuration_activity, {"hostname": hostname}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)
            workflow.logger.info("event=step_labels_setup_start compose=%s target_service=%s", compose_file, target_service)
            await workflow.execute_activity(add_labels_to_compose_activity, {"compose_path": compose_file, "hostname": hostname, "network_name": network_name, "ip_address": ip_address, "port": port, "service_name": service_name, "target_service": target_service, "tls_strategy": tls_strategy}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)
            workflow.logger.info("event=labels_setup_complete")
            await workflow.execute_activity(diagnostic_container_inspect_activity, {"container_name": "traefik-scaibu"}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)
            workflow.logger.info("event=step_service_deploy_start service=%s", service_name)
            await workflow.execute_activity(start_compose_activity, {"compose_path": compose_file, "project_name": service_name}, start_to_close_timeout=timedelta(seconds=300), retry_policy=retry_policy)
            
            service_container = params.get("expected_container_name") or f"{service_name}-instance-0"
            
            container_check = await workflow.execute_activity(check_container_exists_activity, {"container_name": service_container}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)
            if container_check.get("exists"):
                await workflow.execute_activity(restart_container_activity, {"container_name": service_container}, start_to_close_timeout=timedelta(seconds=60), retry_policy=retry_policy)
            service_running = await workflow.execute_activity(verify_container_running_activity, {"container_name": service_container, "max_retries": 10, "retry_delay": 5}, start_to_close_timeout=timedelta(seconds=120), retry_policy=retry_policy)
            if not service_running.get("running"):
                return {"success": False, "error": f"Service {service_name} failed to start (container: {service_container})", "step": "service_deploy"}
            workflow.logger.info("event=service_deploy_complete service=%s container=%s", service_name, service_container)
            await workflow.execute_activity(diagnostic_container_inspect_activity, {"container_name": service_container}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)
            workflow.logger.info("event=step_network_attach_start container=%s network=%s", service_container, network_name)
            attach_result = await workflow.execute_activity(attach_container_to_network_activity, {"container_name": service_container, "network_name": network_name, "ip_address": ip_address}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)
            verify_attach = await workflow.execute_activity(verify_network_attachment_activity, {"container_name": service_container, "network_name": network_name}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)
            if not verify_attach.get("attached"):
                workflow.logger.info("event=network_attach_warning message=container_may_already_be_attached")
            
            # Ensure Traefik is attached to the service network to route traffic
            traefik_check = await workflow.execute_activity(check_container_exists_activity, {"container_name": traefik_container}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)
            if traefik_check.get("exists"):
                 await workflow.execute_activity(attach_container_to_network_activity, {"container_name": traefik_container, "network_name": network_name}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)

            workflow.logger.info("event=network_attach_complete")
            await workflow.execute_activity(diagnostic_network_inspect_activity, {"network_name": network_name}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)
            workflow.logger.info("event=step_restart_services")
            await workflow.execute_activity(restart_container_activity, {"container_name": traefik_container}, start_to_close_timeout=timedelta(seconds=60), retry_policy=retry_policy)
            await workflow.execute_activity(restart_container_activity, {"container_name": service_container}, start_to_close_timeout=timedelta(seconds=60), retry_policy=retry_policy)
            if health_check_command:
                workflow.logger.info("event=step_health_check_start command=%s", " ".join(health_check_command))
                health_result = await workflow.execute_activity(health_check_activity, {"container_name": service_container, "health_check_command": health_check_command, "max_retries": 5, "retry_delay": 10}, start_to_close_timeout=timedelta(seconds=120), retry_policy=retry_policy)
                if not health_result.get("healthy"):
                    workflow.logger.info("event=health_check_warning healthy=false")
                workflow.logger.info("event=health_check_complete healthy=%s", health_result.get("healthy"))
                await workflow.execute_activity(diagnostic_container_inspect_activity, {"container_name": service_container}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)
            workflow.logger.info("event=step_final_diagnostics")
            diagnostics = await workflow.execute_activity(diagnostic_full_inspection_activity, {"container_name": service_container, "network_name": network_name, "hostname": hostname}, start_to_close_timeout=timedelta(seconds=60), retry_policy=retry_policy)
            workflow.logger.info("event=service_setup_workflow_complete service=%s hostname=%s", service_name, hostname)
            return {"success": True, "service_name": service_name, "hostname": hostname, "container": service_container, "network": network_name, "diagnostics": diagnostics.get("diagnostics", {})}
        except Exception as e:
            workflow.logger.error("event=service_setup_workflow_failed error=%s", str(e))
            return {"success": False, "error": str(e)}


@workflow.defn(name="ServiceTeardownWorkflow")
class ServiceTeardownWorkflow:
    @workflow.run
    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        workflow.logger.info("event=service_teardown_workflow_start service=%s", params.get("service_name"))
        compose_file: str = params["compose_file"]
        service_name: str = params["service_name"]
        container_name: Optional[str] = params.get("container_name")
        image_name: Optional[str] = params.get("image_name")
        retry_policy = RetryPolicy(maximum_attempts=3, initial_interval=timedelta(seconds=2), maximum_interval=timedelta(seconds=30), backoff_coefficient=2.0)
        try:
            workflow.logger.info("event=step_stop_compose_start")
            await workflow.execute_activity(stop_compose_activity, {"compose_path": compose_file, "project_name": service_name}, start_to_close_timeout=timedelta(seconds=120), retry_policy=retry_policy)
            
            # Additional cleanup as requested: ensure container and undefined images are gone
            container_name = container_name or f"{service_name}-instance-0"
            workflow.logger.info("event=step_cleanup_container_start container=%s", container_name)
            await workflow.execute_activity(remove_container_activity, {"container_name": container_name}, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy)
            
            # Attempt to remove image if provided
            image_name = params.get("image_name")
            if image_name:
                workflow.logger.info("event=step_remove_image_start image=%s", image_name)
                # We use check first or just try remove. remove_image_activity handles errors.
                await workflow.execute_activity(remove_image_activity, {"image_name": image_name}, start_to_close_timeout=timedelta(seconds=60), retry_policy=retry_policy)
            
            workflow.logger.info("event=service_teardown_workflow_complete service=%s", service_name)
            return {"success": True, "service_name": service_name}
        except Exception as e:
            workflow.logger.error("event=service_teardown_workflow_failed error=%s", str(e))
            return {"success": False, "error": str(e)}
