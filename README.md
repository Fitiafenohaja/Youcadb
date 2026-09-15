# Youcadb

[![CI](https://github.com/Fitiafenohaja/Youcadb/actions/workflows/ci.yml/badge.svg)](https://github.com/Fitiafenohaja/Youcadb/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/youcadb)](https://pypi.org/project/youcadb/)
[![Coverage](https://img.shields.io/codecov/c/github/Fitiafenohaja/Youcadb)](https://codecov.io/gh/Fitiafenohaja/Youcadb)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Database diagnostics and configuration CLI for developers.**

Youcadb detects your project's language and framework, connects to PostgreSQL or MySQL, creates databases and users, and runs full environment diagnostics — all from a single, interactive CLI.

---

## Features

- **Automatic project detection** — reads `pyproject.toml`, `package.json`, `docker-compose.yml`, `.env` and infers engine, host, port, and credentials.
- **Interactive wizard** — guided prompts for `init` and `create` with sensible defaults and fallbacks for non-TTY environments.
- **Idempotent engine operations** — creates databases and users only when they don't already exist; updates passwords safely.
- **`youcadb doctor`** — checks driver presence, server connectivity, `0.0.0.0` bind exposure, git-tracked secrets, and more.
- **`youcadb config`** — generate `.env` files from `.youcadb.toml`; inspect current settings.
- **Secure by design** — flags passwords tracked in git and dangerous bind addresses; never writes credentials to stdout.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python ≥ 3.10 | |
| PostgreSQL **or** MySQL | Dockerised or local install |
| `psycopg[binary]` | Required for PostgreSQL (`pip install youcadb[postgres]`) |
| `pymysql` | Required for MySQL (`pip install youcadb[mysql]`) |

---

## Installation

```bash
pip install youcadb           # core CLI (no drivers)
pip install youcadb[postgres] # + psycopg (PostgreSQL)
pip install youcadb[mysql]    # + pymysql (MySQL)
pip install youcadb[all]      # both drivers
```

---

## Quick start

```bash
# Initialise configuration in your project root
youcadb init --no-interactive

# Create a database interactively (prompts for name, user, password)
youcadb create postgres

# Non-interactive: specify everything via flags
youcadb create postgres \
  --name my_app_db \
  --user app_user \
  --password s3cret \
  --admin-password postgres

# Check project health
youcadb status

# Run full environment diagnostics
youcadb doctor

# Generate .env from current .youcadb.toml
youcadb config generate

# Show effective configuration
youcadb config show
```

---

## Commands

| Command | Description |
|---|---|
| `youcadb` | Show project status or initialisation hint |
| `youcadb init [--no-interactive]` | Detect project and write `.youcadb.toml` |
| `youcadb create <engine> [--name ...] [--user ...]` | Create database, user, and grant permissions |
| `youcadb status` | Display connection health |
| `youcadb doctor` | Full diagnostics (driver, server, config, security) |
| `youcadb config generate [--force]` | Generate `.env` from `.youcadb.toml` |
| `youcadb config show` | Print active configuration |

Run `youcadb <command> --help` for full options.

---

## Configuration

Yocabd stores its settings in `.youcadb.toml` at the project root:

```toml
[project]
  name = "myproject"

[database]
  engine = "postgres"
  host   = "localhost"
  port   = 5432
  name   = "myproject"
  user   = "app_user"
  password = "s3cret"   # only if stored in the file
```

Generated `.env` files are added to `.gitignore` by default.

---

## Development

```bash
git clone https://github.com/Fitiafenohaja/Youcadb.git
cd Youcadb
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
```

### Quality gates

```bash
ruff check src tests       # lint
ruff format --check src tests  # format
mypy src/youcadb           # type check
pytest tests/unit --cov=youcadb  # tests (≥80% coverage required)
```

### Running integration tests

Set environment variables for a real database, then run:

```bash
export POSTGRES_HOST=localhost POSTGRES_PORT=5432 \
       POSTGRES_USER=postgres  POSTGRES_PASSWORD=postgres
pytest tests/integration/test_postgres.py -v
```

---

## Releases

Pushing a `v*.*.*` tag (or publishing a GitHub Release) triggers `.github/workflows/release.yml` and publishes to PyPI via [Trusted Publishing (OIDC)](https://docs.pypi.org/trusted-publishers/) — no API token is stored in secrets.

**One-time setup (PyPI):**
1. Go to [PyPI Publishing settings](https://pypi.org/manage/account/publishing/) → **Add pending publisher**.
2. Fill: project `youcadb`, owner `Fitiafenohaja`, repo `Youcadb`, workflow `release.yml`, environment `pypi`.

**Creating a release:**

```bash
git tag v0.2.0
git push origin v0.2.0
```

---

## Contributing

Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for setup and guidelines.

## License

MIT — see [LICENSE](LICENSE).
