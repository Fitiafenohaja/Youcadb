"""``youcadb create`` — create a new database instance."""

from __future__ import annotations

import os
import shlex
import socket
import subprocess
import time

import typer

from youcadb import config as config_model
from youcadb.detection.system import SystemInfo, detect_system
from youcadb.engines import get_engine
from youcadb.system.install import install_guide
from youcadb.ui.menu import confirm, password_input, text_input

VALID_ENGINES = ("postgres", "mysql")


def _prompt_engine() -> str:
    from youcadb.ui.menu import select_menu

    choice = select_menu("Database engine?", ["postgres", "mysql"])
    return choice or "postgres"


def _wait_for_port(host: str, port: int, attempts: int = 10, delay: float = 2.0) -> bool:
    """Wait until the host accepts TCP connections. Driver-independent."""
    for _ in range(attempts):
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except OSError:
            time.sleep(delay)
    return False


def _try_start_docker(engine_name: str, host: str, port: int, user: str, password: str) -> bool:
    """Start a dedicated container and wait for the engine to accept connections."""
    guide = install_guide(engine_name, detect_system(), docker_port=port, docker_password=password)
    typer.echo(f"  Starting: {guide.docker_command}", err=True)
    try:
        proc = subprocess.run(shlex.split(guide.docker_command), capture_output=True, timeout=30)
        started = proc.returncode == 0
    except Exception as exc:
        typer.echo(f"  Could not start the Docker container: {exc}", err=True)
        return False

    if not started:
        stderr = (proc.stderr or b"").decode(errors="replace").strip().splitlines()
        detail = f": {stderr[-1]}" if stderr else ""
        typer.echo(f"  The Docker container could not be started{detail}.", err=True)
        return False

    engine = get_engine(engine_name)
    typer.echo("  Waiting for the container to accept connections...", err=True)
    if engine.is_available():
        for _ in range(30):
            result = engine.connect(host=host, port=port, user=user, password=password)
            if result.success:
                typer.echo("  \u2713 Container is responding.", err=True)
                return True
            time.sleep(2)
    elif _wait_for_port(host, port):
        typer.echo("  \u2713 Container is responding.", err=True)
        return True
    typer.echo("  Container started but the engine did not become reachable.", err=True)
    return False


def _engine_installed(system: SystemInfo, engine_name: str) -> bool:
    """Return True when the engine appears installed on the system."""
    if engine_name == "postgres":
        return system.psql_available or system.pg_service_available
    return system.mysql_client_available or system.mysql_service_available


def _offer_missing_engine(engine_name: str, system: SystemInfo) -> None:
    """Print install/start guidance depending on whether the engine is installed."""
    guide = install_guide(engine_name, system)
    if _engine_installed(system, engine_name):
        typer.echo("  The engine appears installed but the service is stopped.", err=True)
        typer.echo("  Start it with:", err=True)
        for cmd in guide.start_commands:
            typer.echo(f"    {cmd}", err=True)
    else:
        typer.echo("  The engine does not appear to be installed.", err=True)
        typer.echo("  Install it with:", err=True)
        for cmd in guide.install_commands:
            typer.echo(f"    {cmd}", err=True)


def _offer_docker(
    engine_name: str,
    host: str,
    port: int,
    user: str,
    password: str,
    system: SystemInfo,
) -> bool:
    """Offer to start a Docker container for the engine when Docker is running."""
    if not system.docker_running:
        return False
    typer.echo("", err=True)
    if confirm("Start a Docker container for this engine?") and _try_start_docker(
        engine_name, host, port, user, password
    ):
        typer.echo(f"  \u2713 {get_engine(engine_name).name} container started.", err=True)
        return True
    return False


def _ensure_engine_ready(engine_name: str, host: str, port: int, user: str, password: str) -> bool:
    """Ensure the engine is installed and reachable; guide the user if not."""
    engine = get_engine(engine_name)
    system = detect_system()

    if not engine.is_available():
        pkg = "psycopg[binary]" if engine_name == "postgres" else "pymysql"
        typer.echo(f"Error: {engine.name} driver is not installed.", err=True)
        typer.echo(f"  \u2192 Install the driver: pip install {pkg}", err=True)
        typer.echo("", err=True)
        _offer_missing_engine(engine_name, system)
        if _offer_docker(engine_name, host, port, user, password, system):
            typer.echo(
                f"  The {engine.name} container is reachable, but the Python driver must "
                "be installed before the database can be created.",
                err=True,
            )
        return False

    result = engine.connect(host=host, port=port, user=user, password=password)
    if result.success:
        return True

    typer.echo(f"Error: {engine.name} server is not reachable.", err=True)
    typer.echo(f"  {result.message}", err=True)
    typer.echo("", err=True)
    _offer_missing_engine(engine_name, system)
    return _offer_docker(engine_name, host, port, user, password, system)


