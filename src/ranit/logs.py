"""Read-only structured log analysis; never return raw log lines."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

MAX_LOG_BYTES = 2_000_000
MAX_MATCHES = 200

SEVERITY_PATTERNS = {
    "CRITICAL": re.compile(r"\b(?:CRITICAL|FATAL)\b", re.IGNORECASE),
    "ERROR": re.compile(r"\bERROR\b|\bERR\b", re.IGNORECASE),
    "WARNING": re.compile(r"\bWARNING\b|\bWARN\b", re.IGNORECASE),
    "INFO": re.compile(r"\bINFO\b", re.IGNORECASE),
    "DEBUG": re.compile(r"\bDEBUG\b", re.IGNORECASE),
}

ERROR_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Python exception", re.compile(r"Traceback \(most recent call last\)|\b(?:ModuleNotFoundError|ImportError|SyntaxError|TypeError|ValueError|KeyError|AttributeError)\b", re.IGNORECASE)),
    ("Docker/Kubernetes issue", re.compile(r"ImagePullBackOff|ErrImagePull|CrashLoopBackOff|OOMKilled|failed to solve|dockerfile parse error", re.IGNORECASE)),
    ("Network/timeout issue", re.compile(r"connection timed out|connection refused|temporary failure in name resolution|\btimeout\b", re.IGNORECASE)),
    ("Permission issue", re.compile(r"permission denied|access is denied|\bAccessDenied\b|UnauthorizedOperation", re.IGNORECASE)),
)


def analyze_log(path: Path) -> dict[str, Any]:
    """Count log severity and summarize known patterns without exposing raw lines."""
    log_path = path.expanduser().resolve()
    if not log_path.is_file():
        return {
            "log_path": str(log_path),
            "exists": False,
            "bytes_read": 0,
            "total_lines": 0,
            "severity_counts": {key: 0 for key in SEVERITY_PATTERNS},
            "matches": [],
            "note": "Log file not found; no file was changed.",
        }

    size = log_path.stat().st_size
    if size > MAX_LOG_BYTES:
        raise ValueError(f"Log file is larger than the {MAX_LOG_BYTES}-byte safety limit.")

    content = log_path.read_text(encoding="utf-8", errors="replace")
    counts = {key: 0 for key in SEVERITY_PATTERNS}
    matches: list[dict[str, Any]] = []
    lines = content.splitlines()

    for line_number, line in enumerate(lines, start=1):
        found_severity = False
        for severity, pattern in SEVERITY_PATTERNS.items():
            if pattern.search(line):
                counts[severity] += 1
                found_severity = True
        if not found_severity and any(pattern.search(line) for _, pattern in ERROR_PATTERNS):
            counts["ERROR"] += 1

        for category, pattern in ERROR_PATTERNS:
            if pattern.search(line) and len(matches) < MAX_MATCHES:
                matches.append({
                    "line": line_number,
                    "severity": "ERROR",
                    "category": category,
                })

    return {
        "log_path": str(log_path),
        "exists": True,
        "bytes_read": size,
        "total_lines": len(lines),
        "severity_counts": counts,
        "matches": matches,
        "note": "Local heuristic log analysis only. Raw log lines are not returned. Patterns can miss issues or produce false positives; no code was executed and no files were changed.",
    }
