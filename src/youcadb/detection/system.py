"""Detect OS, Docker, and installed database binaries."""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class SystemInfo:
    """Result of system detection."""

    os_name: str
    python_version: str
    docker_available: bool = False
    psql_available: bool = False
    mysql_client_available: bool = False


def detect_system() -> SystemInfo:
    """Gather information about the current system."""
    return SystemInfo(
        os_name=sys.platform,
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        docker_available=shutil.which("docker") is not None,
        psql_available=shutil.which("psql") is not None,
        mysql_client_available=shutil.which("mysql") is not None,
    )
