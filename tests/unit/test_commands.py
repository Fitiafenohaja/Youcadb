"""Tests for CLI commands."""

from __future__ import annotations

from typer.testing import CliRunner

from youcadb.cli import app

runner = CliRunner()


def test_init_success() -> None:
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert "Init" in result.stdout


def test_init_force_flag() -> None:
    result = runner.invoke(app, ["init", "--force"])
    assert result.exit_code == 0
    assert "forced mode" in result.stdout


def test_create_postgres() -> None:
    result = runner.invoke(app, ["create", "postgres"])
    assert result.exit_code == 0
    assert "postgres" in result.stdout.lower()


def test_create_mysql_with_name() -> None:
    result = runner.invoke(app, ["create", "mysql", "--name", "mydb"])
    assert result.exit_code == 0
    assert "mydb" in result.stdout


def test_create_invalid_engine() -> None:
    result = runner.invoke(app, ["create", "oracle"])
    assert result.exit_code == 1
    assert "unknown engine" in result.stderr


def test_status() -> None:
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "Status" in result.stdout


def test_doctor() -> None:
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Doctor" in result.stdout


def test_config_generate() -> None:
    result = runner.invoke(app, ["config", "generate"])
    assert result.exit_code == 0
    assert "Generating" in result.stdout


def test_config_show() -> None:
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "configuration" in result.stdout.lower()


def test_config_invalid_subcommand() -> None:
    result = runner.invoke(app, ["config", "foo"])
    assert result.exit_code == 1
    assert "Unknown config subcommand" in result.stderr
