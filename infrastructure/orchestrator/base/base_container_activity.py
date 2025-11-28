import os
import subprocess
import time
import yaml
from pathlib import Path
from enum import Enum
from typing import Dict, Optional, List, Any
from dataclasses import dataclass

from .logql_logger import LogQLLogger
from .port_manager import PortManager


class ContainerState(Enum):
    RUNNING = "running"
    EXITED = "exited"
    CREATED = "created"
    RESTARTING = "restarting"
    PAUSED = "paused"
    DEAD = "dead"
    NOT_FOUND = "not_found"
    UNKNOWN = "unknown"


@dataclass
class YAMLContainerConfig:
    yaml_path: Path
    service_name: str
    instance_id: int
    env_file: Optional[Path]
    raw_config: Dict[str, Any]


class YAMLConfigLoader:
    def __init__(self, yaml_path: str, instance_id: int = 0):
        self.yaml_path = Path(yaml_path)
        self.instance_id = instance_id
        self.log = LogQLLogger(f"{__name__}.YAMLConfigLoader")
        self.log.set_trace_id()
    
    def load(self) -> YAMLContainerConfig:
        start_time = time.time()
        self.log.info("yaml_config_load_start", yaml_path=str(self.yaml_path), instance_id=self.instance_id)
        
        try:
            if not self.yaml_path.exists():
                self.log.error("yaml_config_not_found", yaml_path=str(self.yaml_path))
                raise FileNotFoundError(f"YAML config not found: {self.yaml_path}")
            
            with open(self.yaml_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if not config or 'services' not in config:
                self.log.error("yaml_config_invalid", yaml_path=str(self.yaml_path), error="No services defined")
                raise ValueError(f"Invalid Docker Compose YAML: {self.yaml_path}")
            
            service_name = list(config['services'].keys())[0]
            
            env_file = self.yaml_path.parent.parent.parent / '.env'
            
            duration = int((time.time() - start_time) * 1000)
            self.log.info("yaml_config_load_complete", 
                         yaml_path=str(self.yaml_path), 
                         service_name=service_name,
                         instance_id=self.instance_id,
                         duration_ms=duration)
            
            return YAMLContainerConfig(
                yaml_path=self.yaml_path,
                service_name=service_name,
                instance_id=self.instance_id,
                env_file=env_file if env_file.exists() else None,
                raw_config=config
            )
        
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            self.log.exception("yaml_config_load_failed", error=e, 
                             yaml_path=str(self.yaml_path), 
                             duration_ms=duration)
            raise


class YAMLContainerManager:
    def __init__(self, yaml_path: str, instance_id: int = 0, env_vars: Optional[Dict[str, str]] = None):
        self.yaml_path = Path(yaml_path)
        self.instance_id = instance_id
        self.env_vars = env_vars or {}
        
        self.log = LogQLLogger(f"{__name__}.YAMLContainerManager")
        self.trace_id = self.log.set_trace_id()
        
        loader = YAMLConfigLoader(str(self.yaml_path), instance_id)
        self.config = loader.load()
        
        self.port_manager = PortManager()
        
        self.log.info("container_manager_initialized",
                     service=self.config.service_name,
                     instance_id=self.instance_id,
                     yaml_path=str(self.yaml_path),
                     trace_id=self.trace_id)
    
    def _build_env(self) -> Dict[str, str]:
        env = os.environ.copy()
        
        env[f"{self.config.service_name.upper().replace('-', '_')}_INSTANCE_ID"] = str(self.instance_id)
        
        for key, value in self.env_vars.items():
            env[key] = value
        
        self.log.debug("env_variables_prepared",
                      service=self.config.service_name,
                      instance_id=self.instance_id,
                      env_count=len(self.env_vars))
        
        return env
    
    def _run_docker_compose(self, args: List[str], check: bool = True, capture_output: bool = True) -> subprocess.CompletedProcess:
        start_time = time.time()
        
        cmd = ['docker-compose', '-f', str(self.yaml_path)]
        
        if self.config.env_file:
            cmd.extend(['--env-file', str(self.config.env_file)])
        
        cmd.extend(args)
        
        cmd_str = ' '.join(cmd)
        self.log.info("docker_compose_command_start",
                     service=self.config.service_name,
                     instance_id=self.instance_id,
                     command=cmd_str,
                     trace_id=self.trace_id)
        
        try:
            result = subprocess.run(
                cmd,
                env=self._build_env(),
                capture_output=capture_output,
                text=True,
                check=check
            )
            
            duration = int((time.time() - start_time) * 1000)
            
            self.log.info("docker_compose_command_success",
                         service=self.config.service_name,
                         instance_id=self.instance_id,
                         command=cmd_str,
                         return_code=result.returncode,
                         duration_ms=duration,
                         trace_id=self.trace_id)
            
            if result.stdout:
                self.log.debug("docker_compose_stdout",
                              service=self.config.service_name,
                              instance_id=self.instance_id,
                              stdout=result.stdout.strip())
            
            if result.stderr:
                self.log.debug("docker_compose_stderr",
                              service=self.config.service_name,
                              instance_id=self.instance_id,
                              stderr=result.stderr.strip())
            
            return result
        
        except subprocess.CalledProcessError as e:
            duration = int((time.time() - start_time) * 1000)
            
            self.log.error("docker_compose_command_failed",
                          service=self.config.service_name,
                          instance_id=self.instance_id,
                          command=cmd_str,
                          return_code=e.returncode,
                          duration_ms=duration,
                          error=e,
                          stdout=e.stdout,
                          stderr=e.stderr,
                          trace_id=self.trace_id)
            raise
        
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            
            self.log.exception("docker_compose_command_exception",
                              service=self.config.service_name,
                              instance_id=self.instance_id,
                              command=cmd_str,
                              duration_ms=duration,
                              error=e,
                              trace_id=self.trace_id)
            raise
    
    def get_status(self) -> ContainerState:
        start_time = time.time()
        
        self.log.info("container_status_check_start",
                     service=self.config.service_name,
                     instance_id=self.instance_id,
                     trace_id=self.trace_id)
        
        try:
            result = self._run_docker_compose(['ps', '-q'], check=False, capture_output=True)
            
            if not result.stdout.strip():
                self.log.info("container_status_check_complete",
                             service=self.config.service_name,
                             instance_id=self.instance_id,
                             status=ContainerState.NOT_FOUND.value,
                             duration_ms=int((time.time() - start_time) * 1000))
                return ContainerState.NOT_FOUND
            
            container_id = result.stdout.strip()
            
            inspect_result = subprocess.run(
                ['docker', 'inspect', '-f', '{{.State.Status}}', container_id],
                capture_output=True,
                text=True,
                check=False
            )
            
            if inspect_result.returncode == 0:
                status_str = inspect_result.stdout.strip()
                
                try:
                    state = ContainerState(status_str)
                except ValueError:
                    state = ContainerState.UNKNOWN
                
                duration = int((time.time() - start_time) * 1000)
                self.log.info("container_status_check_complete",
                             service=self.config.service_name,
                             instance_id=self.instance_id,
                             container_id=container_id,
                             status=state.value,
                             duration_ms=duration,
                             trace_id=self.trace_id)
                
                return state
            
            return ContainerState.UNKNOWN
        
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            self.log.exception("container_status_check_failed",
                              service=self.config.service_name,
                              instance_id=self.instance_id,
                              duration_ms=duration,
                              error=e,
                              trace_id=self.trace_id)
            return ContainerState.UNKNOWN
    
    def start(self, restart_if_running: bool = True) -> bool:
        start_time = time.time()
        
        self.log.info("container_start_requested",
                     service=self.config.service_name,
                     instance_id=self.instance_id,
                     restart_if_running=restart_if_running,
                     trace_id=self.trace_id)
        
        try:
            current_state = self.get_status()
            
            if current_state == ContainerState.RUNNING:
                if restart_if_running:
                    self.log.info("container_already_running_restarting",
                                 service=self.config.service_name,
                                 instance_id=self.instance_id,
                                 trace_id=self.trace_id)
                    return self.restart()
                else:
                    self.log.info("container_already_running_skip",
                                 service=self.config.service_name,
                                 instance_id=self.instance_id,
                                 trace_id=self.trace_id)
                    return True
            
            self._run_docker_compose(['up', '-d'])
            
            duration = int((time.time() - start_time) * 1000)
            
            final_state = self.get_status()
            
            success = final_state == ContainerState.RUNNING
            
            self.log.info("container_start_complete",
                         service=self.config.service_name,
                         instance_id=self.instance_id,
                         initial_state=current_state.value,
                         final_state=final_state.value,
                         success=success,
                         duration_ms=duration,
                         trace_id=self.trace_id)
            
            return success
        
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            self.log.exception("container_start_failed",
                              service=self.config.service_name,
                              instance_id=self.instance_id,
                              duration_ms=duration,
                              error=e,
                              trace_id=self.trace_id)
            return False
    
    def stop(self, force: bool = True, timeout: int = 10) -> bool:
        start_time = time.time()
        
        self.log.info("container_stop_requested",
                     service=self.config.service_name,
                     instance_id=self.instance_id,
                     force=force,
                     timeout=timeout,
                     trace_id=self.trace_id)
        
        try:
            current_state = self.get_status()
            
            if current_state == ContainerState.NOT_FOUND:
                self.log.info("container_not_found_skip_stop",
                             service=self.config.service_name,
                             instance_id=self.instance_id,
                             trace_id=self.trace_id)
                return True
            
            if force:
                self._run_docker_compose(['kill'])
                self.log.info("container_force_killed",
                             service=self.config.service_name,
                             instance_id=self.instance_id,
                             trace_id=self.trace_id)
            else:
                self._run_docker_compose(['stop', '-t', str(timeout)])
                self.log.info("container_graceful_stopped",
                             service=self.config.service_name,
                             instance_id=self.instance_id,
                             timeout=timeout,
                             trace_id=self.trace_id)
            
            duration = int((time.time() - start_time) * 1000)
            
            final_state = self.get_status()
            
            success = final_state in [ContainerState.EXITED, ContainerState.NOT_FOUND]
            
            self.log.info("container_stop_complete",
                         service=self.config.service_name,
                         instance_id=self.instance_id,
                         initial_state=current_state.value,
                         final_state=final_state.value,
                         force=force,
                         success=success,
                         duration_ms=duration,
                         trace_id=self.trace_id)
            
            return success
        
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            self.log.exception("container_stop_failed",
                              service=self.config.service_name,
                              instance_id=self.instance_id,
                              duration_ms=duration,
                              error=e,
                              trace_id=self.trace_id)
            return False
    
    def restart(self) -> bool:
        start_time = time.time()
        
        self.log.info("container_restart_requested",
                     service=self.config.service_name,
                     instance_id=self.instance_id,
                     trace_id=self.trace_id)
        
        try:
            current_state = self.get_status()
            
            self._run_docker_compose(['restart'])
            
            duration = int((time.time() - start_time) * 1000)
            
            final_state = self.get_status()
            
            success = final_state == ContainerState.RUNNING
            
            self.log.info("container_restart_complete",
                         service=self.config.service_name,
                         instance_id=self.instance_id,
                         initial_state=current_state.value,
                         final_state=final_state.value,
                         success=success,
                         duration_ms=duration,
                         trace_id=self.trace_id)
            
            return success
        
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            self.log.exception("container_restart_failed",
                              service=self.config.service_name,
                              instance_id=self.instance_id,
                              duration_ms=duration,
                              error=e,
                              trace_id=self.trace_id)
            return False
    
    def delete(self, remove_volumes: bool = True, remove_images: bool = True, remove_networks: bool = False) -> bool:
        start_time = time.time()
        
        self.log.info("container_delete_requested",
                     service=self.config.service_name,
                     instance_id=self.instance_id,
                     remove_volumes=remove_volumes,
                     remove_images=remove_images,
                     remove_networks=remove_networks,
                     trace_id=self.trace_id)
        
        try:
            current_state = self.get_status()
            
            self.log.info("container_delete_stopping_first",
                         service=self.config.service_name,
                         instance_id=self.instance_id,
                         current_state=current_state.value,
                         trace_id=self.trace_id)
            
            self.stop(force=True)
            
            down_args = ['down']
            
            if remove_volumes:
                down_args.append('--volumes')
                self.log.info("container_delete_removing_volumes",
                             service=self.config.service_name,
                             instance_id=self.instance_id,
                             trace_id=self.trace_id)
            
            if remove_images:
                down_args.append('--rmi')
                down_args.append('all')
                self.log.info("container_delete_removing_images",
                             service=self.config.service_name,
                             instance_id=self.instance_id,
                             trace_id=self.trace_id)
            
            self._run_docker_compose(down_args)
            
            if remove_networks:
                self.log.info("container_delete_removing_networks",
                             service=self.config.service_name,
                             instance_id=self.instance_id,
                             trace_id=self.trace_id)
                
                networks = self.config.raw_config.get('networks', {})
                for network_name in networks.keys():
                    try:
                        result = subprocess.run(
                            ['docker', 'network', 'rm', network_name],
                            capture_output=True,
                            text=True,
                            check=False
                        )
                        if result.returncode == 0:
                            self.log.info("network_removed",
                                         service=self.config.service_name,
                                         network=network_name,
                                         trace_id=self.trace_id)
                        else:
                            self.log.warning("network_removal_failed",
                                           service=self.config.service_name,
                                           network=network_name,
                                           stderr=result.stderr,
                                           trace_id=self.trace_id)
                    except Exception as e:
                        self.log.error("network_removal_exception",
                                      service=self.config.service_name,
                                      network=network_name,
                                      error=e,
                                      trace_id=self.trace_id)
            
            duration = int((time.time() - start_time) * 1000)
            
            final_state = self.get_status()
            
            success = final_state == ContainerState.NOT_FOUND
            
            self.log.info("container_delete_complete",
                         service=self.config.service_name,
                         instance_id=self.instance_id,
                         initial_state=current_state.value,
                         final_state=final_state.value,
                         volumes_removed=remove_volumes,
                         images_removed=remove_images,
                         networks_removed=remove_networks,
                         success=success,
                         duration_ms=duration,
                         trace_id=self.trace_id)
            
            return success
        
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            self.log.exception("container_delete_failed",
                              service=self.config.service_name,
                              instance_id=self.instance_id,
                              duration_ms=duration,
                              error=e,
                              trace_id=self.trace_id)
            return False


class YAMLBaseService:
    def __init__(self, yaml_path: str, instance_id: int = 0, env_vars: Optional[Dict[str, str]] = None):
        self.manager = YAMLContainerManager(yaml_path, instance_id, env_vars)
        self.log = LogQLLogger(f"{__name__}.{self.__class__.__name__}")
        self.log.set_trace_id()
    
    def start(self, restart_if_running: bool = True) -> bool:
        return self.manager.start(restart_if_running)
    
    def stop(self, force: bool = True, timeout: int = 10) -> bool:
        return self.manager.stop(force, timeout)
    
    def restart(self) -> bool:
        return self.manager.restart()
    
    def delete(self, remove_volumes: bool = True, remove_images: bool = True, remove_networks: bool = False) -> bool:
        return self.manager.delete(remove_volumes, remove_images, remove_networks)
    
    def get_status(self) -> ContainerState:
        return self.manager.get_status()


class BaseContainerManager:
    pass
