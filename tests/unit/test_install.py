"""Tests for OS-aware installation guidance."""

from __future__ import annotations

import pytest

from youcadb.detection.system import SystemInfo
from youcadb.system.install import _detect_distro, default_unix_socket_user, install_guide


def _system(os_name: str = "linux") -> SystemInfo:
    return SystemInfo(os_name=os_name, python_version="3.12.3")


def test_install_guide_windows_postgres() -> None:
    guide = install_guide("postgres", _system("win32"))
    assert guide.install_commands == [
        "winget install PostgreSQL.PostgreSQL",
        "or download the installer from https://www.postgresql.org/download/",
    ]
    assert guide.start_commands == ["Start-Service postgresql"]


def test_install_guide_windows_mysql() -> None:
    guide = install_guide("mysql", _system("win32"))
    assert "winget install Oracle.MySQL" in guide.install_commands[0]
    assert guide.start_commands == ["Start-Service mysql"]


def test_install_guide_macos_postgres() -> None:
    guide = install_guide("postgres", _system("darwin"))
    assert guide.install_commands == ["brew install postgresql"]
    assert guide.start_commands == ["brew services start postgresql"]


def test_install_guide_macos_mysql() -> None:
    guide = install_guide("mysql", _system("darwin"))
    assert guide.install_commands == ["brew install mysql"]
    assert guide.start_commands == ["brew services start mysql"]


@pytest.mark.parametrize(
    ("distro", "engine", "install", "start"),
    [
        (
            "ubuntu",
            "postgres",
            "sudo apt install postgresql postgresql-client",
            "sudo systemctl start postgresql",
        ),
        (
            "fedora",
            "postgres",
            "sudo dnf install postgresql-server postgresql",
            "sudo systemctl enable --now postgresql",
        ),
        ("ubuntu", "mysql", "sudo apt install mysql-server", "sudo systemctl start mysql"),
        ("fedora", "mysql", "sudo dnf install mysql-server", "sudo systemctl start mysqld"),
    ],
)
def test_install_guide_linux_distros(
    monkeypatch, distro: str, engine: str, install: str, start: str
) -> None:
    monkeypatch.setattr("youcadb.system.install._detect_distro", lambda: distro)
    guide = install_guide(engine, _system("linux"))
    assert guide.install_commands[0] == install
    assert guide.start_commands[0] == start


def test_install_guide_linux_unknown_distro_falls_back(
    monkeypatch,
) -> None:
    monkeypatch.setattr("youcadb.system.install._detect_distro", lambda: None)
    guide = install_guide("mysql", _system("linux"))
    assert guide.install_commands[0].startswith("sudo apt install mysql-server")


def test_install_guide_docker_commands() -> None:
    assert "postgres:17" in install_guide("postgres", _system("darwin")).docker_command
    assert "mysql:8" in install_guide("mysql", _system("linux")).docker_command


def test_detect_distro_returns_none_on_errors(monkeypatch) -> None:
    import platform

    def raise_error(*_args, **_kwargs):
        raise RuntimeError("cannot read os-release")

    monkeypatch.setattr(platform, "freedesktop_os_release", raise_error)
    monkeypatch.setattr("builtins.open", raise_error)
    assert _detect_distro() is None


def test_default_unix_socket_user_darwin(monkeypatch) -> None:
    monkeypatch.setattr("youcadb.system.install.sys.platform", "darwin")
    assert default_unix_socket_user("postgres") == "postgres"
    assert default_unix_socket_user("mysql") == "root"


def test_default_unix_socket_user_linux_postgres(monkeypatch) -> None:
    import getpass

    monkeypatch.setattr("youcadb.system.install.sys.platform", "linux")
    assert default_unix_socket_user("postgres") == getpass.getuser()
    assert default_unix_socket_user("mysql") == "root"
