"""Tests for the ``youcadb create`` interactive wizard."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from youcadb.cli import app
from youcadb.commands.create import _prompt_engine, _try_start_docker

runner = CliRunner()


def _mock_engine(
    available: bool = True, create_ok: bool = True, connect_ok: bool = True
) -> MagicMock:
    engine = MagicMock(name="PostgreSQL")
    engine.name = "PostgreSQL"
    engine.default_port = 5432
    engine.is_available.return_value = available
    engine.connect.return_value = MagicMock(
        success=connect_ok, message="unreachable", server_version="16" if connect_ok else None
    )
    engine.create_database.return_value = MagicMock(
        success=create_ok, message="created" if create_ok else "failed"
    )
    engine.create_user.return_value = MagicMock(success=True, message="user created")
    engine.test_connection.return_value = MagicMock(success=True, message="ok")
    return engine


def test_prompt_engine_defaults_postgres() -> None:
    with patch("youcadb.ui.menu.select_menu", return_value=None):
        assert _prompt_engine() == "postgres"


def test_prompt_engine_choice() -> None:
    with patch("youcadb.ui.menu.select_menu", return_value="mysql"):
        assert _prompt_engine() == "mysql"


def test_create_noninteractive_requires_engine() -> None:
    result = runner.invoke(app, ["create", "--no-interactive"])
    assert result.exit_code == 1
    assert "engine argument is required" in result.stderr


def test_create_unknown_engine() -> None:
    result = runner.invoke(app, ["create", "oracle", "--no-interactive"])
    assert result.exit_code == 1
    assert "unknown engine" in result.stderr


def test_create_noninteractive_success(monkeypatch) -> None:
    engine = _mock_engine()
    monkeypatch.setenv("YOUCADB_PASSWORD", "pw")
    with patch("youcadb.commands.create.get_engine", return_value=engine):
        result = runner.invoke(
            app,
            [
                "create",
                "postgres",
                "--no-interactive",
                "--name",
                "mydb",
                "--user",
                "bob",
            ],
        )
    assert result.exit_code == 0
    assert "created successfully" in result.stdout
    engine.create_database.assert_called_once()
    engine.create_user.assert_called_once()


def test_create_noninteractive_db_failure() -> None:
    engine = _mock_engine(create_ok=False)
    with patch("youcadb.commands.create.get_engine", return_value=engine):
        result = runner.invoke(app, ["create", "postgres", "--no-interactive", "--name", "mydb"])
    assert result.exit_code == 1
    assert "failed" in result.stderr


def test_create_ensure_engine_driver_missing() -> None:
    engine = _mock_engine(available=False)
    system = MagicMock(
        psql_available=False,
        mysql_client_available=False,
        pg_service_available=False,
        mysql_service_available=False,
        docker_running=False,
    )
    with (
        patch("youcadb.commands.create.get_engine", return_value=engine),
        patch("youcadb.commands.create.detect_system", return_value=system),
    ):
        result = runner.invoke(app, ["create", "postgres", "--no-interactive", "--name", "mydb"])
    assert result.exit_code == 1
    assert "driver is not installed" in result.stderr


def test_create_driver_missing_shows_install_guide() -> None:
    engine = _mock_engine(available=False)
    system = MagicMock(
        psql_available=False,
        mysql_client_available=False,
        pg_service_available=False,
        mysql_service_available=False,
        docker_running=False,
    )
    with (
        patch("youcadb.commands.create.get_engine", return_value=engine),
        patch("youcadb.commands.create.detect_system", return_value=system),
    ):
        result = runner.invoke(app, ["create", "postgres", "--no-interactive", "--name", "mydb"])
    assert result.exit_code == 1
    assert "driver is not installed" in result.stderr
    assert "Install it with" in result.stderr


def test_create_driver_missing_docker_offer_still_blocks() -> None:
    engine = _mock_engine(available=False)
    system = MagicMock(
        psql_available=False,
        mysql_client_available=False,
        pg_service_available=False,
        mysql_service_available=False,
        docker_running=True,
    )
    with (
        patch("youcadb.commands.create.get_engine", return_value=engine),
        patch("youcadb.commands.create.detect_system", return_value=system),
        patch("youcadb.commands.create.confirm", return_value=True),
        patch("youcadb.commands.create._try_start_docker", return_value=True),
    ):
        result = runner.invoke(app, ["create", "postgres", "--no-interactive", "--name", "mydb"])
    assert result.exit_code == 1
    assert "Python driver must be installed" in result.stderr


def test_create_ensure_engine_unreachable_with_service() -> None:
    engine = _mock_engine(connect_ok=False)
    system = MagicMock(
        psql_available=True,
        mysql_client_available=False,
        pg_service_available=False,
        mysql_service_available=False,
        docker_running=False,
    )
    with (
        patch("youcadb.commands.create.get_engine", return_value=engine),
        patch("youcadb.commands.create.detect_system", return_value=system),
    ):
        result = runner.invoke(app, ["create", "postgres", "--no-interactive", "--name", "mydb"])
    assert result.exit_code == 1
    assert "service is stopped" in result.stderr


def test_create_ensure_engine_unreachable_no_install() -> None:
    engine = _mock_engine(connect_ok=False)
    system = MagicMock(
        psql_available=False,
        mysql_client_available=False,
        pg_service_available=False,
        mysql_service_available=False,
        docker_running=False,
    )
    with (
        patch("youcadb.commands.create.get_engine", return_value=engine),
        patch("youcadb.commands.create.detect_system", return_value=system),
    ):
        result = runner.invoke(app, ["create", "postgres", "--no-interactive", "--name", "mydb"])
    assert result.exit_code == 1
    assert "Install it with" in result.stderr


def test_create_ensure_engine_unreachable_docker_offer() -> None:
    engine = _mock_engine(connect_ok=False)
    system = MagicMock(
        psql_available=False,
        mysql_client_available=False,
        pg_service_available=False,
        mysql_service_available=False,
        docker_running=True,
    )
    with (
        patch("youcadb.commands.create.get_engine", return_value=engine),
        patch("youcadb.commands.create.detect_system", return_value=system),
        patch("youcadb.commands.create.confirm", return_value=True),
        patch("youcadb.commands.create._try_start_docker", return_value=False),
    ):
        result = runner.invoke(app, ["create", "postgres", "--no-interactive", "--name", "mydb"])
    assert result.exit_code == 1
    assert "does not appear to be installed" in result.stderr


def test_create_engine_unreachable_starts_docker_daemon() -> None:
    engine = _mock_engine(connect_ok=False)
    stopped = MagicMock(
        psql_available=False,
        mysql_client_available=False,
        pg_service_available=False,
        mysql_service_available=False,
        docker_available=True,
        docker_running=False,
    )
    running = MagicMock(docker_available=True, docker_running=True)
    with (
        patch("youcadb.commands.create.get_engine", return_value=engine),
        patch(
            "youcadb.commands.create.detect_system",
            side_effect=[stopped, running, running],
        ),
        patch("youcadb.commands.create.confirm", return_value=True),
        patch(
            "youcadb.commands.create.subprocess.run",
            return_value=MagicMock(returncode=0),
        ),
        patch("youcadb.commands.create._try_start_docker", return_value=True),
    ):
        result = runner.invoke(app, ["create", "postgres", "--no-interactive", "--name", "mydb"])
    assert result.exit_code == 0
    assert "Running: sudo systemctl start docker" in result.stderr
    assert "created successfully" in result.stdout


def test_create_engine_unreachable_daemon_declined() -> None:
    engine = _mock_engine(connect_ok=False)
    stopped = MagicMock(
        psql_available=False,
        mysql_client_available=False,
        pg_service_available=False,
        mysql_service_available=False,
        docker_available=True,
        docker_running=False,
    )
    with (
        patch("youcadb.commands.create.get_engine", return_value=engine),
        patch("youcadb.commands.create.detect_system", return_value=stopped),
        patch("youcadb.commands.create.confirm", return_value=False),
    ):
        result = runner.invoke(app, ["create", "postgres", "--no-interactive", "--name", "mydb"])
    assert result.exit_code == 1
    assert "does not appear to be installed" in result.stderr


def test_try_start_docker_success() -> None:
    engine = _mock_engine()
    with (
        patch(
            "youcadb.commands.create.detect_system", return_value=MagicMock(docker_running=True)
        ),
        patch(
            "youcadb.commands.create.subprocess.run",
            return_value=MagicMock(returncode=0),
        ),
        patch("youcadb.commands.create.time.sleep"),
        patch("youcadb.commands.create.get_engine", return_value=engine),
    ):
        ok = _try_start_docker("postgres", "localhost", 5432, "postgres", "pw")
    assert ok is True


def test_try_start_docker_docker_fails() -> None:
    with (
        patch(
            "youcadb.commands.create.detect_system", return_value=MagicMock(docker_running=True)
        ),
        patch(
            "youcadb.commands.create.subprocess.run",
            return_value=MagicMock(returncode=1),
        ),
    ):
        ok = _try_start_docker("postgres", "localhost", 5432, "postgres", "pw")
    assert ok is False


def test_try_start_docker_server_never_ready() -> None:
    engine = _mock_engine(connect_ok=False)
    with (
        patch(
            "youcadb.commands.create.detect_system", return_value=MagicMock(docker_running=True)
        ),
        patch(
            "youcadb.commands.create.subprocess.run",
            return_value=MagicMock(returncode=0),
        ),
        patch("youcadb.commands.create.time.sleep"),
        patch("youcadb.commands.create.get_engine", return_value=engine),
    ):
        ok = _try_start_docker("postgres", "localhost", 5432, "postgres", "pw")
    assert ok is False


def test_try_start_docker_subprocess_raises() -> None:
    with (
        patch(
            "youcadb.commands.create.detect_system", return_value=MagicMock(docker_running=True)
        ),
        patch(
            "youcadb.commands.create.subprocess.run",
            side_effect=RuntimeError("boom"),
        ),
    ):
        ok = _try_start_docker("postgres", "localhost", 5432, "postgres", "pw")
    assert ok is False


def test_wait_for_port_success(monkeypatch) -> None:
    import time

    import youcadb.commands.create as create_mod

    monkeypatch.setattr(time, "sleep", lambda _s: None)
    monkeypatch.setattr(create_mod.socket, "create_connection", lambda *_a, **_k: MagicMock())
    assert create_mod._wait_for_port("localhost", 5432) is True


def test_wait_for_port_never_opens(monkeypatch) -> None:
    import time

    import youcadb.commands.create as create_mod

    monkeypatch.setattr(time, "sleep", lambda _s: None)
    monkeypatch.setattr(
        create_mod.socket,
        "create_connection",
        MagicMock(side_effect=OSError("refused")),
    )
    assert create_mod._wait_for_port("localhost", 5432, attempts=3, delay=0.1) is False


def test_create_interactive_success(tmp_path, monkeypatch) -> None:
    engine = _mock_engine()

    values = iter(["mydb", "bob", "pw", "", ""])

    def fake_input(prompt: str, default: str | None = None) -> str:
        return next(values)

    def fake_password(prompt: str) -> str:
        return "pw"

    monkeypatch.chdir(tmp_path)
    with (
        patch("youcadb.commands.create.get_engine", return_value=engine),
        patch("youcadb.commands.create.text_input", side_effect=fake_input),
        patch("youcadb.commands.create.password_input", side_effect=fake_password),
        patch("youcadb.commands.create.confirm", return_value=False),
    ):
        result = runner.invoke(app, ["create", "postgres", "--interactive"])
    assert result.exit_code == 0
    assert "created successfully" in result.stdout


def test_create_interactive_updates_config(tmp_path, monkeypatch) -> None:
    from youcadb.config import (
        DBConfig,
        YoucaDBConfig,
        load_config,
        save_config,
    )

    save_config(
        YoucaDBConfig(project_name="p", database=DBConfig(engine="postgres")),
        str(tmp_path),
    )
    eng = _mock_engine()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("YOUCADB_PASSWORD", "apppw")
    monkeypatch.setenv("YOUCADB_ADMIN_PASSWORD", "x")
    with (
        patch("youcadb.commands.create.get_engine", return_value=eng),
        patch("youcadb.commands.create.text_input", side_effect=["mydb", "bob", "5432"]),
        patch("youcadb.commands.create.confirm", return_value=True),
    ):
        result = runner.invoke(app, ["create", "postgres", "--interactive", "--port", "5433"])
    assert result.exit_code == 0
    cfg = load_config(str(tmp_path))
    assert cfg is not None
    assert cfg.database.name == "mydb"
    assert cfg.database.user == "bob"
    assert cfg.database.engine == "postgres"
