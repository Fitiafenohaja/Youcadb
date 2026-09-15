"""Tests for engine implementations using mocked drivers.

These tests exercise the full success/error paths of each engine without
requiring a real database server.
"""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from youcadb.engines.mysql import MySQLEngine
from youcadb.engines.postgres import PostgresEngine


def _make_module(name: str, **attrs: object) -> ModuleType:
    mod = ModuleType(name)
    for key, value in attrs.items():
        setattr(mod, key, value)
    return mod


def _install_fake(module_name: str, fake: ModuleType) -> None:
    if module_name in sys.modules:
        sys.modules[f"_saved_{module_name}"] = sys.modules[module_name]
    sys.modules[module_name] = fake


def _restore_fake(module_name: str) -> None:
    saved = sys.modules.pop(f"_saved_{module_name}", None)
    if saved is not None:
        sys.modules[module_name] = saved
    else:
        sys.modules.pop(module_name, None)


@pytest.fixture
def fake_psycopg():
    fake = _make_module("psycopg")
    fake.connect = MagicMock()
    _install_fake("psycopg", fake)
    yield fake
    _restore_fake("psycopg")


@pytest.fixture
def fake_pymysql():
    fake = _make_module("pymysql")
    fake.connect = MagicMock()
    _install_fake("pymysql", fake)
    yield fake
    _restore_fake("pymysql")


def _ok_conn(version: str) -> MagicMock:
    conn = MagicMock()
    conn.info.server_version = version
    return conn


def _cur_of(conn: MagicMock) -> MagicMock:
    """Return the connector's cursor configured as a self-returning context manager."""
    cur = conn.cursor.return_value
    cur.__enter__.return_value = cur
    return cur


# ---------- PostgreSQL connect ----------


def test_pg_connect_success(fake_psycopg) -> None:
    conn = _ok_conn("160014")
    fake_psycopg.connect.return_value = conn
    result = PostgresEngine().connect(host="h", port=5432, user="u", password="p")
    assert result.success is True
    assert result.server_version == "160014"
    assert conn.close.called


def test_pg_connect_failure(fake_psycopg) -> None:
    fake_psycopg.connect.side_effect = RuntimeError("boom")
    result = PostgresEngine().connect()
    assert result.success is False
    assert "boom" in result.message


def test_pg_connect_without_driver() -> None:
    with patch.dict(sys.modules, {"psycopg": None}):
        result = PostgresEngine().connect()
    assert result.success is False
    assert "not installed" in result.message


def test_pg_connect_default_port(fake_psycopg) -> None:
    conn = _ok_conn("16")
    fake_psycopg.connect.return_value = conn
    PostgresEngine().connect()
    assert fake_psycopg.connect.call_args.kwargs["port"] == 5432


# ---------- PostgreSQL create/drop/user ----------


def test_pg_create_database_success(fake_psycopg) -> None:
    conn = MagicMock()
    cur = _cur_of(conn)
    cur.fetchone.return_value = None
    fake_psycopg.connect.return_value = conn
    result = PostgresEngine().create_database("appdb", host="h", password="pw")
    assert result.success is True
    statements = [str(c) for c in cur.execute.call_args_list]
    assert any("CREATE DATABASE" in s for s in statements)


def test_pg_create_database_idempotent(fake_psycopg) -> None:
    conn = MagicMock()
    cur = _cur_of(conn)
    cur.fetchone.return_value = (1,)  # database already exists
    fake_psycopg.connect.return_value = conn
    result = PostgresEngine().create_database("appdb", host="h", password="pw")
    assert result.success is True
    assert not any("CREATE DATABASE" in str(c) for c in cur.execute.call_args_list)


def test_pg_create_database_invalid_name(fake_psycopg) -> None:
    result = PostgresEngine().create_database('bad"; DROP TABLE x')
    assert result.success is False
    fake_psycopg.connect.assert_not_called()


def test_pg_drop_database_success(fake_psycopg) -> None:
    conn = MagicMock()
    fake_psycopg.connect.return_value = conn
    result = PostgresEngine().drop_database("appdb", host="h")
    assert result.success is True


