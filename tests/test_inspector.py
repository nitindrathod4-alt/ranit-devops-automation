from pathlib import Path

from ranit.inspector import inspect_project


def test_missing_project_is_reported(tmp_path: Path) -> None:
    result = inspect_project(tmp_path / "missing")
    assert result["exists"] is False
    assert result["markers"] == []


def test_detects_common_project_markers(tmp_path: Path) -> None:
    (tmp_path / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("print('not executed')\n", encoding="utf-8")
    result = inspect_project(tmp_path)
    assert result["exists"] is True
    assert "Dockerfile" in result["markers"]
    assert "Python (pyproject.toml)" in result["markers"]
    assert result["files_scanned"] == 3


def test_ignores_generated_directories(tmp_path: Path) -> None:
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    result = inspect_project(tmp_path)
    assert "Node.js / JavaScript" in result["markers"]
    assert result["files_scanned"] == 1
