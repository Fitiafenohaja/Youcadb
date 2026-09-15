"""PostgreSQL engine implementation (stub)."""

from __future__ import annotations

from typing import Any

from youcadb.engines.base import Engine


class PostgresEngine(Engine):
    """PostgreSQL engine backed by *psycopg*."""

    @property
    def name(self) -> str:
        return "PostgreSQL"

    def connect(self, **kwargs: Any) -> None:
        # TODO: implement connection via psycopg
        msg = "psycopg connection not yet implemented"
        raise NotImplementedError(msg)

    def create_database(self, database_name: str) -> None:
        # TODO: CREATE DATABASE via psycopg
        msg = "PostgreSQL create_database not yet implemented"
        raise NotImplementedError(msg)

    def drop_database(self, database_name: str) -> None:
        # TODO: DROP DATABASE via psycopg
        msg = "PostgreSQL drop_database not yet implemented"
        raise NotImplementedError(msg)

    def is_available(self) -> bool:
        try:
            import psycopg  # noqa: F401
        except ImportError:
            return False
        return True