def create(
    engine: str = typer.Argument(None, help="Database engine: 'postgres' or 'mysql'."),
    name: str = typer.Option(None, "--name", "-n", help="Database name."),
    user: str = typer.Option(None, "--user", "-u", help="Application user to create."),
    host: str = typer.Option("localhost", "--host", help="Database host."),
    port: int = typer.Option(None, "--port", help="Database port."),
    admin_user: str = typer.Option(None, "--admin-user", help="Administrative user."),
    interactive: bool = typer.Option(
        True, "--interactive/--no-interactive", help="Run the interactive wizard."
    ),
) -> None:
    """Create a new database, user, and permissions using the specified engine."""
    if engine is None:
        if not interactive:
            typer.echo("Error: engine argument is required in non-interactive mode.", err=True)
            raise typer.Exit(code=1)
        engine = _prompt_engine()

    if engine not in VALID_ENGINES:
        typer.echo(
            f"Error: unknown engine '{engine}'. Choose from: {', '.join(VALID_ENGINES)}", err=True
        )
        raise typer.Exit(code=1)

    engine_instance = get_engine(engine)
    effective_port = port or engine_instance.default_port

    password = os.environ.get("YOUCADB_PASSWORD", "")
    admin_password = os.environ.get("YOUCADB_ADMIN_PASSWORD", "")

    cfg = config_model.load_config(".")
    project_name = name or (cfg.database.name if cfg else "") or "myproject"

    if interactive:
        typer.echo(f"Database engine: {engine_instance.name}")
        if name is None:
            project_name = text_input("Database name", default=project_name)
        if user is None:
            default_user = "postgres" if engine == "postgres" else "root"
            user = text_input("Username", default=default_user)
        if not password:
            password = password_input("Password")
        if port is None:
            port_str = text_input("Port", default=str(engine_instance.default_port))
            effective_port = int(port_str) if port_str.isdigit() else engine_instance.default_port
        admin_user = admin_user or ("postgres" if engine == "postgres" else "root")
        if not admin_password:
            admin_password = password_input(f"Admin password ({admin_user})")
    else:
        project_name = name or project_name
        user = user or ("postgres" if engine == "postgres" else "root")
        admin_user = admin_user or ("postgres" if engine == "postgres" else "root")
        if not password or not admin_password:
            typer.echo(
                "Warning: password(s) missing in non-interactive mode. Set the "
                "YOUCADB_PASSWORD and YOUCADB_ADMIN_PASSWORD environment variables instead of "
                "passing secrets on the command line.",
                err=True,
            )

    effective_port = effective_port or engine_instance.default_port
    typer.echo(f"Creating {engine_instance.name} database...")

    if not _ensure_engine_ready(engine, host, effective_port, admin_user, admin_password):
        raise typer.Exit(code=1)

    db_result = engine_instance.create_database(
        project_name, host=host, port=effective_port, user=admin_user, password=admin_password
    )
    if not db_result.success:
        typer.echo(f"Error: {db_result.message}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"  \u2713 {db_result.message}")

    user_result = engine_instance.create_user(
        user,
        password,
        host=host,
        database=project_name,
        admin_user=admin_user,
        admin_password=admin_password,
        port=effective_port,
    )
    if user_result.success:
        typer.echo(f"  \u2713 {user_result.message}")
    else:
        typer.echo(f"  \u26a0\ufe0f  {user_result.message}", err=True)

    test = engine_instance.test_connection(
        host=host, port=effective_port, user=user, password=password, database=project_name
    )
    if test.success:
        typer.echo("  \u2713 Connection test successful")
    else:
        typer.echo(f"  \u26a0\ufe0f  Connection test failed: {test.message}", err=True)

    typer.echo(f"Database '{project_name}' created successfully.")

    if cfg is not None:
        cfg.database.engine = engine
        cfg.database.host = host
        cfg.database.port = effective_port
        cfg.database.name = project_name
        cfg.database.user = user
        cfg.database.password = password
        if not interactive or confirm("Update .youcadb.toml with these settings?", default=True):
            config_model.save_config(cfg, ".")
            typer.echo("Configuration updated.")
