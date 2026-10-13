
from pathlib import Path

import pytest

from ranit.docker_health import check_docker_health


def test_docker_cli_missing(monkeypatch) -> None:
    monkeypatch.setattr("ranit.docker_health.shutil.which", lambda _: None)

    result = check_docker_health()

    assert result["available"] is False
    assert result["containers"] == []
    assert "Docker CLI was not found" in result["error"]


def test_docker_lists_healthy_container(monkeypatch) -> None:
    class FakeResult:
        returncode = 0
        stdout = (
            '{"ID":"abc123","Names":"web","Image":"nginx:latest",'
            '"State":"running","Status":"Up 2 minutes (healthy)"}\n'
        )
        stderr = ""

    monkeypatch.setattr("ranit.docker_health.shutil.which", lambda _: "docker")
    monkeypatch.setattr(
        "ranit.docker_health.subprocess.run",
        lambda *args, **kwargs: FakeResult(),
    )

    result = check_docker_health()

    assert result["available"] is True
    assert len(result["containers"]) == 1
    assert result["containers"][0]["name"] == "web"
    assert result["containers"][0]["health"] == "healthy"


def test_docker_unhealthy_container(monkeypatch) -> None:
    class FakeResult:
        returncode = 0
        stdout = (
            '{"ID":"def456","Names":"api","Image":"api:latest",'
            '"State":"running","Status":"Up 1 minute (unhealthy)"}\n'
        )
        stderr = ""

    monkeypatch.setattr("ranit.docker_health.shutil.which", lambda _: "docker")
    monkeypatch.setattr(
        "ranit.docker_health.subprocess.run",
        lambda *args, **kwargs: FakeResult(),
    )

    result = check_docker_health()

    assert result["containers"][0]["health"] == "unhealthy"


def test_docker_command_failure(monkeypatch) -> None:
    class FakeResult:
        returncode = 1
        stdout = ""
        stderr = "Docker daemon unavailable"

    monkeypatch.setattr("ranit.docker_health.shutil.which", lambda _: "docker")
    monkeypatch.setattr(
        "ranit.docker_health.subprocess.run",
        lambda *args, **kwargs: FakeResult(),
    )

    result = check_docker_health()

    assert result["available"] is True
    assert result["containers"] == []
    assert result["error"] is not None


def test_docker_command_timeout(monkeypatch) -> None:
    def timeout(*args, **kwargs):
        raise __import__("subprocess").TimeoutExpired("docker", 10)

    monkeypatch.setattr("ranit.docker_health.shutil.which", lambda _: "docker")
    monkeypatch.setattr("ranit.docker_health.subprocess.run", timeout)

    result = check_docker_health()

    assert result["error"] == "Docker command timed out after 10 seconds."
    assert result["containers"] == []
