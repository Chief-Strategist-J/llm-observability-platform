from pathlib import Path
from temporalio import activity
from infrastructure.orchestrator.base.logql_logger import LogQLLogger
from typing import Set
import yaml


@activity.defn(name="discover_service_hostnames_activity")
async def discover_service_hostnames_activity(params: dict) -> dict:
    """
    Discovers all Docker services that have Traefik routing enabled.
    
    This activity:
    1. Scans all *-docker.yaml files in config/docker/
    2. Finds services with traefik.enable labels
    3. Generates scaibu.* hostnames for all discovered services
    
    Returns:
        dict: {
            "success": bool,
            "service_names": List[str],  # e.g. ["grafana", "prometheus", "temporal"]
            "hostnames": List[str],      # e.g. ["scaibu.grafana", "scaibu.prometheus"]
            "count": int
        }
    """
    log = LogQLLogger("discover_service_hostnames_activity")
    trace_id = log.set_trace_id()
    
    config_dir = Path(__file__).parent.parent.parent / "config" / "docker"
    
    log.info(
        event="activity_start",
        trace_id=trace_id,
        config_dir=str(config_dir)
    )
    
    service_names: Set[str] = set()
    
    # Scan all service YAML files
    yaml_files = list(config_dir.glob("*-docker.yaml"))
    yaml_files.extend(config_dir.parent.glob("temporal-orchestrator-compose.yaml"))
    
    log.info(
        event="scanning_files",
        trace_id=trace_id,
        file_count=len(yaml_files)
    )
    
    for yaml_file in yaml_files:
        try:
            with open(yaml_file, 'r') as f:
                content = f.read()
                
            config = yaml.safe_load(content)
            
            if not config or 'services' not in config:
                continue
                
            # Check each service in the YAML file
            for service_name, service_config in config.get('services', {}).items():
                if not isinstance(service_config, dict):
                    continue
                    
                labels = service_config.get('labels', {})
                if not labels:
                    continue
                
                # Check if Traefik is enabled
                has_traefik_enabled = False
                for label_key in labels.keys():
                    if 'traefik.enable' in str(label_key):
                        label_value = labels[label_key]
                        if label_value == "true" or label_value is True:
                            has_traefik_enabled = True
                            break
                
                # Only include services with Traefik routing
                if has_traefik_enabled:
                    clean_name = service_name.replace('-instance', '')
                    
                    # Map service names to scaibu hostname equivalents
                    # Only special cases that need transformation
                    name_mappings = {
                        'temporal-ui': 'temporal',                    # temporal-ui → scaibu.temporal
                        'opentelemetry-collector': 'otel',           # opentelemetry-collector → scaibu.otel
                        'mongo-express': 'mongo-express',            # mongo-express → scaibu.mongo-express (no change)
                        'argocd-server': 'argocd',                   # argocd-server → scaibu.argocd
                    }
                    
                    # All other services use their name as-is:
                    # grafana → scaibu.grafana
                    # prometheus → scaibu.prometheus
                    # loki → scaibu.loki
                    # etc.
                    
                    clean_name = name_mappings.get(clean_name, clean_name)
                    service_names.add(clean_name)
                    
                    log.debug(
                        event="service_discovered",
                        trace_id=trace_id,
                        original_name=service_name,
                        mapped_name=clean_name
                    )
                    
        except Exception as e:
            log.error(
                event="file_parse_error",
                trace_id=trace_id,
                file=str(yaml_file),
                error=str(e)
            )
            continue
    
    # Always add traefik itself
    service_names.add('traefik')
    
    # Generate scaibu.* hostnames
    hostnames = [f"scaibu.{name}" for name in sorted(service_names)]
    
    log.info(
        event="activity_complete",
        trace_id=trace_id,
        service_count=len(service_names),
        hostname_count=len(hostnames),
        services=sorted(list(service_names))
    )
    
    return {
        "success": True,
        "service_names": sorted(list(service_names)),
        "hostnames": hostnames,
        "count": len(hostnames)
    }


@activity.defn(name="configure_etc_hosts_activity")
async def configure_etc_hosts_activity(params: dict) -> dict:
    """
    Updates /etc/hosts with all scaibu.* hostnames.
    
    This activity:
    1. Creates a backup of /etc/hosts
    2. Removes any existing scaibu.* entries
    3. Adds all scaibu.* hostnames pointing to 127.0.0.1
    
    Args:
        params: {
            "hostnames": List[str]  # e.g. ["scaibu.grafana", "scaibu.prometheus"]
        }
    
    Returns:
        dict: {
            "success": bool,
            "hostnames_configured": int,
            "backup_path": str
        }
    
    Requires: sudo permissions
    """
    log = LogQLLogger("configure_etc_hosts_activity")
    trace_id = log.set_trace_id()
    
    import subprocess
    import tempfile
    from datetime import datetime
    
    hostnames = params.get("hostnames", [])
    if not hostnames:
        log.error(event="missing_hostnames", trace_id=trace_id)
        return {"success": False, "error": "No hostnames provided"}
    
    log.info(
        event="activity_start",
        trace_id=trace_id,
        hostname_count=len(hostnames)
    )
    
    hosts_file = "/etc/hosts"
    backup_dir = "/var/backups/scaibu-hosts-backups"
    
    try:
        # Create backup directory
        subprocess.run(["sudo", "mkdir", "-p", backup_dir], check=True)
        
        # Create timestamped backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{backup_dir}/hosts.backup.{timestamp}"
        subprocess.run(["sudo", "cp", hosts_file, backup_path], check=True)
        
        log.info(
            event="backup_created",
            trace_id=trace_id,
            backup_path=backup_path
        )
        
        # Read current /etc/hosts and filter out scaibu.* entries
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.hosts') as tmp:
            result = subprocess.run(
                f"sudo cat {hosts_file}",
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Write all lines except scaibu.* entries
            for line in result.stdout.split('\n'):
                if any(hostname in line for hostname in hostnames):
                    continue  # Skip existing scaibu entries
                tmp.write(line + '\n')
            
            # Add all scaibu.* hostnames on one line
            canonical_line = "127.0.0.1 " + " ".join(hostnames)
            tmp.write(canonical_line + '\n')
            tmp_path = tmp.name
        
        # Replace /etc/hosts with updated version
        subprocess.run(["sudo", "cp", tmp_path, hosts_file], check=True)
        subprocess.run(["sudo", "chmod", "644", hosts_file], check=True)
        subprocess.run(["rm", "-f", tmp_path], check=True)
        
        log.info(
            event="hosts_file_updated",
            trace_id=trace_id,
            hostnames_added=len(hostnames)
        )
        
        return {
            "success": True,
            "hostnames_configured": len(hostnames),
            "backup_path": backup_path
        }
        
    except Exception as e:
        log.error(
            event="configuration_failed",
            trace_id=trace_id,
            error=str(e)
        )
        return {
            "success": False,
            "error": str(e)
        }
