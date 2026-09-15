"""Integration tests for MySQL (require running service)."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    not os.environ.get("MYSQL_HOST"),
    reason="MySQL service not available",
)
def test_mysql_connect() -> None:
    """Verify we can connect to the MySQL service."""
    # TODO: implement real connection test
    pytest.skip("Connection logic not yet implemented")
