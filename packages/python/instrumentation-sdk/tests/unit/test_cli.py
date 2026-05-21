import pytest
from api.cli.controller import ObservabilityController


class FakeDockerClient:
    def __init__(self) -> None:
        self.installed = True
        self.daemon_running = True
        self.running_containers = set()
        self.existing_containers = set()
        self.started_containers = set()
        self.stopped_containers = set()
        self.removed_containers = set()
        self.run_calls = []

    def is_installed(self) -> bool:
        return self.installed

    def is_daemon_running(self) -> bool:
        return self.daemon_running

    def container_exists(self, name: str) -> bool:
        return name in self.existing_containers

    def is_container_running(self, name: str) -> bool:
        return name in self.running_containers

    def start_container(self, name: str) -> bool:
        self.started_containers.add(name)
        return True

    def run_container(self, name: str, image: str, tag: str, ports: list[str]) -> bool:
        self.run_calls.append((name, image, tag, ports))
        return True

    def stop_container(self, name: str) -> bool:
        self.stopped_containers.add(name)
        return True

    def remove_container(self, name: str) -> bool:
        self.removed_containers.add(name)
        return True


class FakePortChecker:
    def __init__(self) -> None:
        self.in_use_ports = set()

    def is_port_in_use(self, port: int) -> bool:
        return port in self.in_use_ports


def test_start_docker_not_installed(capsys) -> None:
    docker = FakeDockerClient()
    docker.installed = False
    checker = FakePortChecker()
    controller = ObservabilityController(docker, checker)

    code = controller.start("test-stack", "image", "latest", 8000, 3000, 4317, 9090)
    assert code == 1
    captured = capsys.readouterr()
    assert "Docker is not installed" in captured.err


def test_start_docker_daemon_not_running(capsys) -> None:
    docker = FakeDockerClient()
    docker.daemon_running = False
    checker = FakePortChecker()
    controller = ObservabilityController(docker, checker)

    code = controller.start("test-stack", "image", "latest", 8000, 3000, 4317, 9090)
    assert code == 1
    captured = capsys.readouterr()
    assert "Docker daemon is not running" in captured.err


def test_start_already_running(capsys) -> None:
    docker = FakeDockerClient()
    docker.running_containers.add("test-stack")
    checker = FakePortChecker()
    controller = ObservabilityController(docker, checker)

    code = controller.start("test-stack", "image", "latest", 8000, 3000, 4317, 9090)
    assert code == 0
    captured = capsys.readouterr()
    assert "already running" in captured.out


def test_start_existing_stopped(capsys) -> None:
    docker = FakeDockerClient()
    docker.existing_containers.add("test-stack")
    checker = FakePortChecker()
    controller = ObservabilityController(docker, checker)

    code = controller.start("test-stack", "image", "latest", 8000, 3000, 4317, 9090)
    assert code == 0
    assert "test-stack" in docker.started_containers
    captured = capsys.readouterr()
    assert "Starting existing stopped container" in captured.out


def test_start_port_conflict(capsys) -> None:
    docker = FakeDockerClient()
    checker = FakePortChecker()
    checker.in_use_ports.add(3000)
    controller = ObservabilityController(docker, checker)

    code = controller.start("test-stack", "image", "latest", 8000, 3000, 4317, 9090)
    assert code == 1
    captured = capsys.readouterr()
    assert "Port 3000 for Grafana is already in use" in captured.err


def test_start_success(capsys) -> None:
    docker = FakeDockerClient()
    checker = FakePortChecker()
    controller = ObservabilityController(docker, checker)

    code = controller.start("test-stack", "image", "latest", 8000, 3000, 4317, 9090)
    assert code == 0
    assert len(docker.run_calls) == 1
    name, image, tag, ports = docker.run_calls[0]
    assert name == "test-stack"
    assert image == "image"
    assert tag == "latest"
    assert "8000:8000" in ports
    assert "3000:3000" in ports
    assert "4317:4317" in ports
    assert "9090:9090" in ports
    captured = capsys.readouterr()
    assert "launched successfully" in captured.out


def test_stop_not_existing(capsys) -> None:
    docker = FakeDockerClient()
    checker = FakePortChecker()
    controller = ObservabilityController(docker, checker)

    code = controller.stop("test-stack")
    assert code == 0
    captured = capsys.readouterr()
    assert "does not exist" in captured.out


def test_stop_success(capsys) -> None:
    docker = FakeDockerClient()
    docker.existing_containers.add("test-stack")
    checker = FakePortChecker()
    controller = ObservabilityController(docker, checker)

    code = controller.stop("test-stack")
    assert code == 0
    assert "test-stack" in docker.stopped_containers
    assert "test-stack" in docker.removed_containers
    captured = capsys.readouterr()
    assert "stopped and removed successfully" in captured.out


def test_status_not_created(capsys) -> None:
    docker = FakeDockerClient()
    checker = FakePortChecker()
    controller = ObservabilityController(docker, checker)

    code = controller.status("test-stack")
    assert code == 0
    captured = capsys.readouterr()
    assert "Not created" in captured.out


def test_status_stopped(capsys) -> None:
    docker = FakeDockerClient()
    docker.existing_containers.add("test-stack")
    checker = FakePortChecker()
    controller = ObservabilityController(docker, checker)

    code = controller.status("test-stack")
    assert code == 0
    captured = capsys.readouterr()
    assert "Stopped" in captured.out


def test_status_running(capsys) -> None:
    docker = FakeDockerClient()
    docker.running_containers.add("test-stack")
    checker = FakePortChecker()
    controller = ObservabilityController(docker, checker)

    code = controller.status("test-stack")
    assert code == 0
    captured = capsys.readouterr()
    assert "Running" in captured.out
