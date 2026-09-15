"""Configuration model for .youcadb.toml."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:
    import tomli as tomllib

CONFIG_FILE = ".youcadb.toml"


@dataclass
class DBConfig:
    """Database connection configuration."""

    engine: str = "postgres"
    host: str = "localhost"
    port: int = 5432
    name: str = ""
    user: str = ""
    password: str = ""

    @property
    def database_url(self) -> str:
        """Build a DATABASE_URL from the config."""
        scheme = "postgresql" if self.engine == "postgres" else "mysql"
        if self.password:
            return f"{scheme}://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        return f"{scheme}://{self.user}@{self.host}:{self.port}/{self.name}"


@dataclass
class YoucaDBConfig:
    """Full .youcadb.toml configuration."""

    project_name: str = ""
    database: DBConfig = field(default_factory=DBConfig)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dict suitable for TOML dumping."""
        return {
            "project": {"name": self.project_name},
            "database": {
                "engine": self.database.engine,
                "host": self.database.host,
                "port": self.database.port,
                "name": self.database.name,
                "user": self.database.user,
                "password": self.database.password,
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> YoucaDBConfig:
        """Deserialize from a parsed TOML dict."""
        project = data.get("project", {})
        db = data.get("database", {})
        return cls(
            project_name=project.get("name", ""),
            database=DBConfig(
                engine=db.get("engine", "postgres"),
                host=db.get("host", "localhost"),
                port=db.get("port", 5432),
                name=db.get("name", ""),
                user=db.get("user", ""),
                password=db.get("password", ""),
            ),
        )


def load_config(path: str = ".") -> YoucaDBConfig | None:
    """Load .youcadb.toml from the given directory. Returns None if not found."""
    config_path = Path(path) / CONFIG_FILE
    if not config_path.exists():
        return None
    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
        return YoucaDBConfig.from_dict(data)
    except Exception:
        return None


def save_config(config: YoucaDBConfig, path: str = ".") -> None:
    """Write .youcadb.toml to the given directory."""
    config_path = Path(path) / CONFIG_FILE
    lines = ["# YoucaDB configuration", ""]
    lines.append("[project]")
    lines.append(f'  name = "{config.project_name}"')
    lines.append("")
    lines.append("[database]")
    lines.append(f'  engine = "{config.database.engine}"')
    lines.append(f'  host = "{config.database.host}"')
    lines.append(f"  port = {config.database.port}")
    lines.append(f'  name = "{config.database.name}"')
    lines.append(f'  user = "{config.database.user}"')
    if config.database.password:
        lines.append(f'  password = "{config.database.password}"')
    lines.append("")
    config_path.write_text("\n".join(lines), encoding="utf-8")


def generate_env_content(config: YoucaDBConfig) -> str:
    """Generate .env file content from a YoucaDBConfig."""
    db = config.database
    scheme = "postgresql" if db.engine == "postgres" else "mysql"

    lines = [
        f"DATABASE_URL={scheme}://{db.user}:{db.password}@{db.host}:{db.port}/{db.name}",
        "",
        f"DB_HOST={db.host}",
        f"DB_PORT={db.port}",
        f"DB_NAME={db.name}",
        f"DB_USER={db.user}",
        f"DB_PASSWORD={db.password}",
        "",
    ]
    return "\n".join(lines)


def detect_env_password_in_git(project_dir: str = ".") -> list[str]:
    """Check if .env files with passwords are tracked by git."""
    warnings: list[str] = []
    env_path = Path(project_dir) / ".env"
    if not env_path.exists():
        return warnings

    try:
        import subprocess

        result = subprocess.run(
            ["git", "ls-files", ".env"],
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            content = env_path.read_text(encoding="utf-8", errors="ignore")
            for line in content.splitlines():
                if "PASSWORD" in line.upper() and "=" in line:
                    value = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if value:
                        warnings.append(
                            f".env is tracked by git and contains a password"
                            f" (line: {line.split('=')[0]}=***)"
                        )
                        break
    except Exception:
        pass

    return warnings


def check_bind_address(project_dir: str = ".") -> list[str]:
    """Check if the database is configured to bind on 0.0.0.0."""
    warnings: list[str] = []
    env_path = Path(project_dir) / ".env"
    if env_path.exists():
        content = env_path.read_text(encoding="utf-8", errors="ignore")
        for line in content.splitlines():
            stripped = line.strip()
            if (
                stripped.startswith("DB_HOST=")
                or stripped.startswith("POSTGRES_HOST=")
                or stripped.startswith("MYSQL_HOST=")
            ):
                value = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                if value == "0.0.0.0":
                    warnings.append(
                        f"Database host is set to 0.0.0.0 in .env ({stripped.split('=')[0]})"
                    )
    return warnings
