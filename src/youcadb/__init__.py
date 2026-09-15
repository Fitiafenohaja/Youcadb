"""YoucaDB - Database diagnostics and configuration CLI for developers."""

from __future__ import annotations

try:
    from importlib.metadata import version

    __version__ = version("youcadb")
except Exception:  # pragma: no cover
    __version__ = "0.0.0"

__all__ = ["__version__"]
