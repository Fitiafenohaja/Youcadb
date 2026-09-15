"""Tests for UI helpers, install guide, system detection, and CLI rendering."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from youcadb.cli import app
from youcadb.detection.system import SystemInfo, detect_system
from youcadb.system.install import InstallGuide, default_unix_socket_user, install_guide
from youcadb.ui.menu import confirm, password_input, select_menu, text_input

runner = CliRunner()


# ---------- menu: questionary path ----------


def test_select_menu_uses_questionary() -> None:
    fake_q = MagicMock()
    fake_q.select.return_value.ask.return_value = "postgres"
    with patch.dict(sys.modules, {"questionary": fake_q}):
        result = select_menu("Which engine?", ["postgres", "mysql"])
    assert result == "postgres"


def test_select_menu_questionary_none() -> None:
    fake_q = MagicMock()
    fake_q.select.return_value.ask.return_value = None
    with patch.dict(sys.modules, {"questionary": fake_q}):
        result = select_menu("Which engine?", ["postgres"])
    assert result is None


def test_select_menu_questionary_raises_uses_fallback() -> None:
    fake_q = MagicMock()
    fake_q.select.side_effect = RuntimeError("no tty")
    with (
        patch.dict(sys.modules, {"questionary": fake_q}),
        patch("builtins.input", return_value="1"),
    ):
        result = select_menu("Which engine?", ["postgres", "mysql"])
    assert result == "postgres"


def test_confirm_questionary() -> None:
    fake_q = MagicMock()
    fake_q.confirm.return_value.ask.return_value = True
    with patch.dict(sys.modules, {"questionary": fake_q}):
        assert confirm("Proceed?") is True


def test_confirm_questionary_raises_uses_fallback() -> None:
    fake_q = MagicMock()
    fake_q.confirm.side_effect = RuntimeError("no tty")
    with (
        patch.dict(sys.modules, {"questionary": fake_q}),
        patch("builtins.input", return_value="yes"),
    ):
        assert confirm("Proceed?") is True
    with patch.dict(sys.modules, {"questionary": None}):
        pass


def test_password_input_getpass_fallback() -> None:
    with (
        patch.dict(sys.modules, {"questionary": None}),
        patch("getpass.getpass", return_value="sekret"),
    ):
        assert password_input("Password") == "sekret"


def test_password_input_questionary() -> None:
    fake_q = MagicMock()
    fake_q.password.return_value.ask.return_value = "sekret"
    with patch.dict(sys.modules, {"questionary": fake_q}):
        assert password_input("Password") == "sekret"


def test_text_input_questionary() -> None:
    fake_q = MagicMock()
    fake_q.text.return_value.ask.return_value = "mydb"
    with patch.dict(sys.modules, {"questionary": fake_q}):
        assert text_input("Name", default="x") == "mydb"


def test_text_input_fallback_with_default() -> None:
    with (
        patch.dict(sys.modules, {"questionary": None}),
        patch("builtins.input", return_value=""),
    ):
        assert text_input("Name", default="mydb") == "mydb"


def test_text_input_fallback() -> None:
    with (
        patch.dict(sys.modules, {"questionary": None}),
        patch("builtins.input", return_value="typed"),
    ):
        assert text_input("Name") == "typed"


# ---------- install guide ----------


def test_install_guide_macos_postgres() -> None:
    guide = install_guide("postgres", SystemInfo("darwin", "3.12"))
    assert guide.install_commands == ["brew install postgresql"]
    assert guide.start_commands == ["brew services start postgresql"]


def test_install_guide_macos_mysql() -> None:
    guide = install_guide("mysql", SystemInfo("darwin", "3.12"))
    assert "brew install mysql" in guide.install_commands


def test_install_guide_windows() -> None:
    guide = install_guide("postgres", SystemInfo("win32", "3.12"))
    assert any("winget" in cmd for cmd in guide.install_commands)


def test_install_guide_linux_apt(patch_distro) -> None:
    guide = install_guide("postgres", SystemInfo("linux", "3.12"))
    assert any("apt install postgresql" in c for c in guide.install_commands)


def test_install_guide_linux_dnf() -> None:
    with patch("youcadb.system.install._detect_distro", return_value="fedora"):
        guide = install_guide("mysql", SystemInfo("linux", "3.12"))
    assert any("dnf install mysql-server" in c for c in guide.install_commands)


def test_install_guide_docker_command() -> None:
    pg = install_guide("postgres", SystemInfo("linux", "3.12"))
    assert "postgres:17" in pg.docker_command
    my = install_guide("mysql", SystemInfo("linux", "3.12"))
    assert "mysql:8" in my.docker_command


def test_default_unix_socket_user_linux() -> None:
    with patch("sys.platform", "linux"):
        import getpass

        assert default_unix_socket_user("postgres") == getpass.getuser()
        assert default_unix_socket_user("mysql") == "root"


def test_install_guide_dataclass() -> None:
    g = InstallGuide("x", ["a"], ["b"], "c")
    assert g.engine == "x"


def test_install_guide_unknown_platform_fallback() -> None:
    guide = install_guide("postgres", SystemInfo("plan9", "3.12"))
    assert guide.install_commands


@pytest.fixture
def patch_distro() -> None:  # helper fixture no-op body
    with patch("youcadb.system.install._detect_distro", return_value="debian"):
        yield


# ---------- system detection ----------


def test_detect_system_docker_running() -> None:
    with (
        patch("shutil.which", return_value="/usr/bin/docker"),
        patch(
            "youcadb.detection.system.subprocess.run",
            return_value=MagicMock(returncode=0),
        ),
    ):
        info = detect_system()
    assert info.docker_available is True
    assert info.docker_running is True


def test_detect_system_docker_not_running() -> None:
    with (
        patch("shutil.which", return_value="/usr/bin/docker"),
        patch(
            "youcadb.detection.system.subprocess.run",
            return_value=MagicMock(returncode=1),
        ),
    ):
        info = detect_system()
    assert info.docker_running is False


def test_detect_system_service_active() -> None:
    with (
        patch(
            "shutil.which",
            side_effect=lambda name: "/usr/bin/systemctl" if name == "systemctl" else None,
        ),
        patch(
            "youcadb.detection.system.subprocess.run",
            return_value=MagicMock(returncode=0),
        ),
    ):
        info = detect_system()
    assert info.pg_service_available is True


# ---------- __main__ ----------


def test_main_module_importable() -> None:
    import importlib

    main = importlib.import_module("youcadb.__main__")
    assert hasattr(main, "app")


# ---------- config command interactive ----------


def test_config_generate_with_config_prompts(tmp_path, monkeypatch) -> None:
    from youcadb.config import DBConfig, YoucaDBConfig, save_config

    save_config(
        YoucaDBConfig(project_name="p", database=DBConfig(engine="postgres")), str(tmp_path)
    )
    monkeypatch.chdir(tmp_path)
    with (
        patch("youcadb.commands.config.text_input", return_value="mydb"),
        patch("youcadb.commands.config.password_input", return_value="pw"),
    ):
        result = runner.invoke(app, ["config", "generate"])
    assert result.exit_code == 0
    assert (tmp_path / ".env").exists()


def test_config_generate_refuses_overwrite(tmp_path, monkeypatch) -> None:
    (tmp_path / ".env").write_text("POINTER=1\n")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "generate", "--no-interactive"])
    assert result.exit_code == 1
    assert "already exists" in result.stderr


def test_config_show_with_config(tmp_path, monkeypatch) -> None:
    from youcadb.config import DBConfig, YoucaDBConfig, save_config

    save_config(
        YoucaDBConfig(project_name="p", database=DBConfig(engine="postgres")), str(tmp_path)
    )
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "engine" in result.stdout


# ---------- cli render paths ----------


def test_cli_no_args_configured_healthy(tmp_path, monkeypatch) -> None:
    from youcadb.config import DBConfig, YoucaDBConfig, save_config

    save_config(
        YoucaDBConfig(
            project_name="p",
            database=DBConfig(engine="postgres", name="mydb", user="u", password="p"),
        ),
        str(tmp_path),
    )
    monkeypatch.chdir(tmp_path)
    fake_conn = MagicMock(success=True, message="ok", server_version="16")
    mock_engine = MagicMock(
        is_available=MagicMock(return_value=True),
        connect=MagicMock(return_value=fake_conn),
        name="PostgreSQL",
    )
    with patch("youcadb.engines.get_engine", return_value=mock_engine):
        result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "HEALTHY" in result.stdout


def test_cli_no_args_configured_unhealthy(tmp_path, monkeypatch) -> None:
    from youcadb.config import DBConfig, YoucaDBConfig, save_config

    save_config(
        YoucaDBConfig(project_name="p", database=DBConfig(engine="postgres", name="mydb")),
        str(tmp_path),
    )
    monkeypatch.chdir(tmp_path)
    fake_conn = MagicMock(success=False, message="unreachable", server_version=None)
    mock_engine = MagicMock(
        is_available=MagicMock(return_value=True),
        connect=MagicMock(return_value=fake_conn),
        name="PostgreSQL",
    )
    with patch("youcadb.engines.get_engine", return_value=mock_engine):
        result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "UNHEALTHY" in result.stdout


def test_cli_no_args_missing_driver(tmp_path, monkeypatch) -> None:
    from youcadb.config import DBConfig, YoucaDBConfig, save_config

    save_config(
        YoucaDBConfig(project_name="p", database=DBConfig(engine="postgres")),
        str(tmp_path),
    )
    monkeypatch.chdir(tmp_path)
    mock_engine = MagicMock(is_available=MagicMock(return_value=False), name="PostgreSQL")
    with patch("youcadb.engines.get_engine", return_value=mock_engine):
        result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "UNHEALTHY" in result.stdout
