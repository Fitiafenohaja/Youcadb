"""OS-aware installation guidance and service commands."""

from __future__ import annotations

import shlex
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from youcadb.detection.system import SystemInfo


@dataclass(frozen=True)
class InstallGuide:
    """Installation guidance for a database engine on a specific OS."""

    engine: str
    install_commands: list[str]
    start_commands: list[str]
    docker_command: str


def _detect_distro() -> str | None:
    """Try to identify the Linux distribution."""
    try:
        import platform

        distro = platform.freedesktop_os_release()
        return distro.get("ID")
    except Exception:
        try:
            with open("/etc/os-release", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("ID="):
                        return line.strip().split("=", 1)[1].strip('"')
        except Exception:
            pass
    return None


def install_guide(
    engine: str,
    system: SystemInfo,
    docker_port: int | None = None,
    docker_password: str = "",
) -> InstallGuide:
    """Return OS-aware install/start/docker guidance for a database engine.

    ``docker_port`` is the host port the container should publish (defaults to
    the engine's native port); ``docker_password`` sets the admin password used
    by the container (defaults to the engine's conventional development value).
    The container name is derived from the port so parallel instances do not clash.
    """
    os_name = system.os_name

    if engine == "postgres":
        port = docker_port or 5432
        pw = shlex.quote(docker_password or "postgres")
        docker_command = (
            f"docker run --name youcadb-pg-{port} -e POSTGRES_PASSWORD={pw} "
            f"-p {port}:5432 -d postgres:17"
        )
    else:
        port = docker_port or 3306
        pw = shlex.quote(docker_password or "root")
        docker_command = (
            f"docker run --name youcadb-mysql-{port} -e MYSQL_ROOT_PASSWORD={pw} "
            f"-p {port}:3306 -d mysql:8"
        )

    if os_name == "darwin":
        if engine == "postgres":
            return InstallGuide(
                engine=engine,
                install_commands=["brew install postgresql"],
                start_commands=["brew services start postgresql"],
                docker_command=docker_command,
            )
        return InstallGuide(
            engine=engine,
            install_commands=["brew install mysql"],
            start_commands=["brew services start mysql"],
            docker_command=docker_command,
        )

    if os_name.startswith("win"):
        if engine == "postgres":
            return InstallGuide(
                engine=engine,
                install_commands=[
                    "winget install PostgreSQL.PostgreSQL",
                    "or download the installer from https://www.postgresql.org/download/",
                ],
                start_commands=["Start-Service postgresql"],
                docker_command=docker_command,
            )
        return InstallGuide(
            engine=engine,
            install_commands=[
                "winget install Oracle.MySQL",
                "or download the installer from https://dev.mysql.com/downloads/",
            ],
            start_commands=["Start-Service mysql"],
            docker_command=docker_command,
        )

    distro = _detect_distro()
    apt_based = distro in ("debian", "ubuntu", "linuxmint", "pop")
    dnf_based = distro in ("fedora", "rhel", "centos", "rocky", "almalinux")

    if engine == "postgres":
        if apt_based:
            install = ["sudo apt install postgresql postgresql-client"]
            start = ["sudo systemctl start postgresql"]
        elif dnf_based:
            install = ["sudo dnf install postgresql-server postgresql"]
            start = ["sudo systemctl enable --now postgresql"]
        else:
            install = ["sudo apt install postgresql postgresql-client"]
            start = ["sudo systemctl start postgresql"]
    else:
        if apt_based:
            install = ["sudo apt install mysql-server"]
            start = ["sudo systemctl start mysql"]
        elif dnf_based:
            install = ["sudo dnf install mysql-server"]
            start = ["sudo systemctl start mysqld"]
        else:
            install = ["sudo apt install mysql-server"]
            start = ["sudo systemctl start mysql"]

    return InstallGuide(
        engine=engine,
        install_commands=install,
        start_commands=start,
        docker_command=docker_command,
    )


def default_unix_socket_user(engine: str) -> str:
    """Return the default admin user for the engine."""
    if sys.platform == "darwin":
        return "postgres" if engine == "postgres" else "root"
    if engine == "postgres":
        import getpass

        return getpass.getuser()
    return "root"
