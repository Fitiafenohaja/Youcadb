"""Tests for the exceptions module."""

from __future__ import annotations

import pytest

from youcadb.exceptions import ConfigError, DatabaseConnectionError, DetectionError, YoucaDBError


def test_exceptions_inherit_from_base() -> None:
    assert issubclass(DatabaseConnectionError, YoucaDBError)
    assert issubclass(ConfigError, YoucaDBError)
    assert issubclass(DetectionError, YoucaDBError)


def test_exceptions_are_raisable() -> None:
    with pytest.raises(YoucaDBError):
        raise YoucaDBError("test")
    with pytest.raises(DatabaseConnectionError):
        raise DatabaseConnectionError("connection failed")
