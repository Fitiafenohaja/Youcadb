"""CLI entry point — defines commands and dispatches to implementations."""

from __future__ import annotations

import typer

from youcadb import __version__
from youcadb.commands import config as config_cmd
from youcadb.commands import create as create_cmd
from youcadb.commands import doctor as doctor_cmd
from youcadb.commands import init as init_cmd
from youcadb.commands import status as status_cmd

app = typer.Typer(
    name="youcadb",
    help="Database diagnostics and configuration CLI for developers.",
    add_completion=False,
    no_args_is_help=False,
    invoke_without_command=True,
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit."),
) -> None:
    """YoucaDB — Database diagnostics & configuration for developers."""
    if version:
        typer.echo(f"youcadb {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        typer.echo(f"YoucaDB v{__version__} — Database diagnostics & configuration")
        typer.echo("Run 'youcadb --help' to see available commands.")


app.command()(init_cmd.init)
app.command()(create_cmd.create)
app.command()(status_cmd.status)
app.command()(doctor_cmd.doctor)
app.command(name="config")(config_cmd.config)


def run() -> None:
    """Console-script entry point."""
    app()


main = run  # alias so the console script and tests stay tidy


if __name__ == "__main__":
    run()
