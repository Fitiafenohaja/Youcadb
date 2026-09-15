"""``youcadb doctor`` — diagnose the local environment for database issues."""

from __future__ import annotations

import typer

from youcadb import config as config_model
from youcadb.detection.project import read_env_file
from youcadb.detection.system import detect_system
from youcadb.doctor import DiagnosticReport, run_diagnostics
from youcadb.engines import get_engine
from youcadb.ui.menu import select_menu


def _print_report(report: DiagnosticReport) -> None:
    """Pretty-print a diagnostic report grouped by category."""
    typer.echo("DATABASE DOCTOR")
    typer.echo("\u2500" * 28)
    typer.echo(f"Engine: {report.engine_name}")
    typer.echo("")

    current_section = ""
    for check in report.checks:
        section = check.name.split(" ")[0]
        if section not in current_section:
            current_section = section
        typer.echo(f"  {check.icon} {check.name}: {check.message}")
        if check.fix and check.kind != "info":
            for fix_line in check.fix.splitlines():
                typer.echo(f"      \u2192 {fix_line}")

    typer.echo("")
    if report.healthy:
        typer.echo("Overall: healthy")
    else:
        typer.echo(f"Overall: {report.warnings} warning(s), {report.errors} error(s)")

    if report.errors:
        raise typer.Exit(code=1)


def doctor(
    engine: str = typer.Option(None, "--engine", "-e", help="Force a database engine."),
    path: str = typer.Option(".", "--path", help="Project directory to inspect."),
) -> None:
    """Run diagnostics and report potential issues."""
    cfg = config_model.load_config(path)
    engine_name = engine or (cfg.database.engine if cfg else None)

    if engine_name is None:
        engine_name = select_menu(
            "No configuration found. Which engine should be diagnosed?",
            ["postgres", "mysql"],
        )
        engine_name = engine_name or "postgres"

    if engine_name not in ("postgres", "mysql"):
        typer.echo(f"Error: unknown engine '{engine_name}'.", err=True)
        raise typer.Exit(code=1)

    engine_instance = get_engine(engine_name)
    system = detect_system()

    host = cfg.database.host if cfg else "localhost"
    port = cfg.database.port if cfg else engine_instance.default_port
    database = cfg.database.name if cfg else ""
    user = cfg.database.user if cfg else ""
    password = cfg.database.password if cfg else ""

    env_vars = read_env_file(path)

    git_warnings = config_model.detect_env_password_in_git(path)
    bind_warnings = config_model.check_bind_address(path)

    report = run_diagnostics(
        engine_name=engine_name,
        system=system,
        database=database,
        host=host,
        port=port,
        user=user,
        password=password,
        env=env_vars,
        exposed_on_0_0_0_0=bool(bind_warnings),
        password_tracked_in_git=bool(git_warnings),
    )
    report.engine_name = engine_instance.name

    _print_report(report)
