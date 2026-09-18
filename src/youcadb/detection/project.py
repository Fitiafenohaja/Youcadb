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

PHP_PG_DRIVERS: set[str] = {"ext-pdo_pgsql", "ext-pgsql", "ext-pg"}
PHP_MYSQL_DRIVERS: set[str] = {"ext-pdo_mysql", "ext-mysqli", "ext-mysql"}
PHP_FRAMEWORKS: dict[str, str] = {
    "laravel/framework": "Laravel",
    "laravel/laravel": "Laravel",
    "symfony/symfony": "Symfony",
    "symfony/framework-bundle": "Symfony",
    "cakephp/cakephp": "CakePHP",
    "codeigniter4/framework": "CodeIgniter",
}

RUBY_PG_DRIVERS: set[str] = {"pg"}
RUBY_MYSQL_DRIVERS: set[str] = {"mysql2"}
RUBY_FRAMEWORKS: dict[str, str] = {
    "rails": "Ruby on Rails",
    "sinatra": "Sinatra",
}

JAVA_PG_ARTIFACTS: set[str] = {"postgresql"}
JAVA_MYSQL_ARTIFACTS: set[str] = {
    "mysql-connector-j",
    "mysql-connector-java",
    "mariadb-java-client",
}
JAVA_FRAMEWORK_MARKERS: list[tuple[str, str]] = [
    ("spring-boot", "Spring Boot"),
    ("spring", "Spring"),
    ("quarkus", "Quarkus"),
    ("micronaut", "Micronaut"),
]

DOTNET_PG_PACKAGES: set[str] = {"npgsql", "npgsql.entityframeworkcore.postgresql"}
DOTNET_MYSQL_PACKAGES: set[str] = {
    "mysqlconnector",
    "mysql.data",
    "mysql.entityframeworkcore",
    "pomelo.entityframeworkcore.mysql",
}

_GRADLE_COORD_RE = re.compile(r"""["'(]([\w]+\.[\w.]+):([\w][\w.-]*)["')]""")

_NODE_PG_DRIVERS = ("pg", "psql", "postgres")
_NODE_MYSQL_DRIVERS = ("mysql2", "mysql")


def _sort_engine_hint(
    pg_drivers: set[str], mysql_drivers: set[str], details: list[str], label: str
) -> tuple[str | None, str | None]:
    """Set engine_hint/driver notes from detected driver sets (or None if ambiguous)."""
    if pg_drivers and mysql_drivers:
        details.append(f"Multiple database drivers detected - choose an engine manually ({label})")
        return None, None
    if pg_drivers:
        driver = sorted(pg_drivers)[0].replace("_", "-")
        details.append(f"PostgreSQL driver detected ({driver})")
        return "postgres", driver
    if mysql_drivers:
        driver = sorted(mysql_drivers)[0].replace("_", "-")
        details.append(f"MySQL driver detected ({driver})")
        return "mysql", driver
    return None, None


@dataclass(frozen=True)
class ProjectInfo:
    """Result of project detection."""

    language: str | None = None
    framework: str | None = None
    database_driver: str | None = None
    engine_hint: str | None = None  # "postgres" or "mysql"
    docker_compose: bool = False
    dockerfile: bool = False
    env_file: bool = False
    env_example: bool = False
    env: dict[str, str] = field(default_factory=dict)
    details: list[str] = field(default_factory=list)


def read_env_file(project_dir: str = ".", filename: str = ".env") -> dict[str, str]:
    """Parse a dotenv-style file into a dict of key/value pairs."""
    path = Path(project_dir) / filename
    if not path.exists():
        return {}
    env_vars: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        env_vars[key.strip()] = value.strip().strip('"').strip("'")
    return env_vars


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
) -> tuple[str | None, str | None, str | None, str | None, list[str]]:
    """Detect language/framework/driver from Python project files."""
    language = "Python"
    framework: str | None = None
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

    pg_drivers = all_deps & PG_DRIVERS
    mysql_drivers = all_deps & MYSQL_DRIVERS
    engine_hint, driver_default = _sort_engine_hint(pg_drivers, mysql_drivers, details, "Python")
    driver = driver_default
    if driver_default is None and (pg_drivers or mysql_drivers):
        driver = sorted(pg_drivers | mysql_drivers)[0].replace("_", "-")

    fw_map = {**PG_FRAMEWORKS, **MYSQL_FRAMEWORKS}
    for dep in all_deps:
        if dep in fw_map:
            framework = fw_map[dep]
            details.append(f"{framework} detected")
            break

    return language, framework, driver, engine_hint, details


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

    detected = sorted(all_deps & set(NODE_DRIVERS))
    pg_drivers = set(d for d in detected if d in _NODE_PG_DRIVERS)
    mysql_drivers = set(d for d in detected if d in _NODE_MYSQL_DRIVERS)
    engine_hint, driver_default = _sort_engine_hint(pg_drivers, mysql_drivers, details, "Node.js")
    driver = driver_default
    if driver_default is None and detected:
        driver = NODE_DRIVERS[detected[0]]

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


