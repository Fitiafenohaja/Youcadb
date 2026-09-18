"""Tests for CLI commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from youcadb.cli import app

runner = CliRunner()


def test_init_non_interactive(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--no-interactive", "--engine", "postgres"])
    assert result.exit_code == 0
    assert "Configuration written" in result.stdout


def test_init_force_flag(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--force", "--no-interactive"])
    assert result.exit_code == 0
    assert "forced mode" in result.stdout


def test_init_with_project_name(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app, ["init", "--no-interactive", "--name", "mydb", "--engine", "mysql"]
    )
    assert result.exit_code == 0
    assert "mysql" in result.stdout.lower()


def test_create_invalid_engine() -> None:
    result = runner.invoke(app, ["create", "oracle"])
    assert result.exit_code == 1
    assert "unknown engine" in result.stderr


def test_create_postgres_no_driver(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    mock_engine = MagicMock()
    mock_engine.is_available.return_value = False
    mock_engine.name = "PostgreSQL"
    mock_engine.default_port = 5432
    fake_system = MagicMock(
        psql_available=False,
        mysql_client_available=False,
        pg_service_available=False,
        mysql_service_available=False,
        docker_running=False,
    )
    with (
        patch("youcadb.commands.create.get_engine", return_value=mock_engine),
        patch("youcadb.commands.create.detect_system", return_value=fake_system),
    ):
        result = runner.invoke(app, ["create", "postgres", "--no-interactive"])
    assert result.exit_code == 1
    assert "driver" in result.stderr.lower()


def test_status_no_config(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    with patch("youcadb.commands.status.get_engine") as mock_get:
        mock_engine = MagicMock()
        mock_engine.name = "PostgreSQL"
        mock_engine.default_port = 5432
        mock_engine.is_available.return_value = False
        mock_get.return_value = mock_engine
        with patch("youcadb.commands.status.select_menu", return_value="postgres"):
            result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "STATUS" in result.stdout


def test_status_with_config(tmp_path, monkeypatch) -> None:
    from youcadb.config import DBConfig, YoucaDBConfig, save_config

    cfg = YoucaDBConfig(project_name="test", database=DBConfig(engine="postgres", name="testdb"))
    save_config(cfg, str(tmp_path))
    monkeypatch.chdir(tmp_path)

    mock_engine = MagicMock()
    mock_engine.name = "PostgreSQL"
    mock_engine.default_port = 5432
    mock_engine.is_available.return_value = False
    with patch("youcadb.commands.status.get_engine", return_value=mock_engine):
        result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "STATUS" in result.stdout


def test_doctor_no_config(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    with patch("youcadb.commands.doctor.get_engine") as mock_get:
        mock_engine = MagicMock()
        mock_engine.name = "PostgreSQL"
        mock_engine.default_port = 5432
        mock_engine.is_available.return_value = False
        mock_get.return_value = mock_engine
        with patch("youcadb.commands.doctor.select_menu", return_value="postgres"):
            result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "DOCTOR" in result.stdout


def test_doctor_healthy(tmp_path, monkeypatch) -> None:
    from youcadb.config import DBConfig, YoucaDBConfig, save_config
    from youcadb.detection.system import SystemInfo

    cfg = YoucaDBConfig(project_name="test", database=DBConfig(engine="postgres", name="testdb"))
    save_config(cfg, str(tmp_path))
    (tmp_path / ".env").write_text(
        "DATABASE_URL=postgresql://testdb:testdb@localhost:5432/testdb\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    mock_conn = MagicMock()
    mock_conn.success = True
    mock_conn.message = "Connected to PostgreSQL 16"

    mock_engine = MagicMock()
    mock_engine.name = "PostgreSQL"
    mock_engine.default_port = 5432
    mock_engine.is_available.return_value = True
    mock_engine.connect.return_value = mock_conn
    mock_engine.test_connection.return_value = mock_conn

    fake_system = SystemInfo(
        os_name="linux",
        python_version="3.12",
        psql_available=True,
    )

    with (
        patch("youcadb.doctor.get_engine", return_value=mock_engine),
        patch("youcadb.commands.doctor.detect_system", return_value=fake_system),
    ):
        result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "healthy" in result.stdout.lower()


def test_config_generate(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "generate", "--no-interactive"])
    assert result.exit_code == 0


def test_config_show_no_config(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "configuration" in result.stdout.lower() or "no" in result.stdout.lower()


def test_config_invalid_subcommand() -> None:
    result = runner.invoke(app, ["config", "foo"])
    assert result.exit_code == 1
    assert "Unknown config subcommand" in result.stderr


def test_config_generate_creates_env(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["config", "generate", "--no-interactive"])
    assert (tmp_path / ".env").exists()


def test_config_generate_never_prints_password(tmp_path, monkeypatch) -> None:
    from youcadb.config import DBConfig, YoucaDBConfig, save_config

    save_config(
        YoucaDBConfig(
            project_name="p",
            database=DBConfig(engine="postgres", name="mydb", user="admin", password="s3cret"),
        ),
        str(tmp_path),
    )
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "generate", "--no-interactive"])
    assert result.exit_code == 0
    assert "s3cret" not in result.stdout
    assert ":***" in result.stdout


def test_config_show_masks_password(tmp_path, monkeypatch) -> None:
    from youcadb.config import DBConfig, YoucaDBConfig, save_config

    save_config(
        YoucaDBConfig(
            project_name="p",
            database=DBConfig(engine="postgres", name="mydb", user="admin", password="topsekrit"),
        ),
        str(tmp_path),
    )
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "topsekrit" not in result.stdout
    assert 'password = "***"' in result.stdout
