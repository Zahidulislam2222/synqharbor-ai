"""The operator can provision a valid account without enabling public enrollment."""
import sys
from io import StringIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app import manage
from app.database import make_engine, migrate
from app.main import create_app
from app.settings import Settings


def test_operator_account_login_while_registration_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(_env_file=None, database_url=SecretStr("sqlite:///" + str(tmp_path / "accounts.sqlite")),
                        session_secret=SecretStr("test-key" * 8), public_origin="http://testserver",
                        secure_cookies=False, cookie_name="test-session", registration_enabled=False)
    engine = make_engine(settings)
    migrate(engine)
    engine.dispose()
    monkeypatch.setattr(manage, "get_settings", lambda: settings)
    monkeypatch.setattr(sys, "argv", ["manage", "create-user", "--email", "operator@example.com",
                                    "--name", "Operator", "--password-stdin"])
    monkeypatch.setattr(sys, "stdin", StringIO("test-password-long-enough\n"))
    manage.main()
    app = create_app(settings)
    try:
        with TestClient(app) as client:
            session = client.get("/api/v1/auth/session").json()
            result = client.post("/api/v1/auth/login", json={"email": "operator@example.com", "password": "test-password-long-enough"},
                                 headers={"Origin": settings.public_origin, "X-CSRF-Token": session["csrf"]})
            assert result.status_code == 200
            assert result.json()["user"]["name"] == "Operator"
            assert client.get("/api/v1/workspaces").status_code == 200
    finally:
        app.state.engine.dispose()