def test_pg_create_user_creates(fake_psycopg) -> None:
    conn = MagicMock()
    cur = _cur_of(conn)
    cur.fetchone.return_value = None  # role does not exist
    fake_psycopg.connect.return_value = conn
    result = PostgresEngine().create_user("bob", "s3cret", host="h", database="appdb")
    assert result.success is True
    statements = [str(c) for c in cur.execute.call_args_list]
    assert any('CREATE ROLE "bob"' in s for s in statements)


def test_pg_create_user_escapes_password(fake_psycopg) -> None:
    conn = MagicMock()
    cur = _cur_of(conn)
    cur.fetchone.return_value = None
    fake_psycopg.connect.return_value = conn
    result = PostgresEngine().create_user("bob", "pa''ss", database="x")
    assert result.success is True
    statements = [c.args[0] for c in cur.execute.call_args_list if isinstance(c.args[0], str)]
    assert any("pa''''ss" in s for s in statements)


def test_pg_create_user_updates_existing(fake_psycopg) -> None:
    conn = MagicMock()
    cur = _cur_of(conn)
    cur.fetchone.return_value = (1,)  # role exists
    fake_psycopg.connect.return_value = conn
    result = PostgresEngine().create_user("bob", "newpass", database="appdb")
    assert result.success is True
    statements = [str(c) for c in cur.execute.call_args_list]
    assert any('ALTER ROLE "bob"' in s for s in statements)
    assert not any("CREATE ROLE" in s for s in statements)


# ---------- PostgreSQL is_available ----------


def test_pg_is_available_true(fake_psycopg) -> None:
    assert PostgresEngine().is_available() is True


def test_pg_is_available_false() -> None:
    with patch.dict(sys.modules, {"psycopg": None}):
        assert PostgresEngine().is_available() is False


# ---------- MySQL connect ----------


def test_mysql_connect_success(fake_pymysql) -> None:
    conn = MagicMock()
    conn.get_server_info.return_value = "8.4"
    fake_pymysql.connect.return_value = conn
    result = MySQLEngine().connect(host="h", user="root", password="p")
    assert result.success is True
    assert result.server_version == "8.4"


def test_mysql_connect_failure(fake_pymysql) -> None:
    fake_pymysql.connect.side_effect = RuntimeError("denied")
    result = MySQLEngine().connect()
    assert result.success is False
    assert "denied" in result.message


def test_mysql_connect_without_driver() -> None:
    with patch.dict(sys.modules, {"pymysql": None}):
        result = MySQLEngine().connect()
    assert result.success is False


def test_mysql_connect_default_port(fake_pymysql) -> None:
    fake_pymysql.connect.return_value = MagicMock()
    MySQLEngine().connect()
    assert fake_pymysql.connect.call_args.kwargs["port"] == 3306


# ---------- MySQL create/drop/user ----------


def test_mysql_create_database_success(fake_pymysql) -> None:
    conn = MagicMock()
    cur = _cur_of(conn)
    fake_pymysql.connect.return_value = conn
    result = MySQLEngine().create_database("appdb")
    assert result.success is True
    statements = [str(c) for c in cur.execute.call_args_list]
    assert any("CREATE DATABASE" in s for s in statements)


def test_mysql_create_database_invalid(fake_pymysql) -> None:
    result = MySQLEngine().create_database("bad`name")
    assert result.success is False


def test_mysql_drop_database_success(fake_pymysql) -> None:
    conn = MagicMock()
    fake_pymysql.connect.return_value = conn
    result = MySQLEngine().drop_database("appdb")
    assert result.success is True


def test_mysql_create_user_success(fake_pymysql) -> None:
    conn = MagicMock()
    cur = _cur_of(conn)
    fake_pymysql.connect.return_value = conn
    result = MySQLEngine().create_user("bob", "s3cret", host="localhost", database="appdb")
    assert result.success is True
    calls = [str(c) for c in cur.execute.call_args_list]
    assert any("CREATE USER" in s for s in calls)
    assert any("GRANT ALL PRIVILEGES" in s for s in calls)


def test_mysql_create_user_invalid(fake_pymysql) -> None:
    result = MySQLEngine().create_user("bob;drop", "pw")
    assert result.success is False


# ---------- MySQL is_available ----------


def test_mysql_is_available_true(fake_pymysql) -> None:
    assert MySQLEngine().is_available() is True


def test_mysql_is_available_false() -> None:
    with patch.dict(sys.modules, {"pymysql": None}):
        assert MySQLEngine().is_available() is False
