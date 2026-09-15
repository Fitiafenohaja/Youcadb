"""Detect the current project's language, framework, and DB driver."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:
    import tomli as tomllib

PG_DRIVERS = {"psycopg2", "psycopg", "asyncpg", "psycopg2-binary"}
MYSQL_DRIVERS = {"pymysql", "mysqlclient", "mysql-connector-python", "mysql-connector"}

PG_FRAMEWORKS: dict[str, str] = {
    "fastapi": "FastAPI",
    "flask": "Flask",
    "django": "Django",
    "sqlalchemy": "SQLAlchemy",
    "alembic": "Alembic",
    "uvicorn": "Uvicorn",
}

MYSQL_FRAMEWORKS: dict[str, str] = {
    "fastapi": "FastAPI",
    "flask": "Flask",
    "django": "Django",
    "sqlalchemy": "SQLAlchemy",
    "alembic": "Alembic",
}

NODE_DRIVERS: dict[str, str] = {
    "pg": "PostgreSQL (pg)",
    "psql": "PostgreSQL (node-postgres)",
    "postgres": "PostgreSQL (postgres.js)",
    "mysql2": "MySQL (mysql2)",
    "mysql": "MySQL (mysql)",
    "knex": "Knex.js",
    "sequelize": "Sequelize",
    "typeorm": "TypeORM",
    "prisma": "Prisma",
    "drizzle-orm": "Drizzle ORM",
    "mikro-orm": "MikroORM",
}


@dataclass(frozen=True)
class ProjectInfo:
    """Result of project detection."""

    language: str | None = None
    framework: str | None = None
    database_driver: str | None = None
    engine_hint: str | None = None  # "postgres" or "mysql"
    docker_compose: bool = False
    env_file: bool = False
    env_example: bool = False
    details: list[str] = field(default_factory=list)


def _read_pyproject(path: Path) -> dict[str, Any] | None:
    """Read a pyproject.toml file."""
    try:
        return dict(tomllib.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return None


def _read_package_json(path: Path) -> dict[str, Any] | None:
    """Read a package.json file."""
    import json

    try:
        return dict(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return None


def _read_requirements(path: Path) -> set[str]:
    """Read a requirements.txt file and return package names."""
    deps: set[str] = set()
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            name = re.split(r"[>=<!\[]", line)[0].strip().lower().replace("-", "_")
            if name:
                deps.add(name)
    except Exception:
        pass
    return deps


def _detect_python_project(
    project_dir: Path,
) -> tuple[str | None, str | None, str | None, list[str]]:
    """Detect language/framework/driver from Python project files."""
    language = "Python"
    framework: str | None = None
    driver: str | None = None
    details: list[str] = [f"{language} detected"]

    all_deps: set[str] = set()

    pyproject = _read_pyproject(project_dir / "pyproject.toml")
    if pyproject:
        project_deps = pyproject.get("project", {}).get("dependencies", [])
        for dep in project_deps:
            name = re.split(r"[>=<!\[]", dep)[0].strip().lower().replace("-", "_")
            all_deps.add(name)

        for extra_deps in pyproject.get("project", {}).get("optional-dependencies", {}).values():
            for dep in extra_deps:
                name = re.split(r"[>=<!\[]", dep)[0].strip().lower().replace("-", "_")
                all_deps.add(name)

    for req_file in ["requirements.txt", "requirements-dev.txt", "requirements.in"]:
        req_path = project_dir / req_file
        if req_path.exists():
            all_deps |= _read_requirements(req_path)

    for dep in all_deps:
        if dep in PG_DRIVERS:
            driver = dep.replace("_", "-")
            details.append(f"PostgreSQL driver detected ({driver})")
            break
        if dep in MYSQL_DRIVERS:
            driver = dep.replace("_", "-")
            details.append(f"MySQL driver detected ({driver})")
            break

    fw_map = {**PG_FRAMEWORKS, **MYSQL_FRAMEWORKS}
    for dep in all_deps:
        if dep in fw_map:
            framework = fw_map[dep]
            details.append(f"{framework} detected")
            break

    return language, framework, driver, details


def _detect_node_project(
    project_dir: Path,
) -> tuple[str | None, str | None, str | None, str | None, list[str]]:
    """Detect language/framework/driver from Node.js project files."""
    language = "Node.js"
    framework: str | None = None
    driver: str | None = None
    engine_hint: str | None = None
    details: list[str] = [f"{language} detected"]

    pkg = _read_package_json(project_dir / "package.json")
    if pkg is None:
        return language, framework, driver, engine_hint, details

    all_deps: set[str] = set()
    for dep_key in ("dependencies", "devDependencies"):
        deps_dict = pkg.get(dep_key, {})
        for dep_name in deps_dict:
            all_deps.add(dep_name.lower())

    for dep in all_deps:
        if dep in NODE_DRIVERS:
            driver = NODE_DRIVERS[dep]
            if dep in ("pg", "psql", "postgres"):
                engine_hint = "postgres"
                details.append(f"PostgreSQL driver detected ({driver})")
            elif dep in ("mysql2", "mysql"):
                engine_hint = "mysql"
                details.append(f"MySQL driver detected ({driver})")
            break

    if "express" in all_deps or "fastify" in all_deps:
        framework = "Express" if "express" in all_deps else "Fastify"
        details.append(f"{framework} detected")
    elif "next" in all_deps:
        framework = "Next.js"
        details.append(f"{framework} detected")
    elif "nestjs" in all_deps or "@nestjs/core" in all_deps:
        framework = "NestJS"
        details.append(f"{framework} detected")

    return language, framework, driver, engine_hint, details


def detect_project(path: str = ".") -> ProjectInfo:
    """Inspect *path* and return detected project metadata."""
    project_dir = Path(path).resolve()
    details: list[str] = []
    language: str | None = None
    framework: str | None = None
    driver: str | None = None
    engine_hint: str | None = None
    docker_compose = (project_dir / "docker-compose.yml").exists() or (
        project_dir / "docker-compose.yaml"
    ).exists()
    env_file = (project_dir / ".env").exists()
    env_example = (project_dir / ".env.example").exists()

    if docker_compose:
        details.append("docker-compose.yml detected")
    if env_file:
        details.append(".env file detected")
    if env_example:
        details.append(".env.example detected")

    has_pyproject = (project_dir / "pyproject.toml").exists()
    has_requirements = (project_dir / "requirements.txt").exists()
    has_package_json = (project_dir / "package.json").exists()

    if has_pyproject or has_requirements:
        language, framework, driver, py_details = _detect_python_project(project_dir)
        details.extend(py_details)
        if driver:
            engine_hint = (
                "postgres"
                if "psycopg" in (driver or "").lower() or "asyncpg" in (driver or "").lower()
                else "mysql"
            )

    elif has_package_json:
        language, framework, driver, engine_hint, node_details = _detect_node_project(project_dir)
        details.extend(node_details)

    return ProjectInfo(
        language=language,
        framework=framework,
        database_driver=driver,
        engine_hint=engine_hint,
        docker_compose=docker_compose,
        env_file=env_file,
        env_example=env_example,
        details=details,
    )
