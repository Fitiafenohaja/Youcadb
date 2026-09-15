# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Full engine implementations** for PostgreSQL (`psycopg`) and MySQL (`pymysql`):
  connect with server-version reporting, idempotent database/user creation with
  privilege grants, drop with active-connection termination, and connection tests.
- **Project detection**: scans `pyproject.toml`, `requirements.txt`, `package.json`,
  `docker-compose.yml`, `.env`/`.env.example` to detect language (Python/Node.js),
  framework (FastAPI, Flask, Django, SQLAlchemy, Express, NestJS, …) and the
  recommended database engine from detected drivers.
- **`youcadb init`**: interactive detection wizard that recommends an engine, handles
  existing config (with `--force`), and writes a real `.youcadb.toml`.
- **`youcadb create`**: full wizard to create database + user + permissions, with
  OS-aware install/start guidance when the engine is missing or stopped, Docker
  start proposal, and masked password input.
- **`youcadb status`**: real connectivity checks (driver, server, database, auth) and
  a HEALTHY/UNHEALTHY verdict.
- **`youcadb doctor`**: the core diagnostic with OK/WARNING/ERROR results, corrective
  actions, env coherence checks and basic-security checks (0.0.0.0 exposure,
  passwords committed to Git).
- **`youcadb config generate` / `show`**: real `.env` generation with engine-adapted
  `DATABASE_URL` and pretty-printed config display.
- **Interactive menus** backed by `questionary` (keyboard + mouse) with a plain
  keyboard fallback for non-interactive terminals; masked `password_input`.
- **Config model** (`.youcadb.toml` read/write) with `DBConfig`, `load_config`,
  `save_config`, `generate_env_content`.
- **OS-aware install guide** (apt/dnf/brew/winget + Docker) and service detection.

### Changed

- `Engine` base class now exposes `scheme`, `default_port`, `ConnectionResult`,
  `OperationResult`, and a `create_user`/`test_connection` contract.
- `youcadb` with no arguments now inspects the project and shows a status summary
  (or points to `youcadb init`) instead of a plain banner.
- Added `questionary` and `tomli` (for Python < 3.11) runtime dependencies.

### Fixed

- PostgreSQL `CREATE USER` password escaping (placeholders are invalid in DDL).
- Database/user creation is now idempotent across both engines.

## [0.1.0] - Initial scaffolding

### Added

- Initial project scaffolding with src layout.
- CLI entry point with Typer: `youcadb`, `youcadb init`, `youcadb create`,
  `youcadb status`, `youcadb doctor`, `youcadb config`.
- Abstract `Engine` base class with `PostgresEngine` and `MySQLEngine` stubs.
- Project and system detection modules (stubs).
- Interactive menu utilities with keyboard fallback.
- CI pipeline (GitHub Actions) with Python 3.10–3.13 matrix, lint, type check,
  and integration tests.
- Release pipeline with Trusted Publisher (OIDC) for PyPI.
- Pre-commit hooks for Ruff and mypy.