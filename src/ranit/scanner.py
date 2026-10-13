"""Read-only heuristic security scan. It never executes project code."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

MAX_FILES = 3000
MAX_BYTES = 1_000_000
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".next", "dist", "build", ".terraform", ".pytest_cache"}
TEXT_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rb", ".php", ".yml", ".yaml", ".json", ".toml", ".ini", ".cfg", ".env", ".sh", ".ps1", ".tf", ".properties", ".txt"}
SECRET_PATTERNS = [
    ("Possible AWS access key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("Possible private key material", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("Possible hard-coded credential", re.compile(r"""(?i)(?:password|passwd|api[_-]?key|secret|access[_-]?token)\s*[:=]\s*['"][^'"]{8,}['"]""")),
]
RISK_PATTERNS = [
    ("Potential dynamic code execution", re.compile(r"\b(?:eval|exec)\s*\(")),
    ("TLS verification may be disabled", re.compile(r"(?i)(?:verify\s*=\s*False|rejectUnauthorized\s*:\s*false)")),
    ("Shell execution may be enabled", re.compile(r"(?i)shell\s*=\s*True")),
]
DEPENDENCY_FILES = {"requirements.txt", "pyproject.toml", "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Pipfile.lock", "pom.xml", "build.gradle", "go.mod", "Cargo.lock", "Gemfile.lock"}
DEPLOYMENT_FILES = {"Dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml", "Jenkinsfile", ".gitlab-ci.yml", "azure-pipelines.yml", "Chart.yaml", "main.tf"}


def scan_project(path: Path) -> dict[str, Any]:
    """Report simple risk indicators without printing matched source lines or secrets."""
    root = path.expanduser().resolve()
    if not root.is_dir():
        return {"project_path": str(root), "exists": False, "files_scanned": 0, "findings": [], "dependency_files": [], "deployment_files": []}

    findings: list[dict[str, str]] = []
    dependency_files: set[str] = set()
    deployment_files: set[str] = set()
    scanned = 0

    for current, dirs, filenames in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
        for name in filenames:
            file_path = Path(current) / name
            rel = file_path.relative_to(root).as_posix()
            if name in DEPENDENCY_FILES:
                dependency_files.add(rel)
            if name in DEPLOYMENT_FILES or name.lower() == "dockerfile":
                deployment_files.add(rel)
            if (name == ".env" or name.startswith(".env.")) and name not in {".env.example", ".env.sample"}:
                findings.append({"severity": "HIGH", "file": rel, "rule": "Environment file may contain secrets", "line": "—"})
            if file_path.suffix.lower() not in TEXT_SUFFIXES and name not in {"Dockerfile", "Jenkinsfile"}:
                continue
            try:
                if file_path.stat().st_size > MAX_BYTES:
                    continue
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            scanned += 1
            for line_no, line in enumerate(content.splitlines(), start=1):
                for label, pattern in SECRET_PATTERNS:
                    if pattern.search(line):
                        findings.append({"severity": "HIGH", "file": rel, "rule": label, "line": str(line_no)})
                        break
                for label, pattern in RISK_PATTERNS:
                    if pattern.search(line):
                        findings.append({"severity": "MEDIUM", "file": rel, "rule": label, "line": str(line_no)})
                if len(findings) >= 500:
                    break
            if scanned >= MAX_FILES or len(findings) >= 500:
                break
        if scanned >= MAX_FILES or len(findings) >= 500:
            break

    return {
        "project_path": str(root),
        "exists": True,
        "files_scanned": scanned,
        "findings": findings,
        "dependency_files": sorted(dependency_files),
        "deployment_files": sorted(deployment_files),
        "note": "Heuristic scan only; false positives and missed issues are possible. No project code was executed and no files were changed.",
    }
