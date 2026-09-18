"""MySQL engine implementation."""

from __future__ import annotations

from typing import Any

from youcadb.engines.base import ConnectionResult, Engine, OperationResult


def _validate_identifier(name: str) -> None:
    """Ensure a name is safe to embed in a backtick-quoted identifier."""
    if not name or len(name) > 64 or any(c in name for c in ("`", ";", "\\", "'", '"')):
        raise ValueError(f"Invalid database identifier: {name!r}")


class MySQLEngine(Engine):
    """MySQL engine backed by *pymysql*."""

    @property
    def name(self) -> str:
        return "MySQL"

    @property
    def scheme(self) -> str:
        return "mysql"

    @property
    def default_port(self) -> int:
        return 3306

    def is_available(self) -> bool:
        try:
            import pymysql  # noqa: F401

            return True
        except ImportError:
            return False

    def connect(
        self,
        host: str = "localhost",
        port: int | None = None,
        user: str = "root",
        password: str = "",
        database: str = "",
    ) -> ConnectionResult:
        try:
            import pymysql

            effective_port = port or self.default_port
            conn = pymysql.connect(
                host=host,
                port=effective_port,
                user=user,
                password=password,
                database=database or None,
                connect_timeout=5,
            )
            version = conn.get_server_info()  # type: ignore[no-untyped-call]
            conn.close()
            return ConnectionResult(
                success=True,
                message=f"Connected to MySQL {version}",
                server_version=version,
            )
        except ImportError:
            return ConnectionResult(success=False, message="pymysql driver not installed")
        except Exception as exc:
            return ConnectionResult(success=False, message=f"Connection failed: {exc}")

    def create_database(self, database_name: str, **kwargs: Any) -> OperationResult:
        try:
            _validate_identifier(database_name)
        except ValueError as exc:
            return OperationResult(success=False, message=str(exc))

        host = kwargs.get("host", "localhost")
        port = kwargs.get("port", self.default_port)
        user = kwargs.get("user", "root")
        password = kwargs.get("password", "")

        try:
            import pymysql

            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                connect_timeout=5,
            )
            with conn.cursor() as cur:
                cur.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}`")
            conn.close()
            return OperationResult(success=True, message=f"Database '{database_name}' created")
        except ImportError:
            return OperationResult(success=False, message="pymysql driver not installed")
        except Exception as exc:
            return OperationResult(success=False, message=f"Failed to create database: {exc}")

    def drop_database(self, database_name: str, **kwargs: Any) -> OperationResult:
        try:
            _validate_identifier(database_name)
        except ValueError as exc:
            return OperationResult(success=False, message=str(exc))

        host = kwargs.get("host", "localhost")
        port = kwargs.get("port", self.default_port)
        user = kwargs.get("user", "root")
        password = kwargs.get("password", "")

        try:
            import pymysql

            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                connect_timeout=5,
            )
            with conn.cursor() as cur:
                cur.execute(f"DROP DATABASE IF EXISTS `{database_name}`")
            conn.close()
            return OperationResult(success=True, message=f"Database '{database_name}' dropped")
        except ImportError:
            return OperationResult(success=False, message="pymysql driver not installed")
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
            _validate_identifier(user_host)
            if database:
                _validate_identifier(database)
        except ValueError as exc:
            return OperationResult(success=False, message=str(exc))

        admin_user = admin_user or "root"
        conn_port = port or self.default_port

        try:
            import pymysql

            conn = pymysql.connect(
                host=host,
                port=conn_port,
                user=admin_user,
                password=admin_password,
                connect_timeout=5,
            )
            with conn.cursor() as cur:
                cur.execute(
                    "CREATE USER IF NOT EXISTS %s@%s IDENTIFIED BY %s",
                    (username, user_host, password),
                )
                if database:
                    cur.execute(
                        f"GRANT ALL PRIVILEGES ON `{database}`.* TO %s@%s",
                        (username, user_host),
                    )
                    cur.execute("FLUSH PRIVILEGES")
            conn.close()
            return OperationResult(
                success=True,
                message=f"User '{username}'@'{user_host}' created",
            )
        except ImportError:
            return OperationResult(success=False, message="pymysql driver not installed")
        except Exception as exc:
            return OperationResult(success=False, message=f"Failed to create user: {exc}")

    def test_connection(
        self,
        host: str = "localhost",
        port: int | None = None,
        user: str = "root",
        password: str = "",
        database: str = "",
    ) -> ConnectionResult:
        return self.connect(host=host, port=port, user=user, password=password, database=database)
