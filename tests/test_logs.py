from pathlib import Path

import pytest

from ranit.logs import analyze_log


def test_analyze_log_counts_severity_and_reports_line_numbers_without_raw_text(tmp_path: Path) -> None:
    log = tmp_path / "app.log"
    log.write_text(
        "INFO service started\nERROR ModuleNotFoundError: private_module_name\nWARNING retrying\n",
        encoding="utf-8",
    )

    result = analyze_log(log)

    assert result["exists"] is True
    assert result["total_lines"] == 3
    assert result["severity_counts"]["INFO"] == 1
    assert result["severity_counts"]["ERROR"] == 1
    assert result["severity_counts"]["WARNING"] == 1
    assert result["matches"] == [{"line": 2, "severity": "ERROR", "category": "Python exception"}]
    assert "private_module_name" not in str(result)


def test_analyze_log_detects_kubernetes_issue(tmp_path: Path) -> None:
    log = tmp_path / "k8s.log"
    log.write_text("pod status: CrashLoopBackOff\n", encoding="utf-8")

    result = analyze_log(log)

    assert result["matches"][0]["category"] == "Docker/Kubernetes issue"
    assert result["matches"][0]["line"] == 1


def test_analyze_log_missing_file(tmp_path: Path) -> None:
    result = analyze_log(tmp_path / "missing.log")
    assert result["exists"] is False
    assert result["matches"] == []


def test_analyze_log_rejects_oversized_file(tmp_path: Path) -> None:
    log = tmp_path / "large.log"
    log.write_text("x" * 2_000_001, encoding="utf-8")
    with pytest.raises(ValueError, match="safety limit"):
        analyze_log(log)


def test_analyze_log_caps_pattern_matches(tmp_path: Path) -> None:
    log = tmp_path / "many.log"
    log.write_text("CrashLoopBackOff\n" * 205, encoding="utf-8")

    result = analyze_log(log)

    assert len(result["matches"]) == 200
    assert result["total_lines"] == 205
