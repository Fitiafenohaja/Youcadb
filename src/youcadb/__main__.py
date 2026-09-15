"""Allow running youcadb as ``python -m youcadb``."""

from __future__ import annotations

from youcadb.cli import app

if __name__ == "__main__":
    app()
