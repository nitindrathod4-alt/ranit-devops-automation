"""Read-only project inspection. Does not execute project files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

MAX_FILES_TO_SCAN = 5000
SKIP_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".next",
    "dist", "build", ".terraform", ".pytest_cache",
}
MARKER_LABELS = {
    "Dockerfile": "Dockerfile",
    "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
    "compose.yml": "Docker Compose",
    "compose.yaml": "Docker Compose",
    "package.json": "Node.js / JavaScript",
    "pyproject.toml": "Python (pyproject.toml)",
    "requirements.txt": "Python (requirements.txt)",
    "Pipfile": "Python (Pipenv)",
    "pom.xml": "Java / Maven",
    "build.gradle": "Java/JVM / Gradle",
    "build.gradle.kts": "Kotlin/JVM / Gradle",
    "go.mod": "Go",
    "Cargo.toml": "Rust",
    "Gemfile": "Ruby",
    "composer.json": "PHP / Composer",
    "Jenkinsfile": "Jenkins pipeline",
    ".gitlab-ci.yml": "GitLab CI",
    "azure-pipelines.yml": "Azure Pipelines",
    "Chart.yaml": "Helm chart",
}


def inspect_project(path: Path) -> dict[str, Any]:
    """Inspect a local directory without executing any project content."""
    project_path = path.expanduser().resolve()
    exists = project_path.exists() and project_path.is_dir()
    if not exists:
        return {
            "project_path": str(project_path),
            "exists": False,
            "files_scanned": 0,
            "markers": [],
            "top_level_entries": [],
        }

    try:
        top_level = sorted(entry.name for entry in project_path.iterdir())
    except OSError as exc:
        raise OSError(f"Cannot read project directory: {exc}") from exc

    markers: set[str] = set()
    scanned = 0
    try:
        for _, dirs, filenames in os.walk(project_path):
            dirs[:] = sorted(
                name for name in dirs
                if name not in SKIP_DIRS and not name.startswith(".")
            )
            for filename in filenames:
                scanned += 1
                if filename in MARKER_LABELS:
                    markers.add(MARKER_LABELS[filename])
                if scanned >= MAX_FILES_TO_SCAN:
                    break
            if scanned >= MAX_FILES_TO_SCAN:
                break
    except OSError as exc:
        raise OSError(f"Cannot scan project directory: {exc}") from exc

    return {
        "project_path": str(project_path),
        "exists": True,
        "files_scanned": scanned,
        "markers": sorted(markers),
        "top_level_entries": top_level[:100],
    }
