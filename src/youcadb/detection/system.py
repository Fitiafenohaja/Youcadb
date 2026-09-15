"""Detect OS, Docker, and installed database binaries."""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class SystemInfo:
    """Result of system detection."""

    os_name: str
    python_version: str
    docker_available: bool = False
    docker_running: bool = False
    psql_available: bool = False
    mysql_client_available: bool = False
    pg_service_available: bool = False
    mysql_service_available: bool = False


def _check_service(service: str) -> bool:
    """Check if a systemd service exists and is active."""
    try:
        import subprocess

        if shutil.which("systemctl"):
            result = subprocess.run(
                ["systemctl", "is-active", "--quiet", service],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
    except Exception:
        pass
    return False


def _check_brew_service(service: str) -> bool:
    """Check if a Homebrew service is running."""
    try:
        if shutil.which("brew"):
            result = subprocess.run(
                ["brew", "services", "list"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return service in result.stdout.lower()
    except Exception:
        pass
    return False


def _is_docker_running() -> bool:
    """Check if the Docker daemon is running."""
    if not shutil.which("docker"):
        return False
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def detect_system() -> SystemInfo:
    """Gather information about the current system."""
    return SystemInfo(
        os_name=sys.platform,
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        docker_available=shutil.which("docker") is not None,
        docker_running=_is_docker_running(),
        psql_available=shutil.which("psql") is not None,
        mysql_client_available=shutil.which("mysql") is not None,
        pg_service_available=_check_service("postgresql") or _check_brew_service("postgresql"),
        mysql_service_available=_check_service("mysql") or _check_brew_service("mysql"),
    )
