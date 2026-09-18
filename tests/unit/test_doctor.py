"""Tests for the diagnostics module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from youcadb.detection.system import SystemInfo
from youcadb.doctor import (
    CheckResult,
    DiagnosticReport,
    check_config_vars,
    check_engine_driver,
    check_mysql_auth_plugin,
    check_security,
    check_service_running,
    run_diagnostics,
)


def test_check_result_properties() -> None:
    info = CheckResult(name="x", ok=True, message="ok")
    assert info.icon == "\u2713"
    warn = CheckResult(name="x", ok=False, message="w", kind="warning")
    assert warn.icon == "\u26a0\ufe0f"
    err = CheckResult(name="x", ok=False, message="e", kind="error")
    assert err.icon == "\u2717"


def test_diagnostic_report_totals() -> None:
    report = DiagnosticReport(engine_name="postgres")
    report.add(CheckResult(name="a", ok=True, message="ok"))
    report.add(CheckResult(name="b", ok=False, message="w", kind="warning"))
    report.add(CheckResult(name="c", ok=False, message="e", kind="error"))
    assert report.errors == 1
    assert report.warnings == 1
    assert report.ok_count == 1
    assert report.healthy is False


def test_diagnostic_report_healthy() -> None:
    report = DiagnosticReport(engine_name="postgres")
    report.add(CheckResult(name="a", ok=True, message="ok"))
    assert report.healthy is True


def test_check_engine_driver_available() -> None:
    mock_engine = MagicMock()
    mock_engine.is_available.return_value = True
    mock_engine.name = "PostgreSQL"
    with patch("youcadb.doctor.get_engine", return_value=mock_engine):
        result = check_engine_driver("postgres")
    assert result.ok is True
    assert result.kind == "info"


def test_check_engine_driver_missing() -> None:
    mock_engine = MagicMock()
    mock_engine.is_available.return_value = False
    mock_engine.name = "PostgreSQL"
    with patch("youcadb.doctor.get_engine", return_value=mock_engine):
        result = check_engine_driver("postgres")
    assert result.ok is False
    assert result.kind == "error"
    assert "pip install" in (result.fix or "")


def test_check_config_vars_present() -> None:
    checks = check_config_vars("mysql", {"DATABASE_URL": "mysql://u:p@localhost:3306/db"})
    assert checks
    assert all(c.ok for c in checks)


def test_check_config_vars_scheme_mismatch() -> None:
    checks = check_config_vars("postgres", {"DATABASE_URL": "mysql://u:p@localhost:3306/db"})
    assert any(not c.ok and c.kind == "error" for c in checks)


def test_check_config_vars_missing() -> None:
    checks = check_config_vars("postgres", {})
    assert any(not c.ok and c.kind == "warning" and "DATABASE_URL" in c.name for c in checks)
    assert any(not c.ok and c.name == "DB_PORT" for c in checks)


def test_check_config_vars_contradiction() -> None:
    checks = check_config_vars(
        "postgres",
        {
            "DATABASE_URL": "postgresql://bob:pw@dbhost:5432/prod",
            "DB_HOST": "otherhost",
            "DB_PORT": "3306",
        },
    )
    assert any(not c.ok and c.kind == "error" and "DB_HOST" in c.name for c in checks)
    assert any(not c.ok and c.kind == "error" and "DB_PORT" in c.name for c in checks)


def test_check_mysql_auth_plugin_skipped_for_postgres() -> None:
    assert check_mysql_auth_plugin("postgres", "postgres", "localhost", 5432, "") == []


def test_check_mysql_auth_plugin_missing_driver() -> None:
    with patch.dict("sys.modules", {"pymysql": None}):
        assert check_mysql_auth_plugin("mysql", "root", "localhost", 3306, "") == []


def test_check_mysql_auth_plugin_warns_sha2() -> None:
    fake_pymysql = MagicMock()
    conn = MagicMock()
    cur = conn.cursor.return_value
    cur.__enter__.return_value = cur
    cur.fetchone.return_value = ("caching_sha2_password",)
    fake_pymysql.connect.return_value = conn
    with patch.dict("sys.modules", {"pymysql": fake_pymysql}):
        checks = check_mysql_auth_plugin("mysql", "root", "localhost", 3306, "pw")
    assert len(checks) == 1
    assert checks[0].kind == "warning"
    assert "caching_sha2_password" in checks[0].message


def test_check_security_clean() -> None:
    checks = check_security(False, False)
    assert all(c.ok for c in checks)


def test_check_security_exposed() -> None:
    checks = check_security(True, True)
    assert any(not c.ok and c.kind == "warning" and "0.0.0.0" in c.message for c in checks)
    assert any(not c.ok and c.kind == "warning" and "git" in c.message for c in checks)


def test_no_imports_raise() -> None:
    """check_engine_driver catches ImportError gracefully for missing drivers."""
    with patch("youcadb.doctor.get_engine") as mock_get:
        mock_engine = MagicMock()
        mock_engine.is_available.return_value = False
        mock_engine.name = "MySQL"
        mock_get.return_value = mock_engine
        result = check_engine_driver("mysql")
    assert result.ok is False


def test_check_service_running_unreachable() -> None:
    fake_system = SystemInfo(os_name="linux", python_version="3.12")
    mock_engine = MagicMock()
    mock_engine.name = "PostgreSQL"
    mock_engine.default_port = 5432
    mock_engine.connect.return_value = MagicMock(
        success=False, message="connection refused", server_version=None
    )
    with (
        patch("youcadb.doctor.get_engine", return_value=mock_engine),
        patch("youcadb.system.install.install_guide") as mock_guide,
    ):
        from youcadb.system.install import InstallGuide

        mock_guide.return_value = InstallGuide(
            engine="postgres",
            install_commands=["sudo apt install postgresql"],
            start_commands=["sudo systemctl start postgresql"],
            docker_command="docker run ...",
        )
        result = check_service_running("postgres", fake_system)
    assert result.ok is False
    assert result.kind == "error"


def test_check_service_running_denied_access_is_warning() -> None:
    fake_system = SystemInfo(os_name="linux", python_version="3.12")
    mock_engine = MagicMock()
    mock_engine.name = "PostgreSQL"
    mock_engine.default_port = 5432
    mock_engine.connect.return_value = MagicMock(
        success=False,
        message='Connection failed: permission denied for database "postgres"',
        server_version=None,
    )
    with patch("youcadb.doctor.get_engine", return_value=mock_engine):
        result = check_service_running(
            "postgres", fake_system, user="app_user", password="pw", database="appdb"
        )
    assert result.ok is False
    assert result.kind == "warning"
    assert "denied access" in result.message

    mock_engine.connect.assert_called_with(
        host="localhost", port=5432, user="app_user", password="pw", database="appdb"
    )


def test_run_diagnostics_passes_engine_name() -> None:
    fake_system = SystemInfo(os_name="linux", python_version="3.12", psql_available=True)
    fake_conn = MagicMock(success=True, message="ok", server_version="16")
    mock_engine = MagicMock()
    mock_engine.name = "PostgreSQL"
    mock_engine.is_available.return_value = True
    mock_engine.connect.return_value = fake_conn
    with patch("youcadb.doctor.get_engine", return_value=mock_engine):
        report = run_diagnostics(
            engine_name="postgres",
            system=fake_system,
            database="testdb",
            host="localhost",
            port=5432,
            user="postgres",
            password="",
            env={"DATABASE_URL": "postgresql://postgres@localhost:5432/testdb"},
            exposed_on_0_0_0_0=False,
            password_tracked_in_git=False,
        )
    assert isinstance(report, DiagnosticReport)
    assert len(report.checks) >= 5
    assert report.errors == 0
