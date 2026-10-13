from pathlib import Path

from ranit.health import check_project_health


def test_missing_project_reports_error(tmp_path: Path) -> None:
    result = check_project_health(tmp_path / "missing")
    assert result["exists"] is False
    assert result["status"] == "ERROR"
    assert result["checks"] == []


def test_detects_python_marker_and_runtime_check(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    monkeypatch.setattr("ranit.health.shutil.which", lambda command: "C:/Python/python.exe" if command == "python" else None)
    result = check_project_health(tmp_path)
    assert result["status"] == "OK"
    assert result["markers"] == ["Python (pyproject.toml)"]
    assert result["checks"][0]["status"] == "available"


def test_missing_required_tool_is_warning(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")
    monkeypatch.setattr("ranit.health.shutil.which", lambda command: None)
    result = check_project_health(tmp_path)
    assert result["status"] == "WARNING"
    assert result["checks"][0]["status"] == "missing"
    assert any("Docker CLI was not found" in issue for issue in result["issues"])


def test_unknown_project_markers_report_warning(tmp_path: Path) -> None:
    (tmp_path / "notes.txt").write_text("hello\n", encoding="utf-8")
    result = check_project_health(tmp_path)
    assert result["exists"] is True
    assert result["status"] == "ERROR"
    assert result["issues"] == ["No recognized project/build markers were found."]
