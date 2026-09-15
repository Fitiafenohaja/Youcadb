"""``youcadb config`` — manage youcadb configuration."""

from __future__ import annotations

import typer


def config(
    subcommand: str = typer.Argument("generate", help="Subcommand: 'generate' or 'show'."),
) -> None:
    """Manage youcadb configuration."""
    if subcommand == "generate":
        typer.echo("Generating default configuration...")
        # TODO: generate .youcadb.toml with sensible defaults
        typer.echo("Configuration generated (stub).")
    elif subcommand == "show":
        typer.echo("Current configuration:")
        # TODO: read and display .youcadb.toml
        typer.echo("  (no configuration found — run 'youcadb init' first)")
    else:
        typer.echo(f"Unknown config subcommand: '{subcommand}'", err=True)
        raise typer.Exit(code=1)
