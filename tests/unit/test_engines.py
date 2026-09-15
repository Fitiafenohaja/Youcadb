"""Tests for engine stubs."""

from __future__ import annotations

from youcadb.engines.mysql import MySQLEngine
from youcadb.engines.postgres import PostgresEngine


def test_postgres_engine_name() -> None:
    engine = PostgresEngine()
    assert engine.name == "PostgreSQL"


def test_mysql_engine_name() -> None:
    engine = MySQLEngine()
    assert engine.name == "MySQL"


def test_postgres_is_available_returns_bool() -> None:
    engine = PostgresEngine()
    assert isinstance(engine.is_available(), bool)


def test_mysql_is_available_returns_bool() -> None:
    engine = MySQLEngine()
    assert isinstance(engine.is_available(), bool)


def test_postgres_scheme() -> None:
    assert PostgresEngine().scheme == "postgresql"


def test_mysql_scheme() -> None:
    assert MySQLEngine().scheme == "mysql"


def test_postgres_default_port() -> None:
    assert PostgresEngine().default_port == 5432


def test_mysql_default_port() -> None:
    assert MySQLEngine().default_port == 3306


def test_get_engine() -> None:
    from youcadb.engines import get_engine

    assert isinstance(get_engine("postgres"), PostgresEngine)
    assert isinstance(get_engine("mysql"), MySQLEngine)
    assert isinstance(get_engine("postgresql"), PostgresEngine)


def test_get_engine_invalid() -> None:
    import pytest

    from youcadb.engines import get_engine
    from youcadb.exceptions import ConfigError

    with pytest.raises(ConfigError):
        get_engine("sqlite")
