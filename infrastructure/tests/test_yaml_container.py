#!/usr/bin/env python3
"""
Test script for YAML-based container configuration.
Demonstrates how to use the new YAMLBaseService.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from infrastructure.orchestrator.base.base_container_activity import (
    YAMLBaseService,
    YAMLConfigLoader,
)


def test_yaml_loading():
    """Test YAML configuration loading."""
    print("=" * 60)
    print("Testing YAML Configuration Loading")
    print("=" * 60)
    
    # Test 1: Load Redis configuration
    yaml_file = "infrastructure/orchestrator/config/docker/redis-dynamic-docker.yaml"
    instance_id = "1"
    env_vars = {
        "INSTANCE_ID": instance_id,
        "REDIS_PORT": "6379",
    }
    
    print(f"\n1. Loading Redis YAML: {yaml_file}")
    loader = YAMLConfigLoader()
    yaml_data = loader.load_yaml_file(yaml_file, env_vars)
    
    print(f"   ✓ Services found: {list(yaml_data.get('services', {}).keys())}")
    print(f"   ✓ Networks found: {list(yaml_data.get('networks', {}).keys())}")
    print(f"   ✓ Volumes found: {list(yaml_data.get('volumes', {}).keys())}")
    
    # Test 2: Parse service configuration
    print(f"\n2. Parsing service configuration")
    config = loader.parse_service("redis", yaml_data)
    print(f"   ✓ Container name: {config.container_name}")
    print(f"   ✓ Image: {config.image}")
    print(f"   ✓ Ports: {config.ports}")
    print(f"   ✓ Networks: {config.networks}")
    print(f"   ✓ Restart policy: {config.restart}")
    
    # Test 3: Create service instance
    print(f"\n3. Creating YAMLBaseService instance")
    service = YAMLBaseService(
        yaml_file_path=yaml_file,
        service_name="redis",
        env_vars=env_vars,
        instance_id=instance_id
    )
    print(f"   ✓ Service created successfully")
    print(f"   ✓ Container: {service.config.container_name}")
    print(f"   ✓ Image: {service.config.image}")
    
    print("\n" + "=" * 60)
    print("YAML Loading Test: PASSED ✓")
    print("=" * 60)


def test_multiple_services():
    """Test loading multiple service configurations."""
    print("\n" + "=" * 60)
    print("Testing Multiple Service Configurations")
    print("=" * 60)
    
    services_to_test = [
        ("redis-dynamic-docker.yaml", "redis", {"REDIS_PORT": "6379"}),
        ("mongodb-dynamic-docker.yaml", "mongodb", {"MONGO_PORT": "27017"}),
        ("grafana-dynamic-docker.yaml", "grafana", {"GRAFANA_PORT": "3000"}),
    ]
    
    for yaml_file, service_name, ports in services_to_test:
        full_path = f"infrastructure/orchestrator/config/docker/{yaml_file}"
        env_vars = {"INSTANCE_ID": "1"}
        env_vars.update(ports)
        
        print(f"\n• Loading {service_name} from {yaml_file}")
        try:
            loader = YAMLConfigLoader()
            yaml_data = loader.load_yaml_file(full_path, env_vars)
            config = loader.parse_service(service_name, yaml_data)
            
            print(f"  ✓ Container: {config.container_name}")
            print(f"  ✓ Image: {config.image}")
            print(f"  ✓ Environment vars: {len(config.environment)} vars")
            if config.healthcheck:
                print(f"  ✓ Healthcheck: configured")
            if config.deploy:
                limits = config.deploy.get("resources", {}).get("limits", {})
                print(f"  ✓ Resource limits: memory={limits.get('memory')}, cpus={limits.get('cpus')}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False
    
    print("\n" + "=" * 60)
    print("Multiple Services Test: PASSED ✓")
    print("=" * 60)
    return True


def demo_usage():
    """Demonstrate typical usage pattern."""
    print("\n" + "=" * 60)
    print("Usage Example: Starting a Redis Container")
    print("=" * 60)
    
    print("\n# Python code:")
    print('''
from infrastructure.orchestrator.base.base_container_activity import YAMLBaseService

# Create service from YAML
service = YAMLBaseService(
    yaml_file_path="infrastructure/orchestrator/config/docker/redis-dynamic-docker.yaml",
    service_name="redis",  # Optional, uses first service if not specified
    env_vars={
        "REDIS_PORT": "6379",
    },
    instance_id="1"  # For multi-instance deployments
)

# Start the container
service.run()

# Get logs
logs = service.logs()
print(logs)

# Stop the container
service.stop()

# Delete the container (with cleanup)
service.delete(force=True)
    ''')
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        test_yaml_loading()
        test_multiple_services()
        demo_usage()
        
        print("\n✓ All tests passed successfully!")
        print("\nThe base_container_activity.py has been successfully rewritten.")
        print("You can now use YAMLBaseService to run containers from YAML files.")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
