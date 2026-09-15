"""CLI entry point — defines commands and dispatches to implementations."""

from __future__ import annotations

from pathlib import Path

import typer

from youcadb import __version__
from youcadb import config as config_model
from youcadb.commands import config as config_cmd
from youcadb.commands import create as create_cmd
from youcadb.commands import doctor as doctor_cmd
from youcadb.commands import init as init_cmd
from youcadb.commands import status as status_cmd

app = typer.Typer(
    name="youcadb",
    help="Database diagnostics and configuration CLI for developers.",
    add_completion=False,
    no_args_is_help=False,
    invoke_without_command=True,
)

CONFIG_FILE = config_model.CONFIG_FILE


def _render_no_config() -> None:
    """Print guidance when no configuration is present."""
    typer.echo("")
    typer.echo("Aucune base de données configurée pour ce projet.")
    typer.echo("")
    typer.echo("→ Lancez `youcadb init` pour détecter votre stack")
    typer.echo("  et démarrer la configuration.")


def _render_configured() -> None:
    """Analyse the current project and print a short health summary."""
    cfg = config_model.load_config(".")
    if cfg is None:
        _render_no_config()
        return

    from youcadb.engines import get_engine

    engine = get_engine(cfg.database.engine)
    db = cfg.database

    typer.echo("")
    typer.echo(f"Database: {db.name or '(unnamed)'} ({engine.name})")
    typer.echo("")

    if not engine.is_available():
        typer.echo(f"✗ {engine.name} driver not installed")
        typer.echo("")
        typer.echo("Status: UNHEALTHY")
        typer.echo("")
        typer.echo("→ `youcadb doctor` pour un diagnostic détaillé")
        return

    admin_user = db.user or ("postgres" if db.engine == "postgres" else "root")
    server = engine.connect(host=db.host, port=db.port, user=admin_user, password=db.password)
    if not server.success:
        typer.echo(f"✗ Server unreachable on port {db.port}")
        typer.echo("")
        typer.echo("Status: UNHEALTHY")
        typer.echo("")
        typer.echo("→ `youcadb doctor` pour un diagnostic détaillé et des pistes de correction")
        return

    typer.echo("✓ Server running")
    if db.name:
        conn = engine.connect(
            host=db.host, port=db.port, user=db.user, password=db.password, database=db.name
        )
        if conn.success:
            typer.echo("✓ Database reachable")
            typer.echo("✓ Authentication successful")
            typer.echo("")
            typer.echo("Status: HEALTHY")
        else:
            typer.echo("✗ Database unreachable")
            typer.echo("")
            typer.echo("Status: UNHEALTHY")
    else:
        typer.echo("Status: HEALTHY")

    typer.echo("")
    typer.echo("→ `youcadb doctor` pour un diagnostic complet")


@app.callback(invoke_without_command=True)
def _main_callback(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit."),
) -> None:
    """YoucaDB — Database diagnostics & configuration for developers."""
    if version:
        typer.echo(f"youcadb {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        if Path(CONFIG_FILE).exists() or _has_project_files():
            _render_configured()
        else:
            _render_no_config()


def _has_project_files() -> bool:
    """Return True if the directory looks like a project."""
    markers = (
        "pyproject.toml",
        "package.json",
        "requirements.txt",
        "docker-compose.yml",
        "Dockerfile",
    )
    return any(Path(m).exists() for m in markers)


app.command()(init_cmd.init)
app.command()(create_cmd.create)
app.command()(status_cmd.status)
app.command()(doctor_cmd.doctor)
app.command(name="config")(config_cmd.config)


def main() -> None:
    """Console-script entry point."""
    app()


if __name__ == "__main__":
    main()
