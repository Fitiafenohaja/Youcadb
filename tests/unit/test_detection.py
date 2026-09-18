"""Tests for detection modules."""

from __future__ import annotations

from youcadb.detection.project import ProjectInfo, detect_project
from youcadb.detection.system import SystemInfo, detect_system


def test_detect_project_returns_project_info() -> None:
    result = detect_project()
    assert isinstance(result, ProjectInfo)


def test_detect_system_returns_system_info() -> None:
    result = detect_system()
    assert isinstance(result, SystemInfo)
    assert result.os_name
    assert result.python_version


def test_detect_project_empty_dir(tmp_path) -> None:
    result = detect_project(str(tmp_path))
    assert result.language is None
    assert result.framework is None
    assert result.database_driver is None
    assert result.details == []


def test_detect_python_project(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "test"\ndependencies = ["fastapi", "psycopg[binary]"]\n'
    )
    result = detect_project(str(tmp_path))
    assert result.language == "Python"
    assert "psycopg" in (result.database_driver or "").lower()
    assert result.engine_hint == "postgres"


def test_detect_python_mysql(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "test"\ndependencies = ["flask", "pymysql"]\n'
    )
    result = detect_project(str(tmp_path))
    assert result.language == "Python"
    assert result.engine_hint == "mysql"


def test_detect_node_project(tmp_path) -> None:
    import json

    pkg = {"dependencies": {"express": "^4", "pg": "^8"}}
    (tmp_path / "package.json").write_text(json.dumps(pkg))
    result = detect_project(str(tmp_path))
    assert result.language == "Node.js"
    assert result.engine_hint == "postgres"
    assert "Express" in (result.framework or "")


def test_detect_node_mysql(tmp_path) -> None:
    import json

    pkg = {"dependencies": {"mysql2": "^3"}}
    (tmp_path / "package.json").write_text(json.dumps(pkg))
    result = detect_project(str(tmp_path))
    assert result.language == "Node.js"
    assert result.engine_hint == "mysql"


def test_detect_docker_compose(tmp_path) -> None:
    (tmp_path / "docker-compose.yml").write_text("services:\n  db:\n")
    result = detect_project(str(tmp_path))
    assert result.docker_compose is True


def test_detect_env_file(tmp_path) -> None:
    (tmp_path / ".env").write_text("DB_HOST=localhost\n")
    result = detect_project(str(tmp_path))
    assert result.env_file is True


def test_detect_requirements_txt(tmp_path) -> None:
    (tmp_path / "requirements.txt").write_text("fastapi\nasyncpg\n")
    result = detect_project(str(tmp_path))
    assert result.language == "Python"
    assert result.engine_hint == "postgres"


def test_detect_python_multiple_drivers_ambiguous(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "t"\ndependencies = ["psycopg[binary]", "pymysql"]\n'
    )
    result = detect_project(str(tmp_path))
    assert result.engine_hint is None
    assert any("Multiple database drivers" in d for d in result.details)


def test_detect_node_multiple_drivers_ambiguous(tmp_path) -> None:
    import json

    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"pg": "^8", "mysql2": "^3"}})
    )
    result = detect_project(str(tmp_path))
    assert result.engine_hint is None


def test_detect_dockerfile(tmp_path) -> None:
    (tmp_path / "Dockerfile").write_text("FROM python:3.12\n")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "t"\ndependencies = []\n')
    result = detect_project(str(tmp_path))
    assert result.dockerfile is True
    assert any("Dockerfile detected" in d for d in result.details)


def test_detect_env_values_and_engine_from_url(tmp_path) -> None:
    (tmp_path / ".env").write_text(
        "DATABASE_URL=postgresql://alice:pw@dbhost:5433/appdb\nDB_HOST=dbhost\nDB_USER=alice\n"
    )
    result = detect_project(str(tmp_path))
    assert result.engine_hint == "postgres"
    assert result.env["DB_USER"] == "alice"
    assert result.env["DATABASE_URL"].startswith("postgresql://")
    assert any("DATABASE_URL detected" in d for d in result.details)


def test_detect_mysql_url_takes_precedence(tmp_path) -> None:
    (tmp_path / ".env.example").write_text("DATABASE_URL=mysql://root:pw@localhost:3306/app\n")
    result = detect_project(str(tmp_path))
    assert result.engine_hint == "mysql"


def test_detect_php_laravel_mysql(tmp_path) -> None:
    import json

    (tmp_path / "composer.json").write_text(
        json.dumps({"require": {"laravel/framework": "^10", "ext-pdo_mysql": "*"}})
    )
    result = detect_project(str(tmp_path))
    assert result.language == "PHP"
    assert "Laravel" in (result.framework or "")
    assert result.engine_hint == "mysql"


