
from pathlib import Path

import pytest

from ranit.diagnose import diagnose_log


def test_diagnose_python_import_error_without_returning_log_contents(
    tmp_path: Path,
) -> None:
    log = tmp_path / "app.log"
    log.write_text(
        "ModuleNotFoundError: No module named 'sample_private_value'\n",
        encoding="utf-8",
    )
    result = diagnose_log(log)

    assert result["exists"] is True
    assert any(
        item["category"] == "Python import/module error"
        for item in result["diagnoses"]
    )
    assert "sample_private_value" not in str(result)


def test_diagnose_missing_log(tmp_path: Path) -> None:
    result = diagnose_log(tmp_path / "missing.log")

    assert result["exists"] is False
    assert result["diagnoses"] == []


def test_diagnose_rejects_oversized_log(tmp_path: Path) -> None:
    log = tmp_path / "large.log"
    log.write_text("x" * 2_000_001, encoding="utf-8")

    with pytest.raises(ValueError, match="safety limit"):
        diagnose_log(log)


def test_diagnose_network_timeout(tmp_path: Path) -> None:
    log = tmp_path / "network.log"
    log.write_text("Connection timed out", encoding="utf-8")
    result = diagnose_log(log)

    assert any(
        item["category"] == "Network/timeout error"
        for item in result["diagnoses"]
    )


def test_diagnose_docker_daemon_unavailable(tmp_path: Path) -> None:
    log = tmp_path / "docker.log"
    log.write_text(
        "Cannot connect to the Docker daemon",
        encoding="utf-8",
    )
    result = diagnose_log(log)

    assert any(
        item["category"] == "Docker daemon unavailable"
        for item in result["diagnoses"]
    )


def test_diagnose_docker_port_conflict(tmp_path: Path) -> None:
    log = tmp_path / "docker.log"
    log.write_text(
        "Bind for 0.0.0.0:8080 failed: port is already allocated",
        encoding="utf-8",
    )
    result = diagnose_log(log)

    assert any(
        item["category"] == "Docker port conflict"
        for item in result["diagnoses"]
    )
