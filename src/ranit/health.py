"""Read-only project health checks; never execute project code."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from ranit.inspector import inspect_project


TOOL_CHECKS = {
    "Python": ("python", "Python runtime"),
    "Python (pyproject.toml)": ("python", "Python runtime"),
    "Python (requirements.txt)": ("python", "Python runtime"),
    "Node.js / JavaScript": ("node", "Node.js runtime"),
    "Java / Maven": ("java", "Java runtime"),
    "Java/JVM / Gradle": ("java", "Java runtime"),
    "Kotlin/JVM / Gradle": ("java", "Java runtime"),
    "Go": ("go", "Go runtime"),
    "Rust": ("cargo", "Rust toolchain"),
    "Ruby": ("ruby", "Ruby runtime"),
    "PHP / Composer": ("php", "PHP runtime"),
    "Dockerfile": ("docker", "Docker CLI"),
    "Docker Compose": ("docker", "Docker CLI"),
    "Jenkins pipeline": ("git", "Git"),
    "GitLab CI": ("git", "Git"),
    "Azure Pipelines": ("git", "Git"),
}


def check_project_health(path: Path) -> dict[str, Any]:
    """Summarize project markers and relevant local tools without running them."""
    report = inspect_project(path)
    if not report["exists"]:
        return {
            **report,
            "status": "ERROR",
            "checks": [],
            "issues": ["Project directory does not exist or is not a directory."],
            "note": "Read-only checks only. No project code was executed and no files were changed.",
        }

    checks: list[dict[str, str]] = []
    issues: list[str] = []
    markers = report["markers"]

    if not markers:
        issues.append("No recognized project/build markers were found.")
    for marker in markers:
        tool = TOOL_CHECKS.get(marker)
        if not tool:
            continue
        command, label = tool
        resolved = shutil.which(command)
        checks.append({
            "marker": marker,
            "tool": label,
            "command": command,
            "status": "available" if resolved else "missing",
            "path": resolved or "",
        })
        if not resolved:
            issues.append(f"{label} was not found on PATH (needed for detected {marker} project marker).")

    status = "ERROR" if not markers else ("WARNING" if issues else "OK")
    return {
        "project_path": report["project_path"],
        "exists": True,
        "status": status,
        "files_scanned": report["files_scanned"],
        "markers": markers,
        "checks": checks,
        "issues": issues,
        "note": "Local heuristic health check only. Tool presence does not prove a build works. No project code was executed and no files were changed.",
    }
