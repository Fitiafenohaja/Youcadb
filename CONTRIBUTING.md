# Contributing to YoucaDB

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/youcadb/youcadb.git
cd youcadb

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Running Tests

```bash
# Unit tests only
pytest tests/unit/

# All tests (unit + integration, integration tests need database services)
pytest

# With coverage report
pytest --cov=youcadb --cov-report=term-missing
```

## Code Quality

We use **Ruff** for linting and formatting, and **mypy** for type checking:

```bash
ruff check src/ tests/        # lint
ruff format src/ tests/       # format
mypy src/                     # type check
```

Pre-commit hooks run these automatically on each commit.

## Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** — incompatible API changes
- **MINOR** — new functionality (backwards-compatible)
- **PATCH** — backwards-compatible bug fixes

Releases are triggered by pushing a git tag of the form `v*.*.*` (e.g. `v0.1.0`).
