"""Tests for the CLI entry point."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from youcadb.cli import app

runner = CliRunner()


def test_cli_no_args_no_config(tmp_path, monkeypatch) -> None:
    """Running without args and no config shows the init hint."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "Lancez" in result.stdout or "YoucaDB" in result.stdout


def test_cli_no_args_with_config(tmp_path, monkeypatch) -> None:
    """Running without args with a config shows status."""
    from youcadb.config import DBConfig, YoucaDBConfig, save_config

    cfg = YoucaDBConfig(project_name="test", database=DBConfig(engine="postgres", name="testdb"))
    save_config(cfg, str(tmp_path))
    monkeypatch.chdir(tmp_path)

    with patch("youcadb.engines.postgres.PostgresEngine.is_available", return_value=False):
        result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "Database" in result.stdout


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


def test_cli_version_short_flag() -> None:
    """-v should also work for version."""
    result = runner.invoke(app, ["-v"])
    assert result.exit_code == 0
    assert "youcadb" in result.stdout
