# YoucaDB

[![CI](https://github.com/youcadb/youcadb/actions/workflows/ci.yml/badge.svg)](https://github.com/youcadb/youcadb/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/youcadb)](https://pypi.org/project/youcadb/)
[![Coverage](https://img.shields.io/codecov/c/github/youcadb/youcadb)](https://codecov.io/gh/youcadb/youcadb)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Database diagnostics and configuration CLI for developers.**

YoucaDB helps developers quickly diagnose, configure, and manage local PostgreSQL and MySQL database instances. Detect your project's setup, create databases, verify connectivity, and troubleshoot common issues — all from a single CLI.

## Installation

```bash
pip install youcadb
```

With database driver extras:

```bash
pip install youcadb[postgres]   # PostgreSQL support (psycopg)
pip install youcadb[mysql]      # MySQL support (pymysql)
pip install youcadb[all]        # Both drivers
```

## Quick Start

```bash
# Show welcome banner and available commands
youcadb

# Initialise youcadb configuration in your project
youcadb init

# Create a PostgreSQL database
youcadb create postgres --name my_app_db

# Check the status of detected databases
youcadb status

# Run diagnostics on your local environment
youcadb doctor

# Generate a default configuration file
youcadb config generate
```

## Commands

| Command | Description |
|---|---|
| `youcadb` | Display welcome banner |
| `youcadb init` | Initialise `.youcadb.toml` in the current directory |
| `youcadb create <engine>` | Create a database (`postgres` or `mysql`) |
| `youcadb status` | Show status of detected databases |
| `youcadb doctor` | Run environment diagnostics |
| `youcadb config generate` | Generate default configuration |

## Releases & PyPI Publishing

Releases are published automatically when a git tag `v*.*.*` is pushed (or a GitHub
Release is published), via the `.github/workflows/release.yml` workflow using
[Trusted Publishing (OIDC)](https://docs.pypi.org/trusted-publishers/) — no PyPI API
token is stored in GitHub secrets.

### One-time setup before the first release

1. Go to **PyPI → Account settings → Publishing → Add a new pending publisher** at
   <https://pypi.org/manage/account/publishing/>.
2. Fill in the form:
   - **Project name**: `youcadb`
   - **Publisher owner**: `<your-github-org-or-username>`
   - **Repository name**: `youcadb`
   - **Workflow name**: `release.yml`
   - **Environment name**: `pypi` (must match `environment: pypi` in the workflow job)
3. Click **Add publisher**. The `repository-url` and `skip-existing` fields used in the
   workflow do not require changes.
4. Repeat the same configuration on TestPyPI if you want the TestPyPI job to work:
   - TestPyPI: `https://test.pypi.org/manage/account/publishing/`
   - Project pending name: `youcadb` — use this job's environment accordingly.

After that, pushing `git tag v0.1.0` (and a draft GitHub Release) will publish `youcadb`
to TestPyPI and PyPI automatically.

### Creating a release

```bash
git tag v0.2.0 && git push origin v0.2.0
```

The workflow builds the wheel/sdist, verifies with `twine check`, publishes to TestPyPI
then PyPI, and generates GitHub release notes from commits since the last tag.

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and guidelines.

## License

MIT — see [LICENSE](LICENSE).
