"""PostgreSQL engine implementation."""

from __future__ import annotations

from typing import Any

from youcadb.engines.base import ConnectionResult, Engine, OperationResult


def _validate_identifier(name: str) -> None:
    """Ensure a name is safe to embed in a quoted identifier."""
    if not name or len(name) > 63 or any(c in name for c in ('"', "'", ";", "\\")):
        raise ValueError(f"Invalid database identifier: {name!r}")


class PostgresEngine(Engine):
    """PostgreSQL engine backed by *psycopg*."""

    @property
    def name(self) -> str:
        return "PostgreSQL"

    @property
    def scheme(self) -> str:
        return "postgresql"

    @property
    def default_port(self) -> int:
        return 5432

    def is_available(self) -> bool:
        try:
            import psycopg  # noqa: F401

            return True
        except ImportError:
            return False

    def connect(
        self,
        host: str = "localhost",
        port: int | None = None,
        user: str = "postgres",
        password: str = "",
        database: str = "postgres",
    ) -> ConnectionResult:
        try:
            import psycopg

            effective_port = port or self.default_port
            conn = psycopg.connect(
                host=host,
                port=effective_port,
                user=user,
                password=password,
                dbname=database,
                connect_timeout=5,
            )
            version = conn.info.server_version
            conn.close()
            return ConnectionResult(
                success=True,
                message=f"Connected to PostgreSQL {version}",
                server_version=str(version),
            )
        except ImportError:
            return ConnectionResult(success=False, message="psycopg driver not installed")
        except Exception as exc:
            return ConnectionResult(success=False, message=f"Connection failed: {exc}")

    def create_database(self, database_name: str, **kwargs: Any) -> OperationResult:
        try:
            _validate_identifier(database_name)
        except ValueError as exc:
            return OperationResult(success=False, message=str(exc))

        host = kwargs.get("host", "localhost")
        port = kwargs.get("port", self.default_port)
        user = kwargs.get("user", "postgres")
        password = kwargs.get("password", "")

        try:
            import psycopg

            conn = psycopg.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                dbname="postgres",
                connect_timeout=5,
            )
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
                if cur.fetchone() is None:
                    cur.execute(f'CREATE DATABASE "{database_name}"')
            conn.close()
            return OperationResult(success=True, message=f"Database '{database_name}' created")
        except ImportError:
            return OperationResult(success=False, message="psycopg driver not installed")
        except Exception as exc:
            return OperationResult(success=False, message=f"Failed to create database: {exc}")

    def drop_database(self, database_name: str, **kwargs: Any) -> OperationResult:
        try:
            _validate_identifier(database_name)
        except ValueError as exc:
            return OperationResult(success=False, message=str(exc))

        host = kwargs.get("host", "localhost")
        port = kwargs.get("port", self.default_port)
        user = kwargs.get("user", "postgres")
        password = kwargs.get("password", "")

        try:
            import psycopg

            conn = psycopg.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                dbname="postgres",
                connect_timeout=5,
            )
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity"
                    " WHERE datname = %s AND pid <> pg_backend_pid()",
                    (database_name,),
                )
                cur.execute(f'DROP DATABASE IF EXISTS "{database_name}"')
            conn.close()
            return OperationResult(success=True, message=f"Database '{database_name}' dropped")
        except ImportError:
            return OperationResult(success=False, message="psycopg driver not installed")
        except Exception as exc:
            return OperationResult(success=False, message=f"Failed to drop database: {exc}")

    def create_user(
        self,
        username: str,
        password: str,
        host: str = "localhost",
        database: str | None = None,
        admin_user: str = "",
        admin_password: str = "",
        port: int | None = None,
        user_host: str = "%",
    ) -> OperationResult:
        try:
            _validate_identifier(username)
            if database:
                _validate_identifier(database)
        except ValueError as exc:
            return OperationResult(success=False, message=str(exc))

        admin_user = admin_user or "postgres"
        conn_port = port or self.default_port

        try:
            import psycopg

            conn = psycopg.connect(
                host=host,
                port=conn_port,
                user=admin_user,
                password=admin_password,
                dbname="postgres",
                connect_timeout=5,
            )
            conn.autocommit = True
            with conn.cursor() as cur:
                escaped_password = password.replace("'", "''")
                cur.execute(
                    "SELECT 1 FROM pg_roles WHERE rolname = %s",
                    (username,),
                )
                role_exists = cur.fetchone() is not None
                if role_exists:
                    cur.execute(f"ALTER ROLE \"{username}\" WITH PASSWORD '{escaped_password}'")
                else:
                    cur.execute(
                        f"CREATE ROLE \"{username}\" WITH LOGIN PASSWORD '{escaped_password}'"
                    )
                if database:
                    cur.execute(f'GRANT ALL PRIVILEGES ON DATABASE "{database}" TO "{username}"')
                    cur.execute(f'ALTER DATABASE "{database}" OWNER TO "{username}"')
            conn.close()
            return OperationResult(success=True, message=f"User '{username}' created")
        except ImportError:
            return OperationResult(success=False, message="psycopg driver not installed")
        except Exception as exc:
            return OperationResult(success=False, message=f"Failed to create user: {exc}")

    def test_connection(
        self,
        host: str = "localhost",
        port: int | None = None,
        user: str = "postgres",
        password: str = "",
        database: str = "postgres",
    ) -> ConnectionResult:
        return self.connect(host=host, port=port, user=user, password=password, database=database)
