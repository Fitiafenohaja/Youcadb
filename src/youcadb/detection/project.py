"""Detect the current project's language, framework, and DB driver."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectInfo:
    """Result of project detection."""

    language: str | None = None
    framework: str | None = None
    database_driver: str | None = None


def detect_project(path: str = ".") -> ProjectInfo:
    """Inspect *path* and return detected project metadata.

    TODO: implement file/pyproject.toml scanning for language, framework, driver.
    """
    return ProjectInfo()