def _read_composer(project_dir: Path) -> dict[str, Any] | None:
    """Read a composer.json file."""
    import json

    try:
        return dict(json.loads((project_dir / "composer.json").read_text(encoding="utf-8")))
    except Exception:
        return None


def _detect_php_project(
    project_dir: Path,
) -> tuple[str | None, str | None, str | None, str | None, list[str]]:
    """Detect language/framework/driver from PHP (composer.json) files."""
    language = "PHP"
    framework: str | None = None
    details: list[str] = [f"{language} detected"]

    composer = _read_composer(project_dir)
    if composer is None:
        return language, framework, None, None, details

    require = composer.get("require", {})
    dep_names = {str(name).lower() for name in require}

    pg_drivers = dep_names & PHP_PG_DRIVERS
    mysql_drivers = dep_names & PHP_MYSQL_DRIVERS
    engine_hint, driver = _sort_engine_hint(pg_drivers, mysql_drivers, details, "PHP")

    for dep in dep_names:
        if dep in PHP_FRAMEWORKS:
            framework = PHP_FRAMEWORKS[dep]
            details.append(f"{framework} detected")
            break

    return language, framework, driver, engine_hint, details


def _read_gemfile(project_dir: Path) -> set[str]:
    """Parse a Gemfile and return gem names."""
    gemfile = project_dir / "Gemfile"
    if not gemfile.exists():
        return set()
    gems: set[str] = set()
    try:
        for line in gemfile.read_text(encoding="utf-8", errors="ignore").splitlines():
            match = re.search(r'gem\s+["\']([\w.-]+)["\']', line)
            if match:
                gems.add(match.group(1).lower())
    except Exception:
        pass
    return gems


def _detect_ruby_project(
    project_dir: Path,
) -> tuple[str | None, str | None, str | None, str | None, list[str]]:
    """Detect language/framework/driver from Ruby (Gemfile) files."""
    language = "Ruby"
    framework: str | None = None
    details: list[str] = [f"{language} detected"]

    gems = _read_gemfile(project_dir)
    if not gems:
        return language, framework, None, None, details

    pg_drivers = {g for g in gems if g in RUBY_PG_DRIVERS}
    mysql_drivers = {g for g in gems if g in RUBY_MYSQL_DRIVERS}
    engine_hint, driver = _sort_engine_hint(pg_drivers, mysql_drivers, details, "Ruby")

    for gem in gems:
        if gem in RUBY_FRAMEWORKS:
            framework = RUBY_FRAMEWORKS[gem]
            details.append(f"{framework} detected")
            break

    return language, framework, driver, engine_hint, details


def _read_pom_coords(pom_path: Path) -> list[tuple[str, str]]:
    """Return (groupId, artifactId) pairs found in a Maven pom.xml."""
    import xml.etree.ElementTree as ET

    def localname(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]

    coords: list[tuple[str, str]] = []
    try:
        root = ET.fromstring(pom_path.read_text(encoding="utf-8"))
        for dependency in root.iter():
            if localname(dependency.tag) != "dependency":
                continue
            fields = {localname(child.tag): (child.text or "").strip() for child in dependency}
            group, artifact = fields.get("groupId", ""), fields.get("artifactId", "")
            if group and artifact:
                coords.append((group, artifact))
    except (ET.ParseError, OSError):
        pass
    return coords


