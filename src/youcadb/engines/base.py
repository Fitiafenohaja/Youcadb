"""Abstract base class for database engines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ConnectionResult:
    """Result of a connection attempt."""

    success: bool
    message: str
    server_version: str | None = None


@dataclass(frozen=True)
class OperationResult:
    """Result of a database operation."""

    success: bool
    message: str


class Engine(ABC):
    """Interface every database engine must implement."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable engine name."""

    @property
    @abstractmethod
    def scheme(self) -> str:
        """URL scheme for DATABASE_URL (e.g. 'postgresql', 'mysql')."""

    @property
    @abstractmethod
    def default_port(self) -> int:
        """Default port number."""

    @abstractmethod
    def connect(
        self,
        host: str = "localhost",
        port: int | None = None,
        user: str = "postgres",
        password: str = "",
        database: str = "postgres",
    ) -> ConnectionResult:
        """Establish a connection to the database server."""

    @abstractmethod
    def create_database(self, database_name: str, **kwargs: Any) -> OperationResult:
        """Create a new database."""

    @abstractmethod
    def drop_database(self, database_name: str, **kwargs: Any) -> OperationResult:
        """Drop an existing database."""

    @abstractmethod
    def create_user(
        self,
        username: str,
        password: str,
        host: str = "localhost",
        database: str | None = None,
        admin_user: str = "",
        admin_password: str = "",
        port: int | None = None,
        user_host: str = "%",
    ) -> OperationResult:
        """Create a user and grant permissions.

        ``host`` is the server the admin connects to; ``user_host`` is the host
        mask the created user may connect from (ignored by PostgreSQL).
        """

    @abstractmethod
    def test_connection(
        self,
        host: str = "localhost",
        port: int | None = None,
        user: str = "postgres",
        password: str = "",
        database: str = "postgres",
    ) -> ConnectionResult:
        """Test a connection and return detailed status."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the engine driver is importable."""
