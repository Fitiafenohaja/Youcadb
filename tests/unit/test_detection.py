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


def test_detect_python_multiple_drivers_ambiguous(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "t"\ndependencies = ["psycopg[binary]", "pymysql"]\n'
    )
    result = detect_project(str(tmp_path))
    assert result.engine_hint is None
    assert any("Multiple database drivers" in d for d in result.details)


def test_detect_node_multiple_drivers_ambiguous(tmp_path) -> None:
    import json

    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"pg": "^8", "mysql2": "^3"}})
    )
    result = detect_project(str(tmp_path))
    assert result.engine_hint is None


def test_detect_dockerfile(tmp_path) -> None:
    (tmp_path / "Dockerfile").write_text("FROM python:3.12\n")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "t"\ndependencies = []\n')
    result = detect_project(str(tmp_path))
    assert result.dockerfile is True
    assert any("Dockerfile detected" in d for d in result.details)


def test_detect_env_values_and_engine_from_url(tmp_path) -> None:
    (tmp_path / ".env").write_text(
        "DATABASE_URL=postgresql://alice:pw@dbhost:5433/appdb\nDB_HOST=dbhost\nDB_USER=alice\n"
    )
    result = detect_project(str(tmp_path))
    assert result.engine_hint == "postgres"
    assert result.env["DB_USER"] == "alice"
    assert result.env["DATABASE_URL"].startswith("postgresql://")
    assert any("DATABASE_URL detected" in d for d in result.details)


def test_detect_mysql_url_takes_precedence(tmp_path) -> None:
    (tmp_path / ".env.example").write_text("DATABASE_URL=mysql://root:pw@localhost:3306/app\n")
    result = detect_project(str(tmp_path))
    assert result.engine_hint == "mysql"


def test_detect_php_laravel_mysql(tmp_path) -> None:
    import json

    (tmp_path / "composer.json").write_text(
        json.dumps({"require": {"laravel/framework": "^10", "ext-pdo_mysql": "*"}})
    )
    result = detect_project(str(tmp_path))
    assert result.language == "PHP"
    assert "Laravel" in (result.framework or "")
    assert result.engine_hint == "mysql"


def test_detect_php_pgsql(tmp_path) -> None:
    import json

    (tmp_path / "composer.json").write_text(
        json.dumps({"require": {"ext-pdo_pgsql": "*", "symfony/symfony": "^6"}})
    )
    result = detect_project(str(tmp_path))
    assert result.language == "PHP"
    assert result.engine_hint == "postgres"


def test_detect_ruby_rails_pg(tmp_path) -> None:
    (tmp_path / "Gemfile").write_text(
        'source "https://rubygems.org"\ngem "rails", "~> 7.0"\ngem "pg"\n'
    )
    result = detect_project(str(tmp_path))
    assert result.language == "Ruby"
    assert "Ruby on Rails" in (result.framework or "")
    assert result.engine_hint == "postgres"


def test_detect_ruby_mysql2(tmp_path) -> None:
    (tmp_path / "Gemfile").write_text(
        'source "https://rubygems.org"\ngem "mysql2"\ngem "sinatra"\n'
    )
    result = detect_project(str(tmp_path))
    assert result.language == "Ruby"
    assert result.engine_hint == "mysql"