def test_detect_php_pgsql(tmp_path) -> None:
    import json

    (tmp_path / "composer.json").write_text(
        json.dumps({"require": {"ext-pdo_pgsql": "*", "symfony/symfony": "^6"}})
    )
    result = detect_project(str(tmp_path))
    assert result.language == "PHP"
    assert result.engine_hint == "postgres"


def test_detect_ruby_rails_pg(tmp_path) -> None:
    (tmp_path / "Gemfile").write_text(
        'source "https://rubygems.org"\ngem "rails", "~> 7.0"\ngem "pg"\n'
    )
    result = detect_project(str(tmp_path))
    assert result.language == "Ruby"
    assert "Ruby on Rails" in (result.framework or "")
    assert result.engine_hint == "postgres"


def test_detect_ruby_mysql2(tmp_path) -> None:
    (tmp_path / "Gemfile").write_text(
        'source "https://rubygems.org"\ngem "mysql2"\ngem "sinatra"\n'
    )
    result = detect_project(str(tmp_path))
    assert result.language == "Ruby"
    assert result.engine_hint == "mysql"


def test_detect_node_express_mysql(tmp_path) -> None:
    import json

    pkg = {"dependencies": {"express": "^4", "mysql": "^2"}}
    (tmp_path / "package.json").write_text(json.dumps(pkg))
    result = detect_project(str(tmp_path))
    assert result.language == "Node.js"
    assert "Express" in (result.framework or "")
    assert result.engine_hint == "mysql"


def test_detect_php_multiple_drivers_ambiguous(tmp_path) -> None:
    import json

    (tmp_path / "composer.json").write_text(
        json.dumps({"require": {"ext-pdo_pgsql": "*", "ext-pdo_mysql": "*"}})
    )
    result = detect_project(str(tmp_path))
    assert result.language == "PHP"
    assert result.engine_hint is None


def test_detect_java_maven_spring_postgres(tmp_path) -> None:
    (tmp_path / "pom.xml").write_text(
        """<?xml version="1.0"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <groupId>com.example</groupId>
  <artifactId>demo</artifactId>
  <dependencies>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
      <groupId>org.postgresql</groupId>
      <artifactId>postgresql</artifactId>
    </dependency>
  </dependencies>
</project>
"""
    )
    result = detect_project(str(tmp_path))
    assert result.language == "Java"
    assert "Spring Boot" in (result.framework or "")
    assert result.engine_hint == "postgres"
    assert result.database_driver == "postgresql"


def test_detect_java_gradle_spring_mysql(tmp_path) -> None:
    (tmp_path / "build.gradle.kts").write_text(
        "dependencies {\n"
        '  implementation("org.springframework.boot:spring-boot-starter-data-jpa")\n'
        '  runtimeOnly("com.mysql:mysql-connector-j")\n'
        "}\n"
    )
    result = detect_project(str(tmp_path))
    assert result.language == "Java"
    assert "Spring Boot" in (result.framework or "")
    assert result.engine_hint == "mysql"


def test_detect_java_multiple_drivers_ambiguous(tmp_path) -> None:
    (tmp_path / "pom.xml").write_text(
        """<project>
  <dependencies>
    <dependency><groupId>org.postgresql</groupId><artifactId>postgresql</artifactId></dependency>
    <dependency><groupId>com.mysql</groupId><artifactId>mysql-connector-j</artifactId></dependency>
  </dependencies>
</project>
"""
    )
    result = detect_project(str(tmp_path))
    assert result.language == "Java"
    assert result.engine_hint is None
    assert any("Multiple database drivers" in d for d in result.details)


def test_detect_dotnet_aspnet_npgsql(tmp_path) -> None:
    (tmp_path / "App.csproj").write_text(
        """<Project Sdk="Microsoft.NET.Sdk.Web">
  <ItemGroup>
    <PackageReference Include="Microsoft.AspNetCore.Mvc" Version="8.0.0" />
    <PackageReference Include="Npgsql.EntityFrameworkCore.PostgreSQL" Version="8.0.1" />
  </ItemGroup>
</Project>
"""
    )
    result = detect_project(str(tmp_path))
    assert result.language == ".NET"
    assert "ASP.NET Core" in (result.framework or "")
    assert result.engine_hint == "postgres"
    assert any("Entity Framework Core" in d for d in result.details)


