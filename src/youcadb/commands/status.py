"""``youcadb status`` — show status of detected databases and connections."""

from __future__ import annotations

import typer

from youcadb import config as config_model
from youcadb.engines import get_engine
from youcadb.ui.menu import select_menu


def _print_status(
    database: str,
    engine_name: str,
    host: str,
    port: int,
    engine_available: bool,
    server_ok: bool,
    server_message: str,
    db_ok: bool,
    db_message: str,
) -> bool:
    """Print a status block and return overall health."""
    engine_instance = get_engine(engine_name)
    typer.echo("YoucaDB STATUS")
    typer.echo("")
    typer.echo(f"Database: {database or '(not configured)'}")
    typer.echo(f"Engine: {engine_instance.name}")
    typer.echo(f"Host: {host}")
    typer.echo(f"Port: {port}")
    typer.echo("")

    if engine_available:
        typer.echo(f"  \u2713 {engine_instance.name} available")
    else:
        typer.echo(f"  \u2717 {engine_instance.name} driver not available")

    if server_ok:
        typer.echo("  \u2713 Server running")
    else:
        typer.echo(f"  \u2717 Server unreachable — {server_message}")

    if db_ok:
        typer.echo("  \u2713 Database reachable")
        typer.echo("  \u2713 Authentication successful")
    else:
        typer.echo(f"  \u2717 {db_message}")

    typer.echo("")
    healthy = engine_available and server_ok and db_ok
    typer.echo(f"Status: {'HEALTHY' if healthy else 'UNHEALTHY'}")
    return healthy


def status(
    engine: str = typer.Option(None, "--engine", "-e", help="Force a database engine."),
    path: str = typer.Option(".", "--path", help="Project directory to inspect."),
) -> None:
    """Display current database status and connection information."""
    cfg = config_model.load_config(path)
    engine_name = engine or (cfg.database.engine if cfg else None)

    if engine_name is None:
        engine_name = select_menu(
            "No configuration found. Which engine should be checked?",
            ["postgres", "mysql"],
        )
        engine_name = engine_name or "postgres"
        typer.echo("Tip: run 'youcadb init' to persist this configuration.")
        typer.echo("")

    if engine_name not in ("postgres", "mysql"):
        typer.echo(f"Error: unknown engine '{engine_name}'.", err=True)
        raise typer.Exit(code=1)

    engine_instance = get_engine(engine_name)
    host = cfg.database.host if cfg else "localhost"
    port = cfg.database.port if cfg else engine_instance.default_port
    database = cfg.database.name if cfg else ""
    user = cfg.database.user if cfg else ""
    password = cfg.database.password if cfg else ""

    engine_available = engine_instance.is_available()

    server_ok = False
    server_message = "engine not available"
    if engine_available:
        admin_user = user or ("postgres" if engine_name == "postgres" else "root")
        server_result = engine_instance.connect(
            host=host, port=port, user=admin_user, password=password
        )
        server_ok = server_result.success
        server_message = server_result.message

    db_ok = False
    db_message = "database not configured"
    if database:
        conn_result = engine_instance.connect(
            host=host, port=port, user=user, password=password, database=database
        )
        db_ok = conn_result.success
        db_message = conn_result.message
    else:
        db_message = "No database name configured. Run 'youcadb create'."

    _print_status(
        database=database,
        engine_name=engine_name,
        host=host,
        port=port,
        engine_available=engine_available,
        server_ok=server_ok,
        server_message=server_message,
        db_ok=db_ok,
        db_message=db_message,
    )

    typer.echo("")
    typer.echo("Run 'youcadb doctor' for a detailed diagnostics report.")
