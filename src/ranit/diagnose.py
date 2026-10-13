"""Read-only log diagnosis using local pattern matching; no AI or code execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MAX_LOG_BYTES = 2_000_000

RULES: tuple[tuple[str, tuple[str, ...], str, str], ...] = (
    ("Python import/module error", ("modulenotfounderror", "no module named", "importerror"), "A Python dependency may be missing or the active environment may be wrong.", "Check the active virtual environment and install the dependency listed by the project."),
    ("Python exception", ("traceback (most recent call last)", "syntaxerror:", "typeerror:", "valueerror:", "keyerror:", "attributeerror:"), "Python raised an exception; the traceback usually points to the failing file and line.", "Read the final lines of the traceback first, then inspect the first project-code frame and the input values."),
    ("Docker image/build error", ("failed to solve:", "dockerfile parse error", "imagepullbackoff", "errimagepull"), "A container image build or image pull may have failed.", "Check the Dockerfile/build context, image name and tag, registry access, and the preceding error message."),
    ("Kubernetes pod/config error", ("crashloopbackoff", "createcontainerconfigerror", "oomkilled", "pending"), "A Kubernetes workload may be failing to start or being terminated.", "Check pod events and logs, resource limits, configuration, and referenced Secrets/ConfigMaps."),
    ("AWS access error", ("accessdenied", "unauthorizedoperation", "invalidclienttokenid", "expiredtoken"), "AWS credentials or IAM permissions may be invalid or insufficient.", "Verify the selected AWS profile/role and region, token validity, and least-privilege IAM permissions. Do not paste credentials into logs or chat."),
    ("Network/timeout error", ("connection timed out", "timeout", "connection refused", "temporary failure in name resolution", "name or service not known"), "A network path, service endpoint, DNS lookup, or service listener may be unavailable.", "Check the endpoint and port, DNS resolution, network/security rules, and whether the destination service is healthy."),
    ("Disk or memory pressure", ("no space left on device", "out of memory", "oom-kill", "oomkilled"), "The host or workload may have exhausted disk or memory.", "Check disk and memory usage, container limits, and recent resource changes before increasing limits."),
    ("Permission error", ("permission denied", "access is denied"), "The process may not have access to a file, directory, socket, or resource.", "Check the file/resource owner and required permissions; avoid running the tool as Administrator/root as a workaround."),
)


def diagnose_log(path: Path) -> dict[str, Any]:
    """Analyze a bounded local text log without executing it or returning its contents."""
    log_path = path.expanduser().resolve()
    if not log_path.is_file():
        return {
            "log_path": str(log_path),
            "exists": False,
            "bytes_read": 0,
            "diagnoses": [],
            "note": "Log file not found; no file was changed.",
        }
    size = log_path.stat().st_size
    if size > MAX_LOG_BYTES:
        raise ValueError(f"Log file is larger than the {MAX_LOG_BYTES}-byte safety limit.")
    content = log_path.read_text(encoding="utf-8", errors="replace")
    lowered = content.lower()
    diagnoses = []
    for title, needles, cause, remedy in RULES:
        if any(needle in lowered for needle in needles):
            diagnoses.append({
                "category": title,
                "possible_cause": cause,
                "suggested_checks": remedy,
            })
    return {
        "log_path": str(log_path),
        "exists": True,
        "bytes_read": size,
        "diagnoses": diagnoses,
        "note": "Local pattern-based suggestions only; not an AI diagnosis. No log contents are printed, no code is executed, and no files are changed.",
    }
