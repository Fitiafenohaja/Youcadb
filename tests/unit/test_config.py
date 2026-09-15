"""Tests for the config module."""

from __future__ import annotations

from youcadb.config import (
    DBConfig,
    YoucaDBConfig,
    detect_env_password_in_git,
    generate_env_content,
    load_config,
    save_config,
)


def test_save_and_load_config(tmp_path) -> None:
    cfg = YoucaDBConfig(
        project_name="testproject",
        database=DBConfig(
            engine="postgres",
            host="localhost",
            port=5432,
            name="testdb",
            user="admin",
            password="secret",
        ),
    )
    save_config(cfg, str(tmp_path))
    loaded = load_config(str(tmp_path))
    assert loaded is not None
    assert loaded.project_name == "testproject"
    assert loaded.database.engine == "postgres"
    assert loaded.database.name == "testdb"
    assert loaded.database.password == "secret"


def test_load_config_missing(tmp_path) -> None:
    assert load_config(str(tmp_path)) is None


def test_database_url_with_password(tmp_path) -> None:
    cfg = YoucaDBConfig(
        database=DBConfig(
            engine="postgres",
            host="localhost",
            port=5432,
            name="mydb",
            user="admin",
            password="pass",
        )
    )
    assert cfg.database.database_url == "postgresql://admin:pass@localhost:5432/mydb"


def test_database_url_no_password(tmp_path) -> None:
    cfg = YoucaDBConfig(
        database=DBConfig(engine="mysql", host="db.local", port=3306, name="prod", user="root")
    )
    assert cfg.database.database_url == "mysql://root@db.local:3306/prod"


def test_generate_env_content() -> None:
    cfg = YoucaDBConfig(
        database=DBConfig(
            engine="postgres",
            host="localhost",
            port=5432,
            name="mydb",
            user="admin",
            password="secret",
        )
    )
    content = generate_env_content(cfg)
    assert "DATABASE_URL=postgresql://admin:secret@localhost:5432/mydb" in content
    assert "DB_HOST=localhost" in content
    assert "DB_PORT=5432" in content


def test_config_to_dict_and_from_dict() -> None:
    cfg = YoucaDBConfig(
        project_name="p",
        database=DBConfig(engine="mysql", host="h", port=3306, name="n", user="u", password="pw"),
    )
    d = cfg.to_dict()
    restored = YoucaDBConfig.from_dict(d)
    assert restored.project_name == "p"
    assert restored.database.engine == "mysql"
    assert restored.database.password == "pw"


def test_detect_env_password_in_git_no_env(tmp_path) -> None:
    warnings = detect_env_password_in_git(str(tmp_path))
    assert warnings == []


def test_detect_env_password_not_tracked(tmp_path) -> None:
    (tmp_path / ".env").write_text("DB_PASSWORD=abc\n")
    import subprocess

    subprocess.run(["git", "init"], cwd=str(tmp_path), check=True, capture_output=True)
    warnings = detect_env_password_in_git(str(tmp_path))
    assert warnings == []


def test_config_file_content(tmp_path) -> None:
    cfg = YoucaDBConfig(
        project_name="x",
        database=DBConfig(engine="postgres", name="x", user="postgres"),
    )
    save_config(cfg, str(tmp_path))
    content = (tmp_path / ".youcadb.toml").read_text()
    assert "[database]" in content
    assert 'engine = "postgres"' in content
