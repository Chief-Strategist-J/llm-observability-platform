from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Any

import yaml
from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn(name="add_labels_to_compose_activity")
async def add_labels_to_compose_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        compose_path: str = params["compose_path"]
        hostname: str = params["hostname"]
        network_name: str = params["network_name"]
        ip_address: str = params["ip_address"]
        port: str = params["port"]
        service_name: str = params.get("service_name", hostname.replace("scaibu.", ""))
        target_service: str = params.get("target_service", "")
        logger.info("event=add_labels_to_compose_start compose=%s hostname=%s network=%s ip=%s port=%s target_service=%s", compose_path, hostname, network_name, ip_address, port, target_service)
        compose_file = Path(compose_path)
        if not compose_file.exists():
            logger.error("event=add_labels_to_compose_failed error=compose_file_not_found path=%s", compose_path)
            return {"success": False, "error": f"Compose file not found: {compose_path}"}
        with open(compose_file, "r") as f:
            compose_data = yaml.safe_load(f)
        services = compose_data.get("services", {})
        if not services:
            logger.error("event=add_labels_to_compose_failed error=no_services_found path=%s", compose_path)
            return {"success": False, "error": "No services found in compose file"}
        if target_service and target_service in services:
            selected_service_name = target_service
        else:
            selected_service_name = list(services.keys())[0]
        service = services[selected_service_name]
        if "labels" not in service:
            service["labels"] = {}
        labels = service["labels"]
        router_name = f"{service_name}-scaibu"
        service_label_name = f"{service_name}-service"
        required_labels = {
            "traefik.enable": "true",
            "traefik.docker.network": network_name,
            f"traefik.http.routers.{router_name}.rule": f"Host(`{hostname}`)",
            f"traefik.http.routers.{router_name}.entrypoints": "web,websecure",
            f"traefik.http.routers.{router_name}.service": service_label_name,
            f"traefik.http.routers.{router_name}.tls": "true",
            f"traefik.http.services.{service_label_name}.loadbalancer.server.port": port
        }
        tls_strategy = params.get("tls_strategy", "local")
        if tls_strategy == "acme":
            required_labels[f"traefik.http.routers.{router_name}.tls.certresolver"] = "myresolver"
        labels_added: List[str] = []
        for key, value in required_labels.items():
            if key not in labels:
                labels[key] = value
                labels_added.append(key)
        if "networks" not in service:
            service["networks"] = {}
        if network_name not in service["networks"]:
            service["networks"][network_name] = {"ipv4_address": ip_address}
            labels_added.append(f"network:{network_name}")
        if labels_added:
            with open(compose_file, "w") as f:
                yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False)
            logger.info("event=add_labels_to_compose_complete compose=%s labels_added=%s", compose_path, labels_added)
        else:
            logger.info("event=add_labels_to_compose_complete compose=%s no_changes_needed=true", compose_path)
        return {"success": True, "compose_path": compose_path, "labels_added": labels_added}
    except Exception as e:
        logger.error("event=add_labels_to_compose_failed error=%s", str(e))
        return {"success": False, "error": str(e)}
