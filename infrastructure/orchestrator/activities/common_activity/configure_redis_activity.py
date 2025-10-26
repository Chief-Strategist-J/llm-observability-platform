import logging
import os
from pathlib import Path

from temporalio import activity

# Configuration paths
CONFIG_DIR = "/home/j/live/dinesh/llm-chatbot-python/infrastructure/observability_platform/config"
REDIS_CONFIG = os.path.join(CONFIG_DIR, "redis.conf")

logging.basicConfig(level=logging.INFO)

# Redis configuration template
REDIS_CONFIG_TEMPLATE = """# Redis Configuration for Development
# Generated automatically by configure_redis_activity

# Network
bind 0.0.0.0
port 6379
timeout 0
tcp-keepalive 300

# General
daemonize no
supervised no
loglevel notice
logfile ""

# Snapshotting
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb

# Security
# requirepass yourpasswordhere  # Uncomment and set password for production

# Memory management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Append only file
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec

# Disable dangerous commands (uncomment for production)
# rename-command FLUSHDB ""
# rename-command FLUSHALL ""
# rename-command SHUTDOWN SHUTDOWN_REDIS

# Performance tuning
tcp-backlog 511
tcp-reuse-addr yes
latency-monitor-threshold 0

# Modules
loadmodule /usr/lib/redis/modules/redisearch.so
loadmodule /usr/lib/redis/modules/redisgraph.so
loadmodule /usr/lib/redis/modules/redistimeseries.so"""

REDIS_DOCKERFILE = """FROM redis:7-alpine

# Install Redis modules and tools
RUN apk add --no-cache redis

# Copy custom configuration
COPY redis.conf /usr/local/etc/redis/redis.conf

# Expose ports
EXPOSE 6379

# Use custom configuration
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]"""


def ensure_config_directory():
    """Ensure the configuration directory exists"""
    Path(CONFIG_DIR).mkdir(parents=True, exist_ok=True)
    logging.info(f"Ensured config directory exists: {CONFIG_DIR}")


def write_config_file(file_path: str, content: str, config_name: str):
    """Write configuration file with backup and validation"""
    try:
        # Create backup if file exists
        if os.path.exists(file_path):
            backup_path = f"{file_path}.backup"
            with open(file_path, 'r') as src, open(backup_path, 'w') as dst:
                dst.write(src.read())
            logging.info(f"Created backup: {backup_path}")

        # Write new configuration
        with open(file_path, 'w') as f:
            f.write(content)

        # Validate file was written correctly
        with open(file_path, 'r') as f:
            written_content = f.read()

        if written_content == content:
            logging.info(f"Successfully wrote {config_name} configuration")
            return True
        else:
            logging.error(f"Configuration validation failed for {config_name}")
            return False

    except Exception as e:
        logging.exception(f"Failed to write {config_name} configuration: {e}")
        return False


@activity.defn
async def configure_redis_container(service_name: str) -> bool:
    """Configure Redis with development configuration"""
    logging.info(f"Configuring Redis for {service_name}")

    ensure_config_directory()

    success = write_config_file(REDIS_CONFIG, REDIS_CONFIG_TEMPLATE, "Redis")

    if success:
        logging.info("Redis configuration completed successfully")
        logging.info(f"Configuration file created: {REDIS_CONFIG}")
    else:
        logging.error("Redis configuration failed")

    return success


@activity.defn
async def validate_redis_config(service_name: str) -> dict:
    """Validate Redis configuration files"""
    logging.info(f"Validating Redis configuration for {service_name}")

    validation_results = {
        "valid": True,
        "files": {},
        "errors": []
    }

    config_files = {
        "redis": REDIS_CONFIG,
    }

    for config_name, file_path in config_files.items():
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                # Basic Redis config validation
                required_directives = ["port 6379", "bind 0.0.0.0", "maxmemory"]
                missing_directives = []

                for directive in required_directives:
                    if directive not in content:
                        missing_directives.append(directive)

                if missing_directives:
                    validation_results["files"][config_name] = {
                        "exists": True,
                        "valid": False,
                        "missing_directives": missing_directives
                    }
                    validation_results["errors"].append(f"{config_name}: Missing directives: {missing_directives}")
                    validation_results["valid"] = False
                else:
                    validation_results["files"][config_name] = {
                        "exists": True,
                        "valid": True,
                        "size": len(content)
                    }
                logging.info(f"{config_name} configuration is valid")

            except Exception as e:
                validation_results["files"][config_name] = {
                    "exists": True,
                    "valid": False,
                    "error": str(e)
                }
                validation_results["errors"].append(f"{config_name}: {str(e)}")
                validation_results["valid"] = False
                logging.error(f"Error validating {config_name} configuration: {e}")
        else:
            validation_results["files"][config_name] = {
                "exists": False,
                "valid": False,
                "error": "File not found"
            }
            validation_results["errors"].append(f"{config_name}: File not found")
            validation_results["valid"] = False
            logging.error(f"{config_name} configuration file not found")

    logging.info(f"Configuration validation completed: {'PASSED' if validation_results['valid'] else 'FAILED'}")
    return validation_results


@activity.defn
async def update_redis_config(service_name: str, config_updates: dict) -> bool:
    """Update specific Redis configuration parameters"""
    logging.info(f"Updating Redis configuration for {service_name}")

    if not os.path.exists(REDIS_CONFIG):
        logging.error("Redis configuration file not found")
        return False

    try:
        with open(REDIS_CONFIG, 'r') as f:
            content = f.read()

        # Apply updates (simplified - could be enhanced for more complex updates)
        updated_content = content

        # Update maxmemory
        if "maxmemory" in config_updates:
            # Remove existing maxmemory line
            import re
            updated_content = re.sub(r'^maxmemory.*$', '', updated_content, flags=re.MULTILINE)
            # Add new maxmemory line
            updated_content = updated_content.strip() + f"\nmaxmemory {config_updates['maxmemory']}\n"

        # Update maxmemory policy
        if "maxmemory_policy" in config_updates:
            updated_content = re.sub(r'^maxmemory-policy.*$', '', updated_content, flags=re.MULTILINE)
            updated_content = updated_content.strip() + f"\nmaxmemory-policy {config_updates['maxmemory_policy']}\n"

        # Update password
        if "password" in config_updates:
            updated_content = re.sub(r'^# requirepass.*$', '', updated_content, flags=re.MULTILINE)
            updated_content = re.sub(r'^requirepass.*$', '', updated_content, flags=re.MULTILINE)
            if config_updates['password']:
                updated_content = updated_content.strip() + f"\nrequirepass {config_updates['password']}\n"
            else:
                updated_content = updated_content.strip() + "\n# requirepass yourpasswordhere\n"

        if write_config_file(REDIS_CONFIG, updated_content, "Redis (updated)"):
            logging.info(f"Configuration update completed: {len(config_updates)} parameters updated")
            return True
        else:
            logging.error("Configuration update failed")
            return False

    except Exception as e:
        logging.exception(f"Error updating Redis configuration: {e}")
        return False
