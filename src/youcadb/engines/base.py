"""Abstract base class for database engines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Engine(ABC):
    """Interface every database engine must implement."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable engine name."""

    @abstractmethod
    def connect(self, **kwargs: Any) -> None:
        """Establish a connection to the database server."""

    @abstractmethod
    def create_database(self, database_name: str) -> None:
        """Create a new database."""

    @abstractmethod
    def drop_database(self, database_name: str) -> None:
        """Drop an existing database."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the engine driver is importable."""