def _read_gradle_coords(path: Path) -> list[tuple[str, str]]:
    """Return (groupId, artifactId) pairs found in a Gradle build file."""
    coords: list[tuple[str, str]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return coords
    for match in _GRADLE_COORD_RE.finditer(text):
        group, artifact = match.group(1).strip(), match.group(2).strip()
        if group and artifact:
            coords.append((group, artifact))
    return coords


def _detect_java_project(
    project_dir: Path,
) -> tuple[str | None, str | None, str | None, str | None, list[str]]:
    """Detect language/framework/driver from Java (Maven/Gradle) files."""
    language = "Java"
    framework: str | None = None
    details: list[str] = [f"{language} detected"]

    coords: list[tuple[str, str]] = list(_read_pom_coords(project_dir / "pom.xml"))
    for filename in ("build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts"):
        coords.extend(_read_gradle_coords(project_dir / filename))

    artifacts = {artifact.lower() for _, artifact in coords}
    pg_drivers = artifacts & JAVA_PG_ARTIFACTS
    mysql_drivers = artifacts & JAVA_MYSQL_ARTIFACTS
    engine_hint, driver = _sort_engine_hint(pg_drivers, mysql_drivers, details, "Java")

    for marker, label in JAVA_FRAMEWORK_MARKERS:
        if any(marker in artifact for artifact in artifacts):
            framework = label
            details.append(f"{label} detected")
            break

    return language, framework, driver, engine_hint, details


def _read_csproj_packages(csproj: Path) -> set[str]:
    """Return package names referenced by a .csproj file."""
    import xml.etree.ElementTree as ET

    def localname(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]

    packages: set[str] = set()
    try:
        root = ET.fromstring(csproj.read_text(encoding="utf-8"))
        for element in root.iter():
            if localname(element.tag) != "PackageReference":
                continue
            include = element.attrib.get("Include") or element.attrib.get("Update") or ""
            if include:
                packages.add(include.strip())
    except (ET.ParseError, OSError):
        pass
    return packages


def _shallow_glob(project_dir: Path, pattern: str) -> list[Path]:
    """Match *pattern* at the root and up to two levels deep, skipping hidden dirs."""
    matches = list(project_dir.glob(pattern))
    for subdir in project_dir.iterdir():
        if not (subdir.is_dir() and not subdir.name.startswith(".")):
            continue
        matches.extend(subdir.glob(pattern))
        for nested in subdir.iterdir():
            if nested.is_dir() and not nested.name.startswith("."):
                matches.extend(nested.glob(pattern))
    return matches


def _detect_dotnet_project(
    project_dir: Path,
) -> tuple[str | None, str | None, str | None, str | None, list[str]]:
    """Detect language/framework/driver from .NET (csproj/sln) files."""
    language = ".NET"
    framework: str | None = None
    details: list[str] = [f"{language} detected"]

    packages: set[str] = set()
    web_sdk = False
    for csproj in _shallow_glob(project_dir, "*.csproj"):
        packages |= _read_csproj_packages(csproj)
        try:
            if 'Sdk="Microsoft.NET.Sdk.Web"' in csproj.read_text(
                encoding="utf-8", errors="ignore"
            ):
                web_sdk = True
        except OSError:
            pass

    lower = {package.lower() for package in packages}
    pg_drivers = lower & DOTNET_PG_PACKAGES
    mysql_drivers = lower & DOTNET_MYSQL_PACKAGES
    engine_hint, driver = _sort_engine_hint(pg_drivers, mysql_drivers, details, ".NET")

    if web_sdk or any("microsoft.aspnetcore" in package for package in lower):
        framework = "ASP.NET Core"
        details.append("ASP.NET Core detected")
    if any("entityframeworkcore" in package for package in lower):
        details.append("Entity Framework Core detected")

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
    dockerfile = (project_dir / "Dockerfile").exists() or (project_dir / "dockerfile").exists()
    env_file = (project_dir / ".env").exists()
    env_example = (project_dir / ".env.example").exists()

    if docker_compose:
        details.append("docker-compose.yml detected")
    if dockerfile:
        details.append("Dockerfile detected")
    if env_file:
        details.append(".env file detected")
    if env_example:
        details.append(".env.example detected")

    env_vars = read_env_file(path)
    if not env_vars and env_example:
        env_vars = read_env_file(path, filename=".env.example")
    if "DATABASE_URL" in env_vars:
        details.append("DATABASE_URL detected")

    has_pyproject = (project_dir / "pyproject.toml").exists()
    has_requirements = (project_dir / "requirements.txt").exists()
    has_package_json = (project_dir / "package.json").exists()
    has_composer = (project_dir / "composer.json").exists()
    has_gemfile = (project_dir / "Gemfile").exists()
    has_java = (project_dir / "pom.xml").exists() or any(
        (project_dir / name).exists()
        for name in ("build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts")
    )
    has_dotnet = any(_shallow_glob(project_dir, "*.csproj")) or any(
        _shallow_glob(project_dir, "*.sln")
    )

    if has_pyproject or has_requirements:
        language, framework, driver, engine_hint, py_details = _detect_python_project(project_dir)
        details.extend(py_details)

    elif has_java:
        language, framework, driver, engine_hint, java_details = _detect_java_project(project_dir)
        details.extend(java_details)

    elif has_dotnet:
        language, framework, driver, engine_hint, dotnet_details = _detect_dotnet_project(
            project_dir
        )
        details.extend(dotnet_details)

    elif has_gemfile:
        language, framework, driver, engine_hint, ruby_details = _detect_ruby_project(project_dir)
        details.extend(ruby_details)

    elif has_composer or (project_dir / "composer.lock").exists():
        language, framework, driver, engine_hint, php_details = _detect_php_project(project_dir)
        details.extend(php_details)

    elif has_package_json:
        language, framework, driver, engine_hint, node_details = _detect_node_project(project_dir)
        details.extend(node_details)

    # Fall back to the engine implied by DATABASE_URL when no driver hints it.
    if engine_hint is None:
        url = env_vars.get("DATABASE_URL", "")
        if url.startswith("mysql://"):
            engine_hint = "mysql"
        elif url.startswith("postgres"):
            engine_hint = "postgres"

    return ProjectInfo(
        language=language,
        framework=framework,
        database_driver=driver,
        engine_hint=engine_hint,
        docker_compose=docker_compose,
        dockerfile=dockerfile,
        env_file=env_file,
        env_example=env_example,
        env=env_vars,
        details=details,
    )
