
"""Read-only smart log diagnosis using local pattern matching."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MAX_LOG_BYTES = 2_000_000

RULES: tuple[tuple[str, tuple[str, ...], str, str, str], ...] = (
    (
        "Disk or memory pressure",
        ("no space left on device", "out of memory", "oom-kill", "oomkilled"),
        "Critical",
        "The host or workload may have exhausted disk space or memory.",
        "Check disk usage, memory usage, container limits, and recent resource changes.",
    ),
    (
        "Python import/module error",
        ("modulenotfounderror", "no module named", "importerror"),
        "High",
        "A Python dependency may be missing or the active environment may be wrong.",
        "Activate the correct virtual environment and install the required project dependency.",
    ),
    (
        "Python exception",
        (
            "traceback (most recent call last)",
            "syntaxerror:",
            "typeerror:",
            "valueerror:",
            "keyerror:",
            "attributeerror:",
        ),
        "High",
        "Python raised an exception.",
        "Read the final traceback lines and inspect the first project-code frame.",
    ),
    (
        "Docker daemon unavailable",
        (
            "cannot connect to the docker daemon",
            "is the docker daemon running",
            "error during connect",
        ),
        "High",
        "The Docker CLI cannot communicate with the Docker daemon.",
        "Start Docker Desktop or the Docker service, then verify with docker info.",
    ),
    (
        "Docker port conflict",
        (
            "port is already allocated",
            "address already in use",
            "bind: only one usage of each socket address",
        ),
        "Medium",
        "Another process or container may already be using the requested port.",
        "Inspect port usage and choose an unused host port if appropriate.",
    ),
    (
        "Docker image/build error",
        ("failed to solve:", "dockerfile parse error", "imagepullbackoff", "errimagepull"),
        "High",
        "A container image build or image pull may have failed.",
        "Check the Dockerfile, build context, image name, tag, registry access, and preceding error.",
    ),
    (
        "Kubernetes pod/config error",
        ("crashloopbackoff", "createcontainerconfigerror", "oomkilled", "pending"),
        "High",
        "A Kubernetes workload may be failing to start or being terminated.",
        "Inspect pod events and logs, resource limits, configuration, Secrets, and ConfigMaps.",
    ),
    (
        "AWS access error",
        ("accessdenied", "unauthorizedoperation", "invalidclienttokenid", "expiredtoken"),
        "High",
        "AWS credentials or IAM permissions may be invalid or insufficient.",
        "Verify the AWS profile, role, region, token validity, and least-privilege IAM permissions.",
    ),
    (
        "Network/timeout error",
        (
            "connection timed out",
            "timeout",
            "connection refused",
            "temporary failure in name resolution",
            "name or service not known",
        ),
        "Medium",
        "A network path, endpoint, DNS lookup, or service listener may be unavailable.",
        "Check the endpoint, port, DNS resolution, network rules, and destination service health.",
    ),
    (
        "Permission error",
        ("permission denied", "access is denied"),
        "High",
        "The process may lack access to a file, directory, socket, or resource.",
        "Check ownership and required permissions; avoid using Administrator/root as a workaround.",
    ),
)


def diagnose_log(path: Path) -> dict[str, Any]:
    """Analyze a bounded local text log without returning its contents."""
    log_path = path.expanduser().resolve()

    if not log_path.is_file():
        return {
            "log_path": str(log_path),
            "exists": False,
            "bytes_read": 0,
            "diagnoses": [],
            "summary": {
                "errors_detected": 0,
                "highest_severity": "None",
            },
            "note": "Log file not found; no file was changed.",
        }

    size = log_path.stat().st_size
    if size > MAX_LOG_BYTES:
        raise ValueError(
            f"Log file is larger than the {MAX_LOG_BYTES}-byte safety limit."
        )

    content = log_path.read_text(encoding="utf-8", errors="replace").lower()
    diagnoses = []

    for category, needles, severity, cause, remedy in RULES:
        if any(needle in content for needle in needles):
            diagnoses.append(
                {
                    "category": category,
                    "severity": severity,
                    "possible_cause": cause,
                    "suggested_checks": remedy,
                }
            )

    severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    diagnoses.sort(
        key=lambda item: severity_order.get(item["severity"], 4)
    )

    return {
        "log_path": str(log_path),
        "exists": True,
        "bytes_read": size,
        "diagnoses": diagnoses,
        "summary": {
            "errors_detected": len(diagnoses),
            "highest_severity": (
                diagnoses[0]["severity"] if diagnoses else "None"
            ),
        },
        "note": (
            "Local rule-based suggestions only; this is not an AI diagnosis. "
            "Log contents are not returned, no code is executed, and no files are changed."
        ),
    }
