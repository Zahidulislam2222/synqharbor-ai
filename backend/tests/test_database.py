"""Frozen migrations preserve data and refuse unknown legacy schemas."""
from typing import Any

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text

from app.database import migrate, migration_config, schema_current
from app.models import Base


def test_migration_baseline_upgrade_is_additive_and_matches_models(tmp_path: Any) -> None:
    engine = create_engine("sqlite:///" + str(tmp_path / "migration.sqlite"))
    config = migration_config()
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "0001")
        connection.execute(text("INSERT INTO users (id,email,name,password_hash,created_at) VALUES (:id,:email,:name,:password,1)"),
                           {"id": "test-user", "email": "test@example.com", "name": "Test", "password": "test-hash"})
    assert not schema_current(engine)
    migrate(engine)
    migrate(engine)
    assert schema_current(engine)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM users")) == 1
        assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
    engine.dispose()


def test_unknown_schema_is_never_stamped_as_migrated() -> None:
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE unrelated (id INTEGER)"))
    with pytest.raises(ValueError, match="Legacy schema drift"):
        migrate(engine)
    assert "alembic_version" not in inspect(engine).get_table_names()
    engine.dispose()
