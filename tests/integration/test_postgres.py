"""Integration tests for PostgreSQL (require running service)."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    not os.environ.get("POSTGRES_HOST"),
    reason="PostgreSQL service not available",
)
def test_postgres_connect() -> None:
    """Verify we can connect to the PostgreSQL service."""
    # TODO: implement real connection test
    pytest.skip("Connection logic not yet implemented")