def test_detect_dotnet_mysql_pomelo(tmp_path) -> None:
    (tmp_path / "App.csproj").write_text(
        """<Project Sdk="Microsoft.NET.Sdk">
  <ItemGroup>
    <PackageReference Include="Pomelo.EntityFrameworkCore.MySql" Version="8.0.0" />
  </ItemGroup>
</Project>
"""
    )
    result = detect_project(str(tmp_path))
    assert result.language == ".NET"
    assert result.engine_hint == "mysql"
    assert any("Entity Framework Core" in d for d in result.details)


def test_detect_dotnet_sln_only(tmp_path) -> None:
    (tmp_path / "App.sln").write_text("Microsoft Visual Studio Solution File\n")
    result = detect_project(str(tmp_path))
    assert result.language == ".NET"
    assert result.engine_hint is None


def test_detect_ruby_multiple_drivers_ambiguous(tmp_path) -> None:
    (tmp_path / "Gemfile").write_text(
        'source "https://rubygems.org"\ngem "pg"\ngem "mysql2"\ngem "rails"\n'
    )
    result = detect_project(str(tmp_path))
    assert result.language == "Ruby"
    assert result.engine_hint is None
    assert any("Multiple database drivers" in d for d in result.details)


def test_detect_node_psql_and_postgres_drivers(tmp_path) -> None:
    import json

    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"psql": "^3", "postgres": "^2"}})
    )
    result = detect_project(str(tmp_path))
    assert result.language == "Node.js"
    assert result.engine_hint == "postgres"


def test_detect_dotnet_aspnet_without_web_sdk(tmp_path) -> None:
    (tmp_path / "App.csproj").write_text(
        """<Project Sdk="Microsoft.NET.Sdk">
  <ItemGroup>
    <PackageReference Include="Microsoft.AspNetCore.Mvc" Version="8.0.0" />
    <PackageReference Include="Npgsql" Version="8.0.1" />
  </ItemGroup>
</Project>
"""
    )
    result = detect_project(str(tmp_path))
    assert result.language == ".NET"
    assert "ASP.NET Core" in (result.framework or "")
    assert result.engine_hint == "postgres"


def test_detect_java_gradle_postgres(tmp_path) -> None:
    (tmp_path / "build.gradle").write_text(
        "dependencies {\n    implementation 'org.postgresql:postgresql'\n}\n"
    )
    result = detect_project(str(tmp_path))
    assert result.language == "Java"
    assert result.engine_hint == "postgres"
    assert result.database_driver == "postgresql"


def test_detect_priority_java_beats_node(tmp_path) -> None:
    import json

    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"express": "^4", "pg": "^8"}})
    )
    (tmp_path / "pom.xml").write_text(
        """<project>
  <dependencies>
    <dependency><groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-web</artifactId></dependency>
    <dependency><groupId>org.postgresql</groupId><artifactId>postgresql</artifactId></dependency>
  </dependencies>
</project>
"""
    )
    result = detect_project(str(tmp_path))
    assert result.language == "Java"
    assert result.engine_hint == "postgres"


def test_detect_priority_ruby_beats_node(tmp_path) -> None:
    import json

    (tmp_path / "package.json").write_text(json.dumps({"dependencies": {"mysql2": "^3"}}))
    (tmp_path / "Gemfile").write_text('source "https://rubygems.org"\ngem "rails"\ngem "pg"\n')
    result = detect_project(str(tmp_path))
    assert result.language == "Ruby"
    assert result.engine_hint == "postgres"


def test_detect_priority_python_beats_all(tmp_path) -> None:
    import json

    (tmp_path / "package.json").write_text(json.dumps({"dependencies": {"express": "^4"}}))
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "t"\ndependencies = []\n')
    result = detect_project(str(tmp_path))
    assert result.language == "Python"


def test_detect_dotnet_project_in_subdirectory(tmp_path) -> None:
    sub = tmp_path / "src" / "App"
    sub.mkdir(parents=True)
    (sub / "App.csproj").write_text(
        """<Project Sdk="Microsoft.NET.Sdk">
  <ItemGroup>
    <PackageReference Include="Npgsql.EntityFrameworkCore.PostgreSQL" Version="8.0.1" />
  </ItemGroup>
</Project>
"""
    )
    result = detect_project(str(tmp_path))
    assert result.language == ".NET"
    assert result.engine_hint == "postgres"


def test_detect_dotnet_sln_in_subdirectory(tmp_path) -> None:
    sub = tmp_path / "sln"
    sub.mkdir()
    (sub / "App.sln").write_text("Microsoft Visual Studio Solution File\n")
    result = detect_project(str(tmp_path))
    assert result.language == ".NET"
