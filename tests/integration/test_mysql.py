"""Integration tests for MySQL (require running service)."""

from __future__ import annotations

import os

import pytest

from youcadb.engines.mysql import MySQLEngine

pytestmark = pytest.mark.integration


def _mysql_admin() -> tuple[str, str]:
    """Return the admin credentials for database/user management."""
    return (
        os.environ.get("MYSQL_ADMIN_USER", "root"),
        os.environ.get("MYSQL_ADMIN_PASSWORD", ""),
    )


@pytest.mark.skipif(
    not os.environ.get("MYSQL_HOST"),
    reason="MySQL service not available",
)
def test_mysql_connect() -> None:
    """Verify we can connect to the MySQL service."""
    engine = MySQLEngine()
    result = engine.connect(
        host=os.environ.get("MYSQL_HOST", "localhost"),
        port=int(os.environ.get("MYSQL_PORT", "3306")),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ.get("MYSQL_PASSWORD", ""),
    )
    assert result.success


@pytest.mark.skipif(
    not os.environ.get("MYSQL_HOST"),
    reason="MySQL service not available",
)
def test_mysql_create_and_drop_database() -> None:
    """Verify database creation and cleanup."""
    engine = MySQLEngine()
    host = os.environ.get("MYSQL_HOST", "localhost")
    port = int(os.environ.get("MYSQL_PORT", "3306"))
    admin_user, admin_password = _mysql_admin()

    result = engine.create_database(
        "youcadb_test_db", host=host, port=port, user=admin_user, password=admin_password
    )
    assert result.success

    drop_result = engine.drop_database(
        "youcadb_test_db", host=host, port=port, user=admin_user, password=admin_password
    )
    assert drop_result.success


@pytest.mark.skipif(
    not os.environ.get("MYSQL_HOST"),
    reason="MySQL service not available",
)
def test_mysql_create_user_and_connect() -> None:
    """Verify user creation and a connection as the new user."""
    engine = MySQLEngine()
    host = os.environ.get("MYSQL_HOST", "localhost")
    port = int(os.environ.get("MYSQL_PORT", "3306"))
    admin_user, admin_password = _mysql_admin()

    db_name = "youcadb_user_db"
    engine.create_database(db_name, host=host, port=port, user=admin_user, password=admin_password)
    result = engine.create_user(
        "youcadb_user",
        "youcadb_pass",
        host=host,
        database=db_name,
        port=port,
        admin_user=admin_user,
        admin_password=admin_password,
    )
    assert result.success

    conn = engine.connect(
        host=host, port=port, user="youcadb_user", password="youcadb_pass", database=db_name
    )
    assert conn.success

    engine.drop_database(db_name, host=host, port=port, user=admin_user, password=admin_password)
