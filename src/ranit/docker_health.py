
"""Read-only Docker container health checks."""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any


def check_docker_health() -> dict[str, Any]:
    """Read container status without starting, stopping, or restarting containers."""
    docker_path = shutil.which("docker")

    if not docker_path:
        return {
            "available": False,
            "containers": [],
            "error": "Docker CLI was not found. Install Docker Desktop and try again.",
            "note": "Read-only check; no containers were changed.",
        }

    try:
        result = subprocess.run(
            [docker_path, "ps", "-a", "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "available": True,
            "containers": [],
            "error": "Docker command timed out after 10 seconds.",
            "note": "Read-only check; no containers were changed.",
        }
    except OSError:
        return {
            "available": True,
            "containers": [],
            "error": "Could not execute the Docker CLI.",
            "note": "Read-only check; no containers were changed.",
        }

    if result.returncode != 0:
        return {
            "available": True,
            "containers": [],
            "error": "Docker could not list containers. Check Docker Desktop or daemon status.",
            "note": "Read-only check; no containers were changed.",
        }

    containers: list[dict[str, str]] = []

    for line in result.stdout.splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue

        state = str(item.get("State", "unknown"))
        status = str(item.get("Status", "unknown"))
        lowered_status = status.lower()

        if "unhealthy" in lowered_status:
            health = "unhealthy"
        elif "healthy" in lowered_status:
            health = "healthy"
        elif "health: starting" in lowered_status:
            health = "starting"
        elif state.lower() == "running":
            health = "no healthcheck configured"
        else:
            health = "unknown"

        containers.append(
            {
                "id": str(item.get("ID", "")),
                "name": str(item.get("Names", "")),
                "image": str(item.get("Image", "")),
                "state": state,
                "status": status,
                "health": health,
            }
        )

    return {
        "available": True,
        "containers": containers,
        "error": None,
        "note": "Read-only check; no containers were started, stopped, or restarted.",
    }
