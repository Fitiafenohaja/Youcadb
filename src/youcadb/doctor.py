"""Diagnostics checks for ``youcadb doctor``."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from youcadb.detection.system import SystemInfo

from youcadb.engines import get_engine


@dataclass(frozen=True)
class CheckResult:
    """Result of a single diagnostic check."""

    name: str
    ok: bool
    message: str
    kind: str = "info"  # info | warning | error
    fix: str | None = None

    @property
    def icon(self) -> str:
        if self.kind == "error":
            return "\u2717"  # ✗
        if self.kind == "warning":
            return "\u26a0\ufe0f"  # ⚠
        return "\u2713"  # ✓


@dataclass
class DiagnosticReport:
    """Aggregate of diagnostic checks."""

    engine_name: str = ""
    checks: list[CheckResult] = field(default_factory=list)

    def add(self, check: CheckResult) -> None:
        """Add a check."""
        self.checks.append(check)

    @property
    def errors(self) -> int:
        return sum(1 for c in self.checks if c.kind == "error")

    @property
    def warnings(self) -> int:
        return sum(1 for c in self.checks if c.kind == "warning")

    @property
    def ok_count(self) -> int:
        return sum(1 for c in self.checks if c.kind == "info")

    @property
    def healthy(self) -> bool:
        return self.errors == 0 and self.warnings == 0


def check_engine_driver(engine_name: str) -> CheckResult:
    """Check if the engine driver is importable."""
    engine = get_engine(engine_name)
    if engine.is_available():
        return CheckResult(
            name=f"{engine.name} driver",
            ok=True,
            message="Driver available",
            kind="info",
        )
    return CheckResult(
        name=f"{engine.name} driver",
        ok=False,
        message="Driver not installed",
        kind="error",
        fix=f"pip install {'psycopg[binary]' if engine_name == 'postgres' else 'pymysql'}",
    )


def check_system_engine(engine_name: str, system: SystemInfo) -> CheckResult:
    """Check if the DB engine is installed on the system."""
    from youcadb.system.install import install_guide

    if engine_name == "postgres":
        if system.psql_available:
            return CheckResult(
                name="PostgreSQL installed",
                ok=True,
                message="psql binary found",
                kind="info",
            )
        if system.pg_service_available:
            return CheckResult(
                name="PostgreSQL installed",
                ok=True,
                message="Service detected",
                kind="info",
            )
    else:
        if system.mysql_client_available:
            return CheckResult(
                name="MySQL installed",
                ok=True,
                message="mysql client found",
                kind="info",
            )
        if system.mysql_service_available:
            return CheckResult(
                name="MySQL installed",
                ok=True,
                message="Service detected",
                kind="info",
            )

    guide = install_guide(engine_name, system)
    if system.docker_running:
        return CheckResult(
            name=f"{engine_name.capitalize()} installed",
            ok=True,
            message="Not installed natively, but Docker is running",
            kind="info",
            fix="Run 'youcadb create <engine>' to start a container.",
        )
    return CheckResult(
        name=f"{engine_name.capitalize()} installed",
        ok=False,
        message=f"{engine_name.capitalize()} engine not found on the system",
        kind="error",
        fix="\n".join(guide.install_commands),
    )


def check_service_running(
    engine_name: str, system: SystemInfo, user: str = "", password: str = ""
) -> CheckResult:
    """Check if the DB service is running."""
    from youcadb.system.install import install_guide

    guide = install_guide(engine_name, system)

    if engine_name == "postgres" and system.pg_service_available and not system.psql_available:
        return CheckResult(
            name="PostgreSQL service",
            ok=True,
            message="Service active",
            kind="info",
        )
    if (
        engine_name == "mysql"
        and system.mysql_service_available
        and not system.mysql_client_available
    ):
        return CheckResult(
            name="MySQL service",
            ok=True,
            message="Service active",
            kind="info",
        )

    # Attempt real connection to decide running vs installed-but-stopped.
    engine = get_engine(engine_name)
    effective_user = user or ("postgres" if engine_name == "postgres" else "root")
    result = engine.connect(host="localhost", user=effective_user, password=password)

    if result.success:
        return CheckResult(
            name=f"{engine.name} server",
            ok=True,
            message=result.message,
            kind="info",
        )

    # Distinguish "installed but stopped" vs "cannot auth" vs "server down".
    if "not installed" in result.message:
        kind = "error"
        fix_text = "\n".join(guide.install_commands)
        message = f"{engine.name} driver not installed"
    elif (
        "password authentication failed" in result.message.lower()
        or "access denied" in result.message.lower()
    ):
        kind = "warning"
        fix_text = "Check the admin credentials or the .youcadb.toml configuration."
        message = f"{engine.name} reachable but authentication failed"
    else:
        kind = "error"
        fix_text = "\n".join(guide.start_commands)
        message = result.message

    return CheckResult(
        name=f"{engine.name} server",
        ok=kind == "info",
        message=message,
        kind=kind,
        fix=fix_text,
    )


def check_database(
    engine_name: str, database: str, host: str, port: int, user: str, password: str
) -> CheckResult:
    """Check the configured database is reachable and authenticates."""
    engine = get_engine(engine_name)
    if port <= 0:
        port = engine.default_port

    result = engine.connect(host=host, port=port, user=user, password=password, database=database)

    if result.success:
        return CheckResult(
            name="Database connection",
            ok=True,
            message=result.message,
            kind="info",
        )
    return CheckResult(
        name="Database connection",
        ok=False,
        message=result.message,
        kind="error",
        fix="Run 'youcadb create <engine>' to create the database, or check credentials.",
    )


def check_config_vars(
    database_url_present: bool, engine_name: str, url_scheme: str | None
) -> CheckResult:
    """Check env variables coherence."""
    expected_scheme = "postgresql" if engine_name == "postgres" else "mysql"
    if not database_url_present:
        return CheckResult(
            name="DATABASE_URL",
            ok=False,
            message="DATABASE_URL not detected in .env",
            kind="warning",
            fix="Run 'youcadb config generate' to create a .env file.",
        )
    if url_scheme is not None and url_scheme != expected_scheme:
        return CheckResult(
            name="DATABASE_URL",
            ok=False,
            message=f"DATABASE_URL uses '{url_scheme}://' but engine is {engine_name}",
            kind="error",
            fix=f"Expected '{expected_scheme}://' scheme.",
        )
    return CheckResult(
        name="DATABASE_URL",
        ok=True,
        message="DATABASE_URL detected and coherent",
        kind="info",
    )


def check_security(exposed_on_0_0_0_0: bool, password_tracked_in_git: bool) -> list[CheckResult]:
    """Return security checks."""
    checks: list[CheckResult] = []
    if exposed_on_0_0_0_0:
        checks.append(
            CheckResult(
                name="Security",
                ok=False,
                message="Database exposed on 0.0.0.0",
                kind="warning",
                fix="Restrict bind-address to 127.0.0.1 in the database config.",
            )
        )
    else:
        checks.append(
            CheckResult(
                name="Security",
                ok=True,
                message="No 0.0.0.0 exposure detected",
                kind="info",
            )
        )
    if password_tracked_in_git:
        checks.append(
            CheckResult(
                name="Security",
                ok=False,
                message="Password committed to git",
                kind="warning",
                fix="Remove the file from git: 'git rm --cached .env' and add it to .gitignore.",
            )
        )
    else:
        checks.append(
            CheckResult(
                name="Security",
                ok=True,
                message="No password tracked in git",
                kind="info",
            )
        )
    return checks


def run_diagnostics(
    engine_name: str,
    system: SystemInfo,
    database: str,
    host: str,
    port: int,
    user: str,
    password: str,
    database_url_present: bool,
    url_scheme: str | None,
    exposed_on_0_0_0_0: bool,
    password_tracked_in_git: bool,
) -> DiagnosticReport:
    """Run the full diagnostic suite and return a report."""
    report = DiagnosticReport(engine_name=engine_name)

    report.add(check_engine_driver(engine_name))
    report.add(check_system_engine(engine_name, system))
    report.add(check_service_running(engine_name, system, user=user, password=password))
    report.add(check_database(engine_name, database, host, port, user, password))
    report.add(check_config_vars(database_url_present, engine_name, url_scheme))
    for check in check_security(exposed_on_0_0_0_0, password_tracked_in_git):
        report.add(check)

    return report
