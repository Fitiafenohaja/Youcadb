"""Project-wide exception types."""

from __future__ import annotations


class YoucaDBError(Exception):
    """Base exception for all youcadb errors."""


class DatabaseConnectionError(YoucaDBError):
    """Raised when a database connection fails."""


class ConfigError(YoucaDBError):
    """Raised for configuration-related issues."""


class DetectionError(YoucaDBError):
    """Raised when project/system detection fails."""
