"""``youcadb status`` — show status of detected databases and connections."""

from __future__ import annotations

import typer


def status() -> None:
    """Display current database status and connection information."""
    # TODO: detect running DB instances, check connectivity
    typer.echo("Database Status")
    typer.echo("=" * 40)
    typer.echo("  PostgreSQL: not detected (stub)")
    typer.echo("  MySQL:      not detected (stub)")
    typer.echo("")
    typer.echo("Run 'youcadb doctor' for a detailed diagnostics report.")
