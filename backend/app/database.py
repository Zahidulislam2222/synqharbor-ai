"""Database connections and explicit, frozen, additive Alembic migrations."""
from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Connection, Engine, MetaData, create_engine, event, inspect, text
from sqlalchemy.pool import StaticPool

from .models import Base
from .settings import Settings


def make_engine(settings: Settings, *, migration: bool = False) -> Engine:
    configured = settings.migration_database_url if migration and settings.migration_database_url else settings.database_url
    url = configured.get_secret_value()
    if url.startswith("sqlite"):
        connection_args = {"check_same_thread": False, "timeout": settings.sqlite_timeout}
        if url in {"sqlite://", "sqlite:///:memory:"}:
            engine = create_engine(url, connect_args=connection_args, poolclass=StaticPool, hide_parameters=True)
        else:
            engine = create_engine(url, connect_args=connection_args, hide_parameters=True)

        @event.listens_for(engine, "connect")
        def foreign_keys(connection: object, _: object) -> None:
            connection.cursor().execute("PRAGMA foreign_keys=ON")  # type: ignore[attr-defined]

        return engine
    engine = create_engine(url, hide_parameters=True, pool_pre_ping=True, pool_size=settings.database_pool_size,
                           max_overflow=settings.database_max_overflow,
                           pool_timeout=settings.database_pool_timeout)
    if not migration:
        @event.listens_for(engine, "connect")
        def restricted_role(connection: object, _: object) -> None:
            cursor = connection.cursor()  # type: ignore[attr-defined]
            try:
                cursor.execute("""SELECT rolsuper OR rolbypassrls
                    OR has_schema_privilege(current_user, current_schema(), 'CREATE')
                    OR EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                               WHERE n.nspname=current_schema()
                                 AND pg_has_role(current_user, c.relowner, 'MEMBER'))
                    FROM pg_roles r WHERE rolname=current_user""")
                row = cursor.fetchone()
                if not row or row[0]:
                    raise ValueError("Database runtime role must not own schema/tables or bypass row security")
            finally:
                cursor.close()
                connection.rollback()  # type: ignore[attr-defined]
    return engine


def migration_config() -> Config:
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "migrations"))
    return config


def migrate(engine: Engine) -> None:
    config = migration_config()
    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            # One protocol-wide migration lock; arbitrary runtime jobs cannot migrate.
            connection.execute(text("SELECT pg_advisory_xact_lock(1936220770)"))
        config.attributes["connection"] = connection
        tables = set(inspect(connection).get_table_names())
        if tables and "alembic_version" not in tables:
            # Adopt only the verified legacy baseline. Never stamp an arbitrary or
            # partially created schema as migrated; type/index/FK drift also blocks.
            additions = {"repository_grants", "workspace_execution", "knowledge_sources"}
            baseline = MetaData()
            for table in Base.metadata.sorted_tables:
                if table.name not in additions:
                    table.to_metadata(baseline)
            if tables != set(baseline.tables):
                raise ValueError("Legacy schema drift requires explicit reconciliation before migration")
            if compare_metadata(MigrationContext.configure(connection), baseline):
                raise ValueError("Legacy schema drift requires explicit reconciliation before migration")
            command.stamp(config, "0001")
        command.upgrade(config, "head")
        if compare_metadata(MigrationContext.configure(connection), Base.metadata):
            raise ValueError("Migrated schema differs from the current application contract")


def schema_current(bind: Engine | Connection) -> bool:
    if isinstance(bind, Engine):
        with bind.connect() as connection:
            current = MigrationContext.configure(connection).get_current_heads()
    else:
        current = MigrationContext.configure(bind).get_current_heads()
    return set(current) == set(ScriptDirectory.from_config(migration_config()).get_heads())


if __name__ == "__main__":
    from .settings import get_settings

    engine = make_engine(get_settings(), migration=True)
    try:
        migrate(engine)
    finally:
        engine.dispose()
