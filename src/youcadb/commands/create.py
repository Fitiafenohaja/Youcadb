"""``youcadb create`` — create a new database instance."""

from __future__ import annotations

import typer

from youcadb import config as config_model
from youcadb.detection.system import detect_system
from youcadb.engines import get_engine
from youcadb.system.install import install_guide
from youcadb.ui.menu import confirm, password_input, text_input

VALID_ENGINES = ("postgres", "mysql")


def _prompt_engine() -> str:
    from youcadb.ui.menu import select_menu

    choice = select_menu("Database engine?", ["postgres", "mysql"])
    return choice or "postgres"


def _ensure_engine_ready(engine_name: str, host: str, port: int, user: str, password: str) -> bool:
    """Ensure the engine is installed and reachable; guide the user if not."""
    engine = get_engine(engine_name)
    system = detect_system()

    if not engine.is_available():
        typer.echo(f"Error: {engine.name} driver is not installed.", err=True)
        pkg = "psycopg[binary]" if engine_name == "postgres" else "pymysql"
        typer.echo(f"  \u2192 Install the driver: pip install {pkg}", err=True)
        return False

    result = engine.connect(host=host, port=port, user=user, password=password)
    if result.success:
        return True

    guide = install_guide(engine_name, system)
    typer.echo(f"Error: {engine.name} server is not reachable.", err=True)
    typer.echo(f"  {result.message}", err=True)
    typer.echo("", err=True)
    if (
        system.psql_available
        or system.mysql_client_available
        or system.pg_service_available
        or system.mysql_service_available
    ):
        typer.echo("  The engine appears installed but the service is stopped.", err=True)
        typer.echo("  Start it with:", err=True)
        for cmd in guide.start_commands:
            typer.echo(f"    {cmd}", err=True)
    else:
        typer.echo("  The engine does not appear to be installed.", err=True)
        typer.echo("  Install it with:", err=True)
        for cmd in guide.install_commands:
            typer.echo(f"    {cmd}", err=True)

    if system.docker_running:
        typer.echo("", err=True)
        if confirm("Start a Docker container for this engine?"):
            typer.echo(f"  Run: {guide.docker_command}")

    return False


def create(
    engine: str = typer.Argument(None, help="Database engine: 'postgres' or 'mysql'."),
    name: str = typer.Option(None, "--name", "-n", help="Database name."),
    user: str = typer.Option(None, "--user", "-u", help="Application user to create."),
    password: str = typer.Option(
        None, "--password", "-p", help="Password for the application user.", hide_input=True
    ),
    host: str = typer.Option("localhost", "--host", help="Database host."),
    port: int = typer.Option(None, "--port", help="Database port."),
    admin_user: str = typer.Option(None, "--admin-user", help="Administrative user."),
    admin_password: str = typer.Option(
        None, "--admin-password", help="Administrative password.", hide_input=True
    ),
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

    cfg = config_model.load_config(".")
    project_name = name or (cfg.database.name if cfg else "") or "myproject"

    if interactive:
        typer.echo(f"Database engine: {engine_instance.name}")
        if name is None:
            project_name = text_input("Database name", default=project_name)
        if user is None:
            default_user = "postgres" if engine == "postgres" else "root"
            user = text_input("Username", default=default_user)
        if password is None:
            password = password_input("Password")
        if port is None:
            port_str = text_input("Port", default=str(engine_instance.default_port))
            effective_port = int(port_str) if port_str.isdigit() else engine_instance.default_port
        admin_user = admin_user or ("postgres" if engine == "postgres" else "root")
        if admin_password is None:
            admin_password = password_input(f"Admin password ({admin_user})")
    else:
        project_name = name or project_name
        user = user or ("postgres" if engine == "postgres" else "root")
        password = password or ""
        admin_user = admin_user or ("postgres" if engine == "postgres" else "root")
        admin_password = admin_password if admin_password is not None else ""

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
