import os
import sys
import logging
import yaml
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import socket
from datetime import datetime

logger = logging.getLogger(__name__)

class PortManager:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.config_path = Path(__file__).parent.parent / "dynamicconfig" / "port_registry.yaml"
            self.config: Dict = {}
            self.allocated_ports: Dict[str, Dict[int, int]] = {}
            self._load_config()
            PortManager._initialized = True
            logger.info("port_manager_initialized config_path=%s", self.config_path)
    
    def _load_config(self) -> None:
        logger.debug("port_manager_load_config_start path=%s", self.config_path)
        try:
            if not self.config_path.exists():
                logger.error("port_manager_config_not_found path=%s", self.config_path)
                raise FileNotFoundError(f"Port registry not found: {self.config_path}")
            
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            logger.info("port_manager_config_loaded services_count=%s", len([k for k in self.config.keys() if not k.startswith('_')]))
        except Exception as e:
            logger.exception("port_manager_load_config_error error=%s", e)
            raise
    
    def get_port(self, service_name: str, instance_id: int = 0, port_type: str = "port") -> int:
        logger.debug("port_manager_get_port service=%s instance=%s type=%s", service_name, instance_id, port_type)
        
        if service_name not in self.config:
            logger.error("port_manager_service_not_found service=%s", service_name)
            raise ValueError(f"Service '{service_name}' not found in port registry")
        
        service_config = self.config[service_name]
        
        if port_type not in service_config:
            logger.error("port_manager_port_type_not_found service=%s type=%s available=%s", 
                        service_name, port_type, list(service_config.keys()))
            raise ValueError(f"Port type '{port_type}' not found for service '{service_name}'")
        
        base_port = service_config[port_type]
        increment = service_config.get('instance_increment', 100)
        max_instances = service_config.get('max_instances', 10)
        
        if instance_id < 0:
            logger.error("port_manager_invalid_instance_id service=%s instance=%s", service_name, instance_id)
            raise ValueError(f"Instance ID must be >= 0, got {instance_id}")
        
        if instance_id >= max_instances:
            logger.warning("port_manager_instance_exceeds_max service=%s instance=%s max=%s", 
                          service_name, instance_id, max_instances)
        
        calculated_port = base_port + (instance_id * increment)
        
        if service_name not in self.allocated_ports:
            self.allocated_ports[service_name] = {}
        self.allocated_ports[service_name][instance_id] = calculated_port
        
        logger.info("port_manager_port_allocated service=%s instance=%s type=%s port=%s base=%s increment=%s", 
                   service_name, instance_id, port_type, calculated_port, base_port, increment)
        
        return calculated_port
    
    def get_ports(self, service_name: str, instance_id: int = 0) -> Dict[str, int]:
        logger.debug("port_manager_get_ports_multi service=%s instance=%s", service_name, instance_id)
        
        if service_name not in self.config:
            logger.error("port_manager_service_not_found service=%s", service_name)
            raise ValueError(f"Service '{service_name}' not found in port registry")
        
        service_config = self.config[service_name]
        ports = {}
        
        for key, value in service_config.items():
            if isinstance(value, int) and not key.startswith('_') and 'port' in key:
                port_type = key
                ports[port_type] = self.get_port(service_name, instance_id, port_type)
        
        logger.info("port_manager_ports_allocated_multi service=%s instance=%s ports=%s", 
                   service_name, instance_id, ports)
        
        return ports
    
    def check_port_available(self, port: int) -> bool:
        logger.debug("port_manager_check_availability port=%s", port)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('0.0.0.0', port))
                logger.debug("port_manager_port_available port=%s", port)
                return True
        except OSError:
            logger.warning("port_manager_port_unavailable port=%s", port)
            return False
    
    def get_service_info(self, service_name: str) -> Dict:
        logger.debug("port_manager_get_service_info service=%s", service_name)
        
        if service_name not in self.config:
            logger.error("port_manager_service_not_found service=%s", service_name)
            raise ValueError(f"Service '{service_name}' not found in port registry")
        
        return self.config[service_name].copy()
    
    def list_services(self) -> List[str]:
        logger.debug("port_manager_list_services")
        services = [k for k in self.config.keys() if not k.startswith('_')]
        logger.info("port_manager_services_listed count=%s", len(services))
        return services
    
    def get_all_allocated_ports(self) -> Dict[str, Dict[int, int]]:
        logger.debug("port_manager_get_all_allocated")
        return self.allocated_ports.copy()
    
    def validate_instance(self, service_name: str, instance_id: int) -> Tuple[bool, str]:
        logger.debug("port_manager_validate_instance service=%s instance=%s", service_name, instance_id)
        
        if service_name not in self.config:
            msg = f"Service '{service_name}' not found in port registry"
            logger.error("port_manager_validation_failed service=%s error=%s", service_name, msg)
            return False, msg
        
        service_config = self.config[service_name]
        max_instances = service_config.get('max_instances', 10)
        
        if instance_id < 0:
            msg = f"Instance ID must be >= 0, got {instance_id}"
            logger.error("port_manager_validation_failed service=%s error=%s", service_name, msg)
            return False, msg
        
        if instance_id >= max_instances:
            msg = f"Instance ID {instance_id} exceeds max_instances {max_instances}"
            logger.warning("port_manager_validation_warning service=%s warning=%s", service_name, msg)
            return True, msg
        
        logger.debug("port_manager_validation_success service=%s instance=%s", service_name, instance_id)
        return True, "Valid"


def get_port_manager() -> PortManager:
    return PortManager()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
    
    pm = get_port_manager()
    
    print("\n=== Port Manager Test ===\n")
    
    print("Available services:")
    for service in pm.list_services():
        print(f"  - {service}")
    
    print("\n--- Testing Kafka ---")
    kafka_broker = pm.get_port("kafka", 0, "broker_port")
    kafka_controller = pm.get_port("kafka", 0, "controller_port")
    print(f"Kafka Instance 0: broker={kafka_broker}, controller={kafka_controller}")
    
    kafka_broker_1 = pm.get_port("kafka", 1, "broker_port")
    kafka_controller_1 = pm.get_port("kafka", 1, "controller_port")
    print(f"Kafka Instance 1: broker={kafka_broker_1}, controller={kafka_controller_1}")
    
    print("\n--- Testing MongoDB ---")
    mongo_0 = pm.get_port("mongodb", 0)
    mongo_1 = pm.get_port("mongodb", 1)
    mongo_2 = pm.get_port("mongodb", 2)
    print(f"MongoDB Instance 0: {mongo_0}")
    print(f"MongoDB Instance 1: {mongo_1}")
    print(f"MongoDB Instance 2: {mongo_2}")
    
    print("\n--- Testing Multiple Ports (Neo4j) ---")
    neo4j_ports = pm.get_ports("neo4j", 0)
    print(f"Neo4j Instance 0 ports: {neo4j_ports}")
    
    print("\n--- All Allocated Ports ---")
    for service, instances in pm.get_all_allocated_ports().items():
        print(f"{service}:")
        for instance_id, port in instances.items():
            print(f"  Instance {instance_id}: {port}")
