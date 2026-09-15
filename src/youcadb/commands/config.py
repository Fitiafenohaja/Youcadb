"""``youcadb config`` — manage youcadb configuration."""

from __future__ import annotations

from pathlib import Path

import typer

from youcadb import config as config_model
from youcadb.engines import get_engine
from youcadb.ui.menu import password_input, text_input


def _load_or_default(path: str) -> config_model.YoucaDBConfig:
    """Load config or build an empty one."""
    cfg = config_model.load_config(path)
    if cfg is not None:
        return cfg
    return config_model.YoucaDBConfig(project_name="myproject")


def _prompt_missing(cfg: config_model.YoucaDBConfig, interactive: bool) -> None:
    """Prompt for missing fields in interactive mode."""
    if not interactive:
        return
    db = cfg.database
    if not db.name:
        db.name = text_input("Database name", default=cfg.project_name or "myproject")
    if not db.user:
        default_user = "postgres" if db.engine == "postgres" else "root"
        db.user = text_input("Database user", default=default_user)
    if not db.password:
        db.password = password_input("Database password")
    if db.engine not in ("postgres", "mysql"):
        db.engine = "postgres"


def config_generate(
    path: str = typer.Option(".", "--path", help="Project directory."),
    output: str = typer.Option(".env", "--output", "-o", help="Output file."),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing file."),
    interactive: bool = typer.Option(
        True, "--interactive/--no-interactive", help="Prompt for missing values."
    ),
) -> None:
    """Generate a .env file with connection variables."""
    cfg = _load_or_default(path)
    _prompt_missing(cfg, interactive)

    output_path = Path(path) / output
    if output_path.exists() and not force:
        typer.echo(f"Error: {output} already exists. Use --force to overwrite.", err=True)
        raise typer.Exit(code=1)

    content = config_model.generate_env_content(cfg)
    try:
        output_path.write_text(content, encoding="utf-8")
    except OSError as exc:
        typer.echo(f"Error: could not write {output}: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Generated {output}")
    typer.echo(f"  DATABASE_URL={cfg.database.database_url}")


def config_show(
    path: str = typer.Option(".", "--path", help="Project directory."),
) -> None:
    """Display the current .youcadb.toml configuration."""
    config_path = Path(path) / config_model.CONFIG_FILE
    if not config_path.exists():
        typer.echo("Current configuration:")
        typer.echo(f"  (no {config_model.CONFIG_FILE} found — run 'youcadb init' first)")
        return

    typer.echo("Current configuration:")
    typer.echo(config_path.read_text(encoding="utf-8").rstrip())


def config(
    subcommand: str = typer.Argument("generate", help="Subcommand: 'generate' or 'show'."),
    path: str = typer.Option(".", "--path", help="Project directory."),
    output: str = typer.Option(".env", "--output", "-o", help="Output file for 'generate'."),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing file."),
    interactive: bool = typer.Option(
        True, "--interactive/--no-interactive", help="Prompt for missing values."
    ),
) -> None:
    """Manage youcadb configuration."""
    if subcommand == "generate":
        config_generate(path=path, output=output, force=force, interactive=interactive)
    elif subcommand == "show":
        config_show(path=path)
    else:
        typer.echo(f"Unknown config subcommand: '{subcommand}'", err=True)
        raise typer.Exit(code=1)


def get_engine_name(path: str) -> str:
    """Return the configured engine name or a default."""
    cfg = config_model.load_config(path)
    if cfg is None:
        return "postgres"
    get_engine(cfg.database.engine)
    return cfg.database.engine
