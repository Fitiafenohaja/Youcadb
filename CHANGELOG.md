# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial project scaffolding with src layout.
- CLI entry point with Typer: `youcadb`, `youcadb init`, `youcadb create`, `youcadb status`, `youcadb doctor`, `youcadb config`.
- Abstract `Engine` base class with `PostgresEngine` and `MySQLEngine` stubs.
- Project and system detection modules (stubs).
- Interactive menu utilities with keyboard fallback.
- CI pipeline (GitHub Actions) with Python 3.10–3.13 matrix, lint, type check, and integration tests.
- Release pipeline with Trusted Publisher (OIDC) for PyPI.
- Pre-commit hooks for Ruff and mypy.
