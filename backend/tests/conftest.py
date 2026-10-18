"""Opt-in PostgreSQL parity gate; credentials stay in an ignored local config."""
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from pydantic import SecretStr
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from app.database import make_engine, migrate
from app.models import Base
from app.settings import Settings


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--database-test-config", help="Private JSON file with dedicated test database URLs")


@pytest.fixture(autouse=True)
def postgres_parity(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    configured = request.config.getoption("--database-test-config")
    if not configured or not {"core", "clients"}.intersection(request.fixturenames):
        yield
        return
    config = json.loads(Path(configured).read_text())
    admin_url, runtime_url = make_url(config["migration_url"]), make_url(config["runtime_url"])
    if (not admin_url.database or not admin_url.database.startswith("synqharbor_test")
            or admin_url.database != runtime_url.database):
        raise ValueError("PostgreSQL parity tests require the same dedicated synqharbor_test database")
    admin = create_engine(admin_url, hide_parameters=True)
    try:
        with admin.begin() as db:
            db.exec_driver_sql("DROP SCHEMA public CASCADE")
            db.exec_driver_sql("CREATE SCHEMA public")
            db.exec_driver_sql("REVOKE ALL ON SCHEMA public FROM PUBLIC")
        migrate(admin)
        role = admin.dialect.identifier_preparer.quote(runtime_url.username or "")
        with admin.begin() as db:
            db.exec_driver_sql("GRANT USAGE ON SCHEMA public TO " + role)
            for table in Base.metadata.sorted_tables:
                quoted = admin.dialect.identifier_preparer.quote(table.name)
                db.exec_driver_sql("GRANT SELECT, INSERT, UPDATE, DELETE ON " + quoted + " TO " + role)
            db.exec_driver_sql("GRANT SELECT ON alembic_version TO " + role)

        def runtime(settings: Settings, **kwargs: Any) -> Any:
            return make_engine(settings.model_copy(update={"database_url": SecretStr(str(runtime_url.render_as_string(hide_password=False)))}), **kwargs)

        monkeypatch.setattr("app.main.make_engine", runtime)
        yield
    finally:
        admin.dispose()
