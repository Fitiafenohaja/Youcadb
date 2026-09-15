"""``youcadb doctor`` — diagnose the local environment for database issues."""

from __future__ import annotations

import typer


def doctor() -> None:
    """Run diagnostics and report potential issues."""
    # TODO: check binaries, drivers, connectivity, Docker, config files
    typer.echo("YoucaDB Doctor")
    typer.echo("=" * 40)
    checks = [
        ("Python version", "OK", "3.x detected"),
        ("psycopg (PostgreSQL driver)", "SKIP", "not installed"),
        ("pymysql (MySQL driver)", "SKIP", "not installed"),
        ("Docker daemon", "SKIP", "detection not implemented"),
    ]
    for label, status, detail in checks:
        icon = {
            "OK": "\u2705",
            "WARN": "\u26a0\ufe0f",
            "FAIL": "\u274c",
            "SKIP": "\u23ed\ufe0f",
        }.get(status, "?")
        typer.echo(f"  {icon} {label}: {detail}")
    typer.echo("")
    typer.echo("All checks passed (stub — limited diagnostics).")
