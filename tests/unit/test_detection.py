"""Tests for detection modules."""

from __future__ import annotations

from youcadb.detection.project import ProjectInfo, detect_project
from youcadb.detection.system import SystemInfo, detect_system


def test_detect_project_returns_project_info() -> None:
    result = detect_project()
    assert isinstance(result, ProjectInfo)


def test_detect_system_returns_system_info() -> None:
    result = detect_system()
    assert isinstance(result, SystemInfo)
    assert result.os_name  # should be non-empty (e.g. "linux", "darwin")
    assert result.python_version  # should be non-empty
