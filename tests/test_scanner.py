from pathlib import Path

from ranit.scanner import scan_project


def test_scan_detects_possible_hardcoded_secret_without_returning_value(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text('api_key = "abcdefghijk-secret-value"\n', encoding="utf-8")
    result = scan_project(tmp_path)
    assert any("credential" in item["rule"].lower() for item in result["findings"])
    assert "secret-value" not in str(result)


def test_scan_finds_env_and_deployment_markers(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("EXAMPLE=value\n", encoding="utf-8")
    (tmp_path / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")
    result = scan_project(tmp_path)
    assert any("Environment file" in item["rule"] for item in result["findings"])
    assert "Dockerfile" in result["deployment_files"]


def test_scan_handles_missing_directory(tmp_path: Path) -> None:
    result = scan_project(tmp_path / "missing")
    assert result["exists"] is False
