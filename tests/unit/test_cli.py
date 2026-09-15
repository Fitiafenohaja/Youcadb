"""Tests for the CLI entry point."""

from __future__ import annotations

from typer.testing import CliRunner

from youcadb.cli import app

runner = CliRunner()


def test_cli_no_args_shows_banner() -> None:
    """Running without arguments should show the banner."""
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "YoucaDB" in result.stdout


def test_cli_help() -> None:
    """--help should list available commands."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.stdout.lower() or "database" in result.stdout.lower()


def test_version() -> None:
    """--version should print the version string."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "youcadb" in result.stdout
