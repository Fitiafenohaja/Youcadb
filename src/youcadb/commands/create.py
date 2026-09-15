"""``youcadb create`` — create a new database instance."""

from __future__ import annotations

from typing import Annotated

import typer


def create(
    engine: Annotated[str, typer.Argument(help="Database engine: 'postgres' or 'mysql'.")],
    name: Annotated[str | None, typer.Option("--name", "-n", help="Database name.")] = None,
) -> None:
    """Create a new database using the specified engine."""
    valid_engines = ("postgres", "mysql")
    if engine not in valid_engines:
        typer.echo(
            f"Error: unknown engine '{engine}'. Choose from: {', '.join(valid_engines)}", err=True
        )
        raise typer.Exit(code=1)
    # TODO: use engines.postgres or engines.mysql to create the database
    typer.echo(f"Creating {engine} database...")
    db_name = name or "my_database"
    typer.echo(f"Database '{db_name}' created successfully (stub).")
