"""Database engine interfaces."""

from __future__ import annotations

from youcadb.engines.base import ConnectionResult, Engine, OperationResult
from youcadb.engines.mysql import MySQLEngine
from youcadb.engines.postgres import PostgresEngine

ENGINE_MAP: dict[str, type[Engine]] = {
    "postgres": PostgresEngine,
    "postgresql": PostgresEngine,
    "mysql": MySQLEngine,
}


def get_engine(name: str) -> Engine:
    """Return an engine instance by name ('postgres' or 'mysql')."""
    engine_class = ENGINE_MAP.get(name.lower())
    if engine_class is None:
        from youcadb.exceptions import ConfigError

        msg = f"Unknown engine: {name}. Choose from 'postgres' or 'mysql'."
        raise ConfigError(msg)
    return engine_class()


__all__ = [
    "ENGINE_MAP",
    "ConnectionResult",
    "Engine",
    "MySQLEngine",
    "OperationResult",
    "PostgresEngine",
    "get_engine",
]
