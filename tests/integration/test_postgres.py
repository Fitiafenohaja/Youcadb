"""Integration tests for PostgreSQL (require running service)."""

from __future__ import annotations

import os

import pytest

from youcadb.engines.postgres import PostgresEngine

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    not os.environ.get("POSTGRES_HOST"),
    reason="PostgreSQL service not available",
)
def test_postgres_connect() -> None:
    """Verify we can connect to the PostgreSQL service."""
    engine = PostgresEngine()
    result = engine.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
    )
    assert result.success


@pytest.mark.skipif(
    not os.environ.get("POSTGRES_HOST"),
    reason="PostgreSQL service not available",
)
def test_postgres_create_and_drop_database() -> None:
    """Verify database creation and cleanup."""
    engine = PostgresEngine()
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = int(os.environ.get("POSTGRES_PORT", "5432"))
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "postgres")

    result = engine.create_database(
        "youcadb_test_db", host=host, port=port, user=user, password=password
    )
    assert result.success

    drop_result = engine.drop_database(
        "youcadb_test_db", host=host, port=port, user=user, password=password
    )
    assert drop_result.success


@pytest.mark.skipif(
    not os.environ.get("POSTGRES_HOST"),
    reason="PostgreSQL service not available",
)
def test_postgres_create_user_and_connect() -> None:
    """Verify user creation and a connection as the new user."""
    engine = PostgresEngine()
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = int(os.environ.get("POSTGRES_PORT", "5432"))
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "postgres")

    db_name = "youcadb_user_db"
    engine.create_database(db_name, host=host, port=port, user=user, password=password)
    result = engine.create_user(
        "youcadb_user",
        "youcadb_pass",
        host=host,
        database=db_name,
        port=port,
        user=user,
        password=password,
    )
    assert result.success

    conn = engine.connect(
        host=host, port=port, user="youcadb_user", password="youcadb_pass", database=db_name
    )
    assert conn.success

    engine.drop_database(db_name, host=host, port=port, user=user, password=password)
