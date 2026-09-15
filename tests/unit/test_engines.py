"""Tests for engine stubs."""

from __future__ import annotations

import pytest

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


def test_postgres_create_database_not_implemented() -> None:
    engine = PostgresEngine()
    with pytest.raises(NotImplementedError):
        engine.create_database("test_db")


def test_mysql_create_database_not_implemented() -> None:
    engine = MySQLEngine()
    with pytest.raises(NotImplementedError):
        engine.create_database("test_db")
