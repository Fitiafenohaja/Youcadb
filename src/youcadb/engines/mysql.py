"""MySQL engine implementation (stub)."""

from __future__ import annotations

from typing import Any

from youcadb.engines.base import Engine


class MySQLEngine(Engine):
    """MySQL engine backed by *pymysql*."""

    @property
    def name(self) -> str:
        return "MySQL"

    def connect(self, **kwargs: Any) -> None:
        # TODO: implement connection via pymysql
        msg = "pymysql connection not yet implemented"
        raise NotImplementedError(msg)

    def create_database(self, database_name: str) -> None:
        # TODO: CREATE DATABASE via pymysql
        msg = "MySQL create_database not yet implemented"
        raise NotImplementedError(msg)

    def drop_database(self, database_name: str) -> None:
        # TODO: DROP DATABASE via pymysql
        msg = "MySQL drop_database not yet implemented"
        raise NotImplementedError(msg)

    def is_available(self) -> bool:
        try:
            import pymysql  # noqa: F401
        except ImportError:
            return False
        return True
