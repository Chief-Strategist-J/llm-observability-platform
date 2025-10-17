#!/usr/bin/env python3
"""Simple autonomous script to stop and clean up ai-proxy-service containers.

This script directly uses Docker commands to stop and remove containers, volumes,
networks, and images without requiring complex module imports.

"""

import asyncio
import logging
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def stop_and_clean_containers():
    """
    Stop and clean up all ai-proxy-service related Docker resources.
    """
    logger.info("Starting autonomous cleanup of ai-proxy-service containers...")

    # Get container IDs first, then operate on them
    container_ids = await _get_container_ids("ai-proxy")
    if container_ids:
        # Stop containers
        await _stop_containers(container_ids)
        # Remove containers
        await _remove_containers(container_ids)

    # Remove images (including specific ones by ID)
    await _remove_images("ai-proxy")
    await _remove_specific_image("a851efa06dc0")  # Remove the specific image mentioned

    # Remove networks
    await _remove_networks("ai-proxy")
    await _remove_specific_network(
        "ai-proxy-service_default"
    )  # Remove the specific network

    # Clean up volumes
    await _cleanup_volumes()

    logger.info("Autonomous cleanup completed!")


async def _get_container_ids(name_filter):
    """
    Get container IDs for containers matching the name filter.
    """
    try:
        result = subprocess.run(
            ["docker", "ps", "-aq", "-f", f"name={name_filter}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            container_ids = [
                cid.strip() for cid in result.stdout.strip().split("\n") if cid.strip()
            ]
            logger.info(
                f"Found {len(container_ids)} containers matching '{name_filter}'"
            )
            return container_ids
        logger.warning(f"Error listing containers: {result.stderr}")
        return []
    except Exception as e:
        logger.error(f"Error getting container IDs: {e}")
        return []


async def _stop_containers(container_ids):
    """
    Stop containers by their IDs.
    """
    for container_id in container_ids:
        try:
            logger.info(f"Stopping container {container_id[:12]}...")
            result = subprocess.run(
                ["docker", "stop", container_id],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                logger.info(f"Stopped container {container_id[:12]}")
            else:
                logger.warning(
                    f"Error stopping container {container_id[:12]}: {result.stderr}"
                )
        except Exception as e:
            logger.error(f"Failed to stop container {container_id[:12]}: {e}")


async def _remove_containers(container_ids):
    """
    Remove containers by their IDs.
    """
    for container_id in container_ids:
        try:
            logger.info(f"Removing container {container_id[:12]}...")
            result = subprocess.run(
                ["docker", "rm", container_id],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                logger.info(f"Removed container {container_id[:12]}")
            else:
                logger.warning(
                    f"Error removing container {container_id[:12]}: {result.stderr}"
                )
        except Exception as e:
            logger.error(f"Failed to remove container {container_id[:12]}: {e}")


async def _remove_images(name_filter):
    """
    Remove images matching the name filter.
    """
    try:
        logger.info(f"Removing images matching '{name_filter}'...")
        result = subprocess.run(
            ["docker", "images", "-q", name_filter],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            image_ids = [
                iid.strip() for iid in result.stdout.strip().split("\n") if iid.strip()
            ]
            for image_id in image_ids:
                try:
                    logger.info(f"Removing image {image_id[:12]}...")
                    remove_result = subprocess.run(
                        ["docker", "rmi", image_id, "-f"],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if remove_result.returncode == 0:
                        logger.info(f"Removed image {image_id[:12]}")
                    else:
                        logger.warning(
                            f"Error removing image {image_id[:12]}: {remove_result.stderr}"
                        )
                except Exception as e:
                    logger.error(f"Failed to remove image {image_id[:12]}: {e}")
        else:
            logger.info(f"No images found matching '{name_filter}'")
    except Exception as e:
        logger.error(f"Error listing images: {e}")


async def _remove_networks(name_filter):
    """
    Remove networks matching the name filter.
    """
    try:
        logger.info(f"Removing networks matching '{name_filter}'...")
        result = subprocess.run(
            ["docker", "network", "ls", "--format", "{{.Name}}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            network_names = [
                name.strip()
                for name in result.stdout.strip().split("\n")
                if name.strip()
            ]

            for network_name in network_names:
                if name_filter in network_name and network_name not in [
                    "bridge",
                    "host",
                    "none",
                ]:
                    try:
                        logger.info(f"Removing network '{network_name}'...")
                        remove_result = subprocess.run(
                            ["docker", "network", "rm", network_name],
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                        if remove_result.returncode == 0:
                            logger.info(f"Removed network '{network_name}'")
                        else:
                            logger.warning(
                                f"Error removing network '{network_name}': {remove_result.stderr}"
                            )
                    except Exception as e:
                        logger.error(f"Failed to remove network '{network_name}': {e}")
        else:
            logger.warning(f"Error listing networks: {result.stderr}")
    except Exception as e:
        logger.error(f"Error during network cleanup: {e}")


async def _remove_specific_image(image_id):
    """
    Remove a specific image by ID.
    """
    try:
        logger.info(f"Removing specific image {image_id[:12]}...")
        result = subprocess.run(
            ["docker", "rmi", image_id, "-f"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            logger.info(f"Removed specific image {image_id[:12]}")
        else:
            logger.warning(
                f"Error removing specific image {image_id[:12]}: {result.stderr}"
            )
    except Exception as e:
        logger.error(f"Failed to remove specific image {image_id[:12]}: {e}")


async def _remove_specific_network(network_name):
    """
    Remove a specific network by name.
    """
    try:
        logger.info(f"Removing specific network '{network_name}'...")
        result = subprocess.run(
            ["docker", "network", "rm", network_name],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            logger.info(f"Removed specific network '{network_name}'")
        else:
            logger.warning(
                f"Error removing specific network '{network_name}': {result.stderr}"
            )
    except Exception as e:
        logger.error(f"Failed to remove specific network '{network_name}': {e}")


async def _cleanup_volumes():
    """
    Clean up orphaned volumes.
    """
    try:
        logger.info("Cleaning up volumes...")
        result = subprocess.run(
            ["docker", "volume", "prune", "-f"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout:
            logger.info(f"Volume cleanup: {result.stdout.strip()}")
        else:
            logger.info("No volumes to clean up")
    except Exception as e:
        logger.warning(f"Error cleaning volumes: {e}")


async def main():
    """
    Main entry point.
    """
    logger.info("=" * 60)
    logger.info("🔄 AUTONOMOUS AI-PROXY CLEANUP")
    logger.info("=" * 60)

    await stop_and_clean_containers()

    logger.info("=" * 60)
    logger.info("✅ Cleanup completed successfully!")
    logger.info("📋 Check 'docker ps' and 'docker images' to verify cleanup")


if __name__ == "__main__":
    asyncio.run(main())
