# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Detection of Java projects** (Maven `pom.xml`, Gradle `build.gradle`/`build.gradle.kts`)
  with framework recognition (Spring Boot, Spring, Quarkus, Micronaut) and driver-based
  engine hints (`org.postgresql:postgresql`, `com.mysql:mysql-connector-j`, MariaDB).
- **Detection of .NET projects** (`*.csproj` / `*.sln`) with ASP.NET Core and Entity
  Framework Core recognition, and PostgreSQL/MySQL engine hints from `Npgsql`,
  `MySqlConnector`, `Pomelo.EntityFrameworkCore.MySql`…
- **Backend-first detection priority**: Python, Java, .NET, Ruby and PHP now win over a
  front-end `package.json` (Node.js) in monorepos; `.csproj`/`.sln` files nested up to two
  levels deep are picked up as well.
- **OS install guide tests**: Windows (winget), macOS (Homebrew), Ubuntu/Fedora and
  unknown-distro fallback paths for `install_guide` and `default_unix_socket_user`.
- **Python 3.14 support**: verified against 3.14 in the local/CI matrix, new
  `Programming Language :: Python :: 3.14` classifier; the obsolete `typer[all]` extra
  was dropped in favour of plain `typer>=0.12` (rich/shellingham are hard deps since
  typer 0.27).
- **Cross-platform CI**: lint/typecheck run on Python 3.14, and a new matrix job runs the
  unit tests on macOS and Windows (Python 3.14); `.python-version` pins the dev version.
- **README rewritten in French** with the detection matrix, security guarantees,
  Python-version policy and cross-platform support.
- **PyPI-specific long description** (`description.md`): the package page now shows a
  user-facing French description instead of the full developer README.
- **Full engine implementations** for PostgreSQL (`psycopg`) and MySQL (`pymysql`):
  connect with server-version reporting, idempotent database/user creation with
  privilege grants, drop with active-connection termination, and connection tests.
- **Project detection**: scans `pyproject.toml`, `requirements.txt`, `package.json`,
  `composer.json`, `Gemfile`, `docker-compose.yml`, `.env`/`.env.example` to detect the
  language (Python, Node.js, PHP, Ruby), framework (FastAPI, Flask, Django, SQLAlchemy,
  Express, NestJS, Laravel, …) and the recommended database engine from detected drivers.
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

- `youcadb doctor` no longer reports a running server as "down" when the stored
  credentials are rejected (e.g. `fe_sendauth: no password supplied`): authentication
  rejections on the server and database probes are warnings pointing to `youcadb init`
  instead of a false "start the service" error.

- `youcadb create` Docker fallback now honours the chosen host port and admin
  password (unique container name derived from the port), instead of always trying
  the default port — which previously collided with an existing instance and failed.
  Docker start failures now show the underlying reason, and the tool waits up to a
  minute for the freshly-started container to accept connections.

- Integration tests (`tests/integration`) use the current `Engine.create_user` contract
  (`admin_user` / `admin_password`) and MySQL admin credentials instead of the
  service-scoped `testuser`, fixing the Linux CI matrix (Python 3.13/3.14).
- `youcadb doctor` « server » probe now connects through the host/port/database from
  the project configuration instead of probing the maintenance database with the app
  credentials, avoiding a false "authentication failed" when the app user has no access
  to the system database. Access denials are reported as a warning, not an error.
- PostgreSQL `CREATE USER` password escaping (placeholders are invalid in DDL).
- Database/user creation is now idempotent across both engines.
- `youcadb create` with a missing Python driver now shows install/start guidance
  and (when available) offers a Docker container instead of stopping abruptly.

### Security

- Removed `--password` and `--admin-password` CLI flags: secrets could leak into
  the shell history. Passwords are now read interactively (masked input) or from
  the `YOUCADB_PASSWORD` / `YOUCADB_ADMIN_PASSWORD` environment variables.
- `youcadb config generate` also honours `YOUCADB_PASSWORD` when set.
- `youcadb config generate` and `youcadb config show` no longer print passwords on
  stdout: the displayed `DATABASE_URL` is masked (`:***`) and `password` lines are
  redacted in `config show`.
- `confirm`, `text_input` and `password_input` degrade gracefully instead of
  crashing when no terminal input is available (EOF / non-TTY).

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