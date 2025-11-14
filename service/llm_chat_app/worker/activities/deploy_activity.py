import os
import json
import logging
import requests
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from temporalio import activity

logger = logging.getLogger(__name__)

@activity.defn
async def create_railway_project_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    project_name = params.get("project_name", "llm-chat-app")
    
    logger.info("event=railway_create_start project=%s", project_name)
    
    try:
        result = subprocess.run(
            ["railway", "init", "--name", project_name],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            logger.info("event=railway_create_success project=%s", project_name)
            return {"success": True, "project_name": project_name}
        else:
            logger.error("event=railway_create_failed stderr=%s", result.stderr)
            return {"success": False, "error": result.stderr}
            
    except Exception as e:
        logger.exception("event=railway_create_exception error=%s", str(e))
        return {"success": False, "error": str(e)}

@activity.defn
async def set_railway_env_vars_activity(params: Dict[str, Any]) -> bool:
    env_vars = params.get("env_vars", {})
    
    logger.info("event=railway_env_start vars_count=%s", len(env_vars))
    
    try:
        for key, value in env_vars.items():
            result = subprocess.run(
                ["railway", "variables", "set", f"{key}={value}"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error("event=railway_env_failed key=%s stderr=%s", key, result.stderr)
                return False
            
            logger.info("event=railway_env_set key=%s", key)
        
        logger.info("event=railway_env_success count=%s", len(env_vars))
        return True
        
    except Exception as e:
        logger.exception("event=railway_env_exception error=%s", str(e))
        return False

@activity.defn
async def deploy_to_railway_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    project_path = params.get("project_path", ".")
    
    logger.info("event=railway_deploy_start path=%s", project_path)
    
    try:
        result = subprocess.run(
            ["railway", "up", "--detach"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode == 0:
            logger.info("event=railway_deploy_success output=%s", result.stdout[:200])
            
            domain_result = subprocess.run(
                ["railway", "domain"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            deployment_url = domain_result.stdout.strip() if domain_result.returncode == 0 else ""
            
            return {
                "success": True,
                "deployment_url": deployment_url,
                "output": result.stdout
            }
        else:
            logger.error("event=railway_deploy_failed stderr=%s", result.stderr)
            return {"success": False, "error": result.stderr}
            
    except Exception as e:
        logger.exception("event=railway_deploy_exception error=%s", str(e))
        return {"success": False, "error": str(e)}

@activity.defn
async def create_render_blueprint_activity(params: Dict[str, Any]) -> bool:
    project_path = params.get("project_path", ".")
    service_name = params.get("service_name", "llm-chat-app")
    
    logger.info("event=render_blueprint_start path=%s", project_path)
    
    blueprint = {
        "services": [
            {
                "type": "web",
                "name": service_name,
                "env": "docker",
                "plan": "free",
                "dockerfilePath": "./Dockerfile",
                "dockerContext": ".",
                "envVars": [
                    {"key": "CLOUDFLARE_ACCOUNT_ID", "sync": False},
                    {"key": "CLOUDFLARE_API_TOKEN", "sync": False}
                ]
            }
        ]
    }
    
    if params.get("neo4j_uri"):
        blueprint["services"][0]["envVars"].extend([
            {"key": "NEO4J_URI", "value": params["neo4j_uri"]},
            {"key": "NEO4J_USER", "value": params.get("neo4j_user", "neo4j")},
            {"key": "NEO4J_PASSWORD", "value": params.get("neo4j_password", "")}
        ])
    
    try:
        render_yaml_path = Path(project_path) / "render.yaml"
        
        import yaml
        with open(render_yaml_path, "w") as f:
            yaml.dump(blueprint, f, default_flow_style=False)
        
        logger.info("event=render_blueprint_success path=%s", str(render_yaml_path))
        return True
        
    except Exception as e:
        logger.exception("event=render_blueprint_exception error=%s", str(e))
        return False

@activity.defn
async def push_to_github_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    project_path = params.get("project_path", ".")
    repo_name = params.get("repo_name", "llm-chat-app")
    
    logger.info("event=github_push_start path=%s repo=%s", project_path, repo_name)
    
    try:
        git_dir = Path(project_path) / ".git"
        
        if not git_dir.exists():
            subprocess.run(["git", "init"], cwd=project_path, check=True, timeout=30)
            subprocess.run(["git", "add", "."], cwd=project_path, check=True, timeout=30)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=project_path, check=True, timeout=30)
        
        result = subprocess.run(
            ["gh", "repo", "create", repo_name, "--public", "--source=.", "--push"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            repo_url = f"https://github.com/{result.stdout.strip()}"
            logger.info("event=github_push_success repo_url=%s", repo_url)
            return {"success": True, "repo_url": repo_url}
        else:
            logger.error("event=github_push_failed stderr=%s", result.stderr)
            return {"success": False, "error": result.stderr}
            
    except Exception as e:
        logger.exception("event=github_push_exception error=%s", str(e))
        return {"success": False, "error": str(e)}

@activity.defn
async def deploy_to_render_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    api_key = params.get("render_api_key") or os.getenv("RENDER_API_KEY")
    service_name = params.get("service_name", "llm-chat-app")
    repo_url = params.get("repo_url")
    
    if not api_key:
        logger.error("event=render_deploy_no_api_key")
        return {"success": False, "error": "RENDER_API_KEY not set"}
    
    if not repo_url:
        logger.error("event=render_deploy_no_repo")
        return {"success": False, "error": "repo_url required"}
    
    logger.info("event=render_deploy_start service=%s", service_name)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "type": "web_service",
        "name": service_name,
        "ownerId": params.get("owner_id"),
        "repo": repo_url,
        "autoDeploy": "yes",
        "serviceDetails": {
            "env": "docker",
            "envVars": [
                {
                    "key": "CLOUDFLARE_ACCOUNT_ID",
                    "value": params.get("cloudflare_account_id")
                },
                {
                    "key": "CLOUDFLARE_API_TOKEN",
                    "value": params.get("cloudflare_api_token")
                }
            ]
        }
    }
    
    if params.get("neo4j_uri"):
        payload["serviceDetails"]["envVars"].extend([
            {"key": "NEO4J_URI", "value": params["neo4j_uri"]},
            {"key": "NEO4J_USER", "value": params.get("neo4j_user", "neo4j")},
            {"key": "NEO4J_PASSWORD", "value": params.get("neo4j_password", "")}
        ])
    
    try:
        resp = requests.post(
            "https://api.render.com/v1/services",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if resp.status_code in [200, 201]:
            data = resp.json()
            service_url = data.get("service", {}).get("serviceDetails", {}).get("url", "")
            logger.info("event=render_deploy_success url=%s", service_url)
            return {"success": True, "deployment_url": service_url, "response": data}
        else:
            logger.error("event=render_deploy_failed status=%s body=%s", resp.status_code, resp.text)
            return {"success": False, "error": resp.text}
            
    except Exception as e:
        logger.exception("event=render_deploy_exception error=%s", str(e))
        return {"success": False, "error": str(e)}

@activity.defn
async def create_flyio_app_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    app_name = params.get("app_name", "llm-chat-app")
    project_path = params.get("project_path", ".")
    
    logger.info("event=flyio_create_start app=%s", app_name)
    
    try:
        result = subprocess.run(
            ["fly", "apps", "create", app_name, "--org", "personal"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0 or "already exists" in result.stderr.lower():
            logger.info("event=flyio_create_success app=%s", app_name)
            return {"success": True, "app_name": app_name}
        else:
            logger.error("event=flyio_create_failed stderr=%s", result.stderr)
            return {"success": False, "error": result.stderr}
            
    except Exception as e:
        logger.exception("event=flyio_create_exception error=%s", str(e))
        return {"success": False, "error": str(e)}

@activity.defn
async def set_flyio_secrets_activity(params: Dict[str, Any]) -> bool:
    secrets = params.get("secrets", {})
    project_path = params.get("project_path", ".")
    
    logger.info("event=flyio_secrets_start count=%s", len(secrets))
    
    try:
        secret_args = []
        for key, value in secrets.items():
            secret_args.extend([key + "=" + value])
        
        if secret_args:
            result = subprocess.run(
                ["fly", "secrets", "set"] + secret_args,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.error("event=flyio_secrets_failed stderr=%s", result.stderr)
                return False
        
        logger.info("event=flyio_secrets_success count=%s", len(secrets))
        return True
        
    except Exception as e:
        logger.exception("event=flyio_secrets_exception error=%s", str(e))
        return False

@activity.defn
async def deploy_to_flyio_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    project_path = params.get("project_path", ".")
    app_name = params.get("app_name", "llm-chat-app")
    
    logger.info("event=flyio_deploy_start path=%s", project_path)
    
    try:
        result = subprocess.run(
            ["fly", "deploy", "--remote-only"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode == 0:
            deployment_url = f"https://{app_name}.fly.dev"
            logger.info("event=flyio_deploy_success url=%s", deployment_url)
            return {"success": True, "deployment_url": deployment_url}
        else:
            logger.error("event=flyio_deploy_failed stderr=%s", result.stderr)
            return {"success": False, "error": result.stderr}
            
    except Exception as e:
        logger.exception("event=flyio_deploy_exception error=%s", str(e))
        return {"success": False, "error": str(e)}

@activity.defn
async def create_neo4j_aura_instance_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    api_key = params.get("neo4j_aura_api_key") or os.getenv("NEO4J_AURA_API_KEY")
    api_secret = params.get("neo4j_aura_api_secret") or os.getenv("NEO4J_AURA_API_SECRET")
    instance_name = params.get("instance_name", "llm-chat-knowledge-graph")
    
    if not api_key or not api_secret:
        logger.error("event=neo4j_aura_no_credentials")
        return {"success": False, "error": "NEO4J_AURA_API_KEY and NEO4J_AURA_API_SECRET required"}
    
    logger.info("event=neo4j_aura_create_start instance=%s", instance_name)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": instance_name,
        "version": "5",
        "region": "us-east-1",
        "memory": "1GB",
        "type": "professional-db"
    }
    
    try:
        resp = requests.post(
            "https://api.neo4j.io/v1/instances",
            headers=headers,
            json=payload,
            timeout=120
        )
        
        if resp.status_code in [200, 201, 202]:
            data = resp.json()
            instance_id = data.get("data", {}).get("id")
            connection_url = data.get("data", {}).get("connection_url")
            username = data.get("data", {}).get("username", "neo4j")
            password = data.get("data", {}).get("password")
            
            logger.info("event=neo4j_aura_create_success instance_id=%s", instance_id)
            
            return {
                "success": True,
                "instance_id": instance_id,
                "connection_url": connection_url,
                "username": username,
                "password": password
            }
        else:
            logger.error("event=neo4j_aura_create_failed status=%s body=%s", resp.status_code, resp.text)
            return {"success": False, "error": resp.text}
            
    except Exception as e:
        logger.exception("event=neo4j_aura_create_exception error=%s", str(e))
        return {"success": False, "error": str(e)}

@activity.defn
async def check_deployment_health_activity(params: Dict[str, Any]) -> bool:
    import time
    
    url = params.get("url")
    max_attempts = params.get("max_attempts", 30)
    delay = params.get("delay", 10)
    
    if not url:
        logger.error("event=health_check_no_url")
        return False
    
    logger.info("event=health_check_start url=%s", url)
    
    for attempt in range(1, max_attempts + 1):
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code < 400:
                logger.info("event=health_check_success attempt=%s url=%s", attempt, url)
                return True
            logger.warning("event=health_check_status attempt=%s status=%s", attempt, resp.status_code)
        except Exception as e:
            logger.warning("event=health_check_failed attempt=%s error=%s", attempt, str(e)[:100])
        
        if attempt < max_attempts:
            time.sleep(delay)
    
    logger.error("event=health_check_timeout url=%s attempts=%s", url, max_attempts)
    return False

@activity.defn
async def generate_deployment_configs_activity(params: Dict[str, Any]) -> bool:
    project_path = params.get("project_path", ".")
    platforms = params.get("platforms", ["railway", "render", "flyio"])
    
    logger.info("event=generate_configs_start platforms=%s", platforms)
    
    try:
        project_dir = Path(project_path)
        
        if "railway" in platforms:
            railway_config = {
                "$schema": "https://railway.app/railway.schema.json",
                "build": {
                    "builder": "DOCKERFILE",
                    "dockerfilePath": "Dockerfile"
                },
                "deploy": {
                    "startCommand": "streamlit run app/streamlit_app.py --server.port=$PORT --server.address=0.0.0.0",
                    "restartPolicyType": "ON_FAILURE",
                    "restartPolicyMaxRetries": 10
                }
            }
            
            with open(project_dir / "railway.json", "w") as f:
                json.dump(railway_config, f, indent=2)
            
            logger.info("event=config_created platform=railway")
        
        if "render" in platforms:
            import yaml
            
            render_config = {
                "services": [
                    {
                        "type": "web",
                        "name": "llm-chat-app",
                        "env": "docker",
                        "plan": "free",
                        "dockerfilePath": "./Dockerfile",
                        "dockerContext": ".",
                        "envVars": [
                            {"key": "CLOUDFLARE_ACCOUNT_ID", "sync": False},
                            {"key": "CLOUDFLARE_API_TOKEN", "sync": False}
                        ]
                    }
                ]
            }
            
            with open(project_dir / "render.yaml", "w") as f:
                yaml.dump(render_config, f, default_flow_style=False)
            
            logger.info("event=config_created platform=render")
        
        if "flyio" in platforms:
            fly_config = """
app = "llm-chat-app"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[http_service]
  internal_port = 8501
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 512
"""
            
            with open(project_dir / "fly.toml", "w") as f:
                f.write(fly_config)
            
            logger.info("event=config_created platform=flyio")
        
        logger.info("event=generate_configs_success count=%s", len(platforms))
        return True
        
    except Exception as e:
        logger.exception("event=generate_configs_exception error=%s", str(e))
        return False