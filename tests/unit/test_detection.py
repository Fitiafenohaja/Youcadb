"""Tests for detection modules."""

from __future__ import annotations

from youcadb.detection.project import ProjectInfo, detect_project
from youcadb.detection.system import SystemInfo, detect_system


def test_detect_project_returns_project_info() -> None:
    result = detect_project()
    assert isinstance(result, ProjectInfo)


def test_detect_system_returns_system_info() -> None:
    result = detect_system()
    assert isinstance(result, SystemInfo)
    assert result.os_name
    assert result.python_version


def test_detect_project_empty_dir(tmp_path) -> None:
    result = detect_project(str(tmp_path))
    assert result.language is None
    assert result.framework is None
    assert result.database_driver is None
    assert result.details == []


def test_detect_python_project(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "test"\ndependencies = ["fastapi", "psycopg[binary]"]\n'
    )
    result = detect_project(str(tmp_path))
    assert result.language == "Python"
    assert "psycopg" in (result.database_driver or "").lower()
    assert result.engine_hint == "postgres"


def test_detect_python_mysql(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "test"\ndependencies = ["flask", "pymysql"]\n'
    )
    result = detect_project(str(tmp_path))
    assert result.language == "Python"
    assert result.engine_hint == "mysql"


def test_detect_node_project(tmp_path) -> None:
    import json

    pkg = {"dependencies": {"express": "^4", "pg": "^8"}}
    (tmp_path / "package.json").write_text(json.dumps(pkg))
    result = detect_project(str(tmp_path))
    assert result.language == "Node.js"
    assert result.engine_hint == "postgres"
    assert "Express" in (result.framework or "")


def test_detect_node_mysql(tmp_path) -> None:
    import json

    pkg = {"dependencies": {"mysql2": "^3"}}
    (tmp_path / "package.json").write_text(json.dumps(pkg))
    result = detect_project(str(tmp_path))
    assert result.language == "Node.js"
    assert result.engine_hint == "mysql"


def test_detect_docker_compose(tmp_path) -> None:
    (tmp_path / "docker-compose.yml").write_text("services:\n  db:\n")
    result = detect_project(str(tmp_path))
    assert result.docker_compose is True


def test_detect_env_file(tmp_path) -> None:
    (tmp_path / ".env").write_text("DB_HOST=localhost\n")
    result = detect_project(str(tmp_path))
    assert result.env_file is True


def test_detect_requirements_txt(tmp_path) -> None:
    (tmp_path / "requirements.txt").write_text("fastapi\nasyncpg\n")
    result = detect_project(str(tmp_path))
    assert result.language == "Python"
    assert result.engine_hint == "postgres"
