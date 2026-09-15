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

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and guidelines.

## License

MIT — see [LICENSE](LICENSE).
