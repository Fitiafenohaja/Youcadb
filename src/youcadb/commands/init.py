"""``youcadb init`` — initialise a youcadb project in the current directory."""

from __future__ import annotations

import typer

from youcadb import config as config_model
from youcadb.detection.project import detect_project
from youcadb.detection.system import detect_system
from youcadb.engines import get_engine
from youcadb.ui.menu import confirm, select_menu


def init(
    path: str = typer.Argument(".", help="Project directory to inspect."),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing configuration."),
    engine: str = typer.Option(None, "--engine", "-e", help="Force a database engine."),
    name: str = typer.Option(None, "--name", "-n", help="Project name."),
    interactive: bool = typer.Option(
        True, "--interactive/--no-interactive", help="Run in interactive mode."
    ),
) -> None:
    """Initialise youcadb configuration in the current directory."""
    typer.echo("YoucaDB Project Detection")
    typer.echo("=" * 40)

    system = detect_system()
    project = detect_project(path)

    for detail in project.details:
        typer.echo(f"  \u2713 {detail}")

    if not project.details:
        typer.echo("  No project files detected (pyproject.toml, package.json, etc.)")

    if system.docker_available:
        typer.echo("  \u2713 Docker detected")

    engine_hint = engine or project.engine_hint
    if engine_hint:
        typer.echo("")
        typer.echo(f"Recommended database: {engine_hint.capitalize()}")
    else:
        typer.echo("")
        typer.echo("Recommended database: not determined (no driver or conflicting drivers)")

    if engine_hint is None and interactive:
        engine_choice = select_menu(
            "Which database engine do you want to use?",
            ["postgres", "mysql"],
        )
        engine_hint = engine_choice or "postgres"
    elif engine_hint is None:
        typer.echo("  (defaulting to PostgreSQL in non-interactive mode)")
        engine_hint = "postgres"

    project_name = name or (project.language.lower() if project.language else "myproject")

    if (
        not force
        and config_model.load_config(path) is not None
        and interactive
        and not confirm(".youcadb.toml already exists. Overwrite?", default=True)
    ):
        raise typer.Exit(code=0)

    engine_instance = get_engine(engine_hint)

    env = project.env
    host = env.get("DB_HOST") or env.get("POSTGRES_HOST") or env.get("MYSQL_HOST") or "localhost"
    port_value = env.get("DB_PORT") or env.get("POSTGRES_PORT") or env.get("MYSQL_PORT")
    port = int(port_value) if port_value and port_value.isdigit() else engine_instance.default_port

    cfg = config_model.YoucaDBConfig(
        project_name=project_name,
        database=config_model.DBConfig(
            engine=engine_hint,
            host=host,
            port=port,
            name=env.get("DB_NAME", ""),
            user=env.get("DB_USER", ""),
            password=env.get("DB_PASSWORD", ""),
        ),
    )

    if env:
        typer.echo("(existing environment variables detected - values pre-filled)")

    if force:
        typer.echo("(forced mode — existing config will be overwritten)")

    config_model.save_config(cfg, path)
    typer.echo(f"Done. Configuration written to {config_model.CONFIG_FILE}")
