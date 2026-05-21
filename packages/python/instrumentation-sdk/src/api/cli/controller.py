import argparse
import os
import shutil
import socket
import subprocess
import sys
from typing import List, Protocol


class DockerClient(Protocol):
    def is_installed(self) -> bool:
        ...

    def is_daemon_running(self) -> bool:
        ...

    def container_exists(self, name: str) -> bool:
        ...

    def is_container_running(self, name: str) -> bool:
        ...

    def start_container(self, name: str) -> bool:
        ...

    def run_container(self, name: str, image: str, tag: str, ports: List[str]) -> bool:
        ...

    def stop_container(self, name: str) -> bool:
        ...

    def remove_container(self, name: str) -> bool:
        ...


class PortChecker(Protocol):
    def is_port_in_use(self, port: int) -> bool:
        ...


def run_system_command(args: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True)


def check_host_port(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


class RealDockerClient:
    def is_installed(self) -> bool:
        return shutil.which("docker") is not None

    def is_daemon_running(self) -> bool:
        result = run_system_command(["docker", "info"])
        return result.returncode == 0

    def container_exists(self, name: str) -> bool:
        result = run_system_command(["docker", "ps", "-a", "--filter", f"name=^{name}$", "--format", "{{.Names}}"])
        return name in result.stdout.splitlines()

    def is_container_running(self, name: str) -> bool:
        result = run_system_command(["docker", "ps", "--filter", f"name=^{name}$", "--format", "{{.Names}}"])
        return name in result.stdout.splitlines()

    def start_container(self, name: str) -> bool:
        result = run_system_command(["docker", "start", name])
        return result.returncode == 0

    def run_container(self, name: str, image: str, tag: str, ports: List[str]) -> bool:
        cmd = ["docker", "run", "-d", "--name", name]
        for p in ports:
            cmd.extend(["-p", p])
        cmd.append(f"{image}:{tag}")
        result = run_system_command(cmd)
        return result.returncode == 0

    def stop_container(self, name: str) -> bool:
        result = run_system_command(["docker", "stop", name])
        return result.returncode == 0

    def remove_container(self, name: str) -> bool:
        result = run_system_command(["docker", "rm", name])
        return result.returncode == 0


class RealPortChecker:
    def is_port_in_use(self, port: int) -> bool:
        return check_host_port(port)


class ObservabilityController:
    def __init__(self, docker_client: DockerClient, port_checker: PortChecker):
        self.docker = docker_client
        self.port_checker = port_checker

    def start(self, name: str, image: str, tag: str, api_port: int, grafana_port: int, otlp_port: int, prometheus_port: int) -> int:
        if not self.docker.is_installed():
            print("Error: Docker is not installed or not in PATH.", file=sys.stderr)
            return 1

        if not self.docker.is_daemon_running():
            print("Error: Docker daemon is not running.", file=sys.stderr)
            return 1

        if self.docker.is_container_running(name):
            print(f"Observability stack '{name}' is already running.")
            print(f"Grafana: http://localhost:{grafana_port}")
            return 0

        if self.docker.container_exists(name):
            print(f"Starting existing stopped container '{name}'...")
            if self.docker.start_container(name):
                print(f"Successfully started '{name}'.")
                print(f"Grafana: http://localhost:{grafana_port}")
                return 0
            print(f"Error: Failed to start container '{name}'.", file=sys.stderr)
            return 1

        ports_to_check = {
            "API": api_port,
            "Grafana": grafana_port,
            "OTLP": otlp_port,
            "Prometheus": prometheus_port,
        }

        for service, port in ports_to_check.items():
            if self.port_checker.is_port_in_use(port):
                print(f"Error: Port {port} for {service} is already in use on the host.", file=sys.stderr)
                return 1

        port_mappings = [
            f"{api_port}:8000",
            f"{grafana_port}:3000",
            f"{otlp_port}:4317",
            f"{prometheus_port}:9090",
        ]

        print(f"Launching observability stack '{name}' using {image}:{tag}...")
        if self.docker.run_container(name, image, tag, port_mappings):
            print("Observability stack launched successfully!")
            print(f"Grafana UI: http://localhost:{grafana_port}")
            print(f"FastAPI API: http://localhost:{api_port}")
            print(f"OTLP Endpoint: http://localhost:{otlp_port}")
            print(f"Prometheus UI: http://localhost:{prometheus_port}")
            return 0

        print("Error: Failed to run container.", file=sys.stderr)
        return 1

    def stop(self, name: str) -> int:
        if not self.docker.is_installed():
            print("Error: Docker is not installed or not in PATH.", file=sys.stderr)
            return 1

        if not self.docker.is_daemon_running():
            print("Error: Docker daemon is not running.", file=sys.stderr)
            return 1

        if not self.docker.container_exists(name):
            print(f"Observability stack '{name}' does not exist.")
            return 0

        print(f"Stopping observability stack '{name}'...")
        self.docker.stop_container(name)
        print(f"Removing container '{name}'...")
        self.docker.remove_container(name)
        print("Observability stack stopped and removed successfully.")
        return 0

    def status(self, name: str) -> int:
        if not self.docker.is_installed():
            print("Docker: Not installed", file=sys.stderr)
            return 1

        if not self.docker.is_daemon_running():
            print("Docker: Daemon not running", file=sys.stderr)
            return 1

        if self.docker.is_container_running(name):
            print(f"Observability stack '{name}': Running")
            return 0
        elif self.docker.container_exists(name):
            print(f"Observability stack '{name}': Stopped")
            return 0
        else:
            print(f"Observability stack '{name}': Not created")
            return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage the LLM Observability Stack")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start", help="Start the observability stack")
    start_parser.add_argument("--name", default="instrumentation-api-allinone", help="Container name")
    start_parser.add_argument("--image", default="chiefj/instrumentation-sdk-api", help="Docker image name")
    start_parser.add_argument("--tag", default="latest", help="Docker image tag")
    start_parser.add_argument("--api-port", type=int, default=8002, help="Host port for the API (default: 8002)")
    start_parser.add_argument("--grafana-port", type=int, default=3002, help="Host port for Grafana UI (default: 3002)")
    start_parser.add_argument("--otlp-port", type=int, default=4317, help="Host port for OTLP gRPC endpoint (default: 4317)")
    start_parser.add_argument("--prometheus-port", type=int, default=9090, help="Host port for Prometheus UI (default: 9090)")

    stop_parser = subparsers.add_parser("stop", help="Stop and remove the observability stack")
    stop_parser.add_argument("--name", default="instrumentation-api-allinone", help="Container name")

    status_parser = subparsers.add_parser("status", help="Get status of the observability stack")
    status_parser.add_argument("--name", default="instrumentation-api-allinone", help="Container name")

    args = parser.parse_args()

    controller = ObservabilityController(RealDockerClient(), RealPortChecker())

    if args.command == "start":
        sys.exit(
            controller.start(
                args.name,
                args.image,
                args.tag,
                args.api_port,
                args.grafana_port,
                args.otlp_port,
                args.prometheus_port,
            )
        )
    elif args.command == "stop":
        sys.exit(controller.stop(args.name))
    elif args.command == "status":
        sys.exit(controller.status(args.name))


if __name__ == "__main__":
    main()
