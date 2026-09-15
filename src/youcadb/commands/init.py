"""``youcadb init`` — initialise a youcadb project in the current directory."""

from __future__ import annotations

import typer


def init(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing configuration."),
) -> None:
    """Initialise youcadb configuration in the current directory."""
    # TODO: detect project context, write .youcadb.toml
    typer.echo("Initializing youcadb project configuration...")
    if force:
        typer.echo("(forced mode — existing config will be overwritten)")
    typer.echo("Done. Configuration written to .youcadb.toml")
