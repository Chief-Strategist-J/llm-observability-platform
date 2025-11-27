#!/usr/bin/env python3
"""
Example: Running a Redis container from YAML configuration.
"""

from infrastructure.orchestrator.base.base_container_activity import YAMLBaseService

def main():
    # Create service from YAML configuration
    service = YAMLBaseService(
        yaml_file_path="infrastructure/orchestrator/config/docker/redis-dynamic-docker.yaml",
        service_name="redis",  # Optional: uses first service if not specified
        env_vars={
            "REDIS_PORT": "6379",
        },
        instance_id="1"  # For multi-instance deployments
    )
    
    print(f"Container: {service.config.container_name}")
    print(f"Image: {service.config.image}")
    print(f"Ports: {service.config.ports}")
    print(f"Networks: {service.config.networks}")
    
    # Start the container
    print("\nStarting container...")
    service.run()
    
    # Get logs
    print("\nFetching logs...")
    logs = service.logs()
    print(logs[:500])  # Print first 500 characters
    
    # Stop the container
    print("\nStopping container...")
    service.stop()
    
    print("\n✓ Example completed successfully!")


if __name__ == "__main__":
    main()
