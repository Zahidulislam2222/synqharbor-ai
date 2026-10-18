"""Behavioral security and persistence checks for the public HTTP contract."""
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.database import migrate
from app.main import create_app
from app.settings import Settings

ORIGIN = "http://testserver"
PREFIX = "/api/v1"
FAKE_PASSWORD = "test-password-long-enough"


@pytest.fixture
def clients() -> Iterator[tuple[TestClient, TestClient]]:
    config = Settings(_env_file=None, database_url=SecretStr("sqlite://"), session_secret=SecretStr("test-key" * 8),
                      public_origin=ORIGIN, secure_cookies=False, cookie_name="test-session",
                      session_rate_limit=1000, auth_rate_limit=1000, write_rate_limit=1000)
    app = create_app(config)
    migrate(app.state.engine)
    with TestClient(app) as a, TestClient(app) as b:
        yield a, b
    app.state.engine.dispose()


def session(client: TestClient) -> dict[str, str]:
    response = client.get(PREFIX + "/auth/session")
    assert response.status_code == 200
    return {"Origin": ORIGIN, "X-CSRF-Token": response.json()["csrf"]}


def register(client: TestClient, email: str) -> dict[str, str]:
    headers = session(client)
    result = client.post(PREFIX + "/auth/register", headers=headers,
                         json={"name": "Test person", "email": email, "password": FAKE_PASSWORD})
    assert result.status_code == 201, result.text
    assert "password" not in result.text
    return {"Origin": ORIGIN, "X-CSRF-Token": result.json()["csrf"]}


def workspace(client: TestClient, headers: dict[str, str]) -> str:
    result = client.post(PREFIX + "/workspaces", headers=headers, json={"name": "Private team"})
    assert result.status_code == 201, result.text
    return str(result.json()["id"])


def state(client: TestClient, wid: str) -> dict[str, Any]:
    result = client.get(PREFIX + "/workspaces/" + wid + "/state")
    assert result.status_code == 200, result.text
    return dict(result.json())


def make_task(client: TestClient, headers: dict[str, str], wid: str) -> dict[str, Any]:
    result = client.post(PREFIX + f"/workspaces/{wid}/tasks", headers=headers,
                         json={"title": "Accessible navigation", "project": "Website", "criteria": ["Keyboard usable"]})
    assert result.status_code == 201, result.text
    return dict(state(client, wid)["tasks"][0])


def share(client: TestClient, other: TestClient, headers: dict[str, str], other_headers: dict[str, str],
          wid: str, role: str) -> None:
    invite = client.post(PREFIX + f"/workspaces/{wid}/invitations", headers=headers, json={"role": role})
    assert invite.status_code == 201
    result = other.post(PREFIX + "/invitations/accept", headers=other_headers, json={"token": invite.json()["token"]})
    assert result.status_code == 200, result.text


def test_session_cookie_and_no_auth_without_login(clients: tuple[TestClient, TestClient]) -> None:
    a, _ = clients
    result = a.get(PREFIX + "/auth/session")
    assert "HttpOnly" in result.headers["set-cookie"]
    assert "SameSite=lax" in result.headers["set-cookie"]
    assert a.get(PREFIX + "/workspaces").status_code == 401
    assert result.headers["cache-control"] == "no-store"


def test_proxy_clients_have_independent_established_session_budgets(clients: tuple[TestClient, TestClient]) -> None:
    a, b = clients
    a.app.state.settings.session_rate_limit = 2
    assert a.get(PREFIX + "/auth/session").status_code == 200
    assert b.get(PREFIX + "/auth/session").status_code == 200
    for client in [a, b]:
        assert client.get(PREFIX + "/auth/session").status_code == 200
        assert client.get(PREFIX + "/auth/session").status_code == 200
        assert client.get(PREFIX + "/auth/session").status_code == 429


def test_operator_can_close_public_registration(clients: tuple[TestClient, TestClient]) -> None:
    a, _ = clients
    a.app.state.settings.registration_enabled = False
    result = a.post(PREFIX + "/auth/register", headers=session(a),
                    json={"name": "Managed person", "email": "managed@example.com", "password": FAKE_PASSWORD})
    assert result.status_code == 403
    assert result.json()["detail"]["code"] == "registration_closed"
    assert a.get(PREFIX + "/workspaces").status_code == 401


def test_forged_session_cookies_cannot_bypass_anonymous_budget(clients: tuple[TestClient, TestClient]) -> None:
    a, _ = clients
    a.app.state.settings.session_rate_limit = 2
    for number, status in enumerate([200, 200, 429]):
        result = a.get(PREFIX + "/auth/session", headers={"Cookie": "test-session=forged-" + str(number)})
        assert result.status_code == status


@pytest.mark.parametrize("origin,csrf", [(ORIGIN, "wrong"), ("https://sibling.example.com", "correct"), ("", "correct")])
def test_csrf_blocks_registration(clients: tuple[TestClient, TestClient], origin: str, csrf: str) -> None:
    a, _ = clients
    headers = session(a)
    headers["Origin"] = origin
    if csrf == "wrong":
        headers["X-CSRF-Token"] = "test-wrong-token"
    result = a.post(PREFIX + "/auth/register", headers=headers,
                    json={"name": "Test", "email": "user@example.com", "password": FAKE_PASSWORD})
    assert result.status_code == 403


def test_tenant_isolation_and_safe_validation(clients: tuple[TestClient, TestClient]) -> None:
    a, b = clients
    ah = register(a, "owner@example.com")
    bh = register(b, "other@example.com")
    wid = workspace(a, ah)
    task = make_task(a, ah, wid)
    assert b.get(PREFIX + f"/workspaces/{wid}/state").status_code == 404
    assert b.get(PREFIX + "/workspaces").json() == []
    assert b.patch(PREFIX + f"/workspaces/{wid}/tasks/{task['id']}", headers=bh,
                   json={"revision": 1, "status": "progress"}).status_code == 404
    bad = a.post(PREFIX + "/auth/login", headers=ah,
                 json={"email": "bad", "password": "test-sensitive-input"})
    assert bad.status_code == 422
    assert "test-sensitive-input" not in bad.text


def test_login_rotation_logout_and_persistence(clients: tuple[TestClient, TestClient]) -> None:
    a, _ = clients
    ah = register(a, "owner@example.com")
    wid = workspace(a, ah)
    make_task(a, ah, wid)
    old = a.cookies.get("test-session")
    assert a.post(PREFIX + "/auth/logout", headers=ah).status_code == 204
    a.cookies.set("test-session", str(old))
    assert a.get(PREFIX + "/workspaces").status_code == 401
    a.cookies.clear()
    login = a.post(PREFIX + "/auth/login", headers=session(a),
                   json={"email": "owner@example.com", "password": FAKE_PASSWORD})
    assert login.status_code == 200
    assert a.cookies.get("test-session") != old
    assert len(state(a, wid)["tasks"]) == 1


def test_versioned_artifacts_and_independent_approvals(clients: tuple[TestClient, TestClient]) -> None:
    a, b = clients
    ah, bh = register(a, "owner@example.com"), register(b, "client@example.com")
    wid = workspace(a, ah)
    share(a, b, ah, bh, wid, "client")
    task = make_task(a, ah, wid)
    task_url = PREFIX + f"/workspaces/{wid}/tasks/{task['id']}"
    assert a.patch(task_url, headers=ah, json={"revision": task["revision"], "status": "complete"}).status_code == 409
    artifact = a.post(task_url + "/artifacts", headers=ah, json={"revision": task["revision"], "content": "First result"})
    assert artifact.status_code == 201
    task = state(a, wid)["tasks"][0]
    decision = {"revision": task["revision"], "version": task["version"], "content_hash": task["content_hash"], "kind": "developer"}
    assert a.post(task_url + "/approvals", headers=ah, json=decision).status_code == 409
    assert b.post(task_url + "/approvals", headers=bh, json=decision).status_code == 403
    decision["kind"] = "client"
    assert b.post(task_url + "/approvals", headers=bh, json=decision).status_code == 201
    task = state(a, wid)["tasks"][0]
    decision.update(revision=task["revision"], kind="developer")
    assert a.post(task_url + "/approvals", headers=ah, json=decision).status_code == 201
    task = state(a, wid)["tasks"][0]
    assert a.patch(task_url, headers=ah, json={"revision": task["revision"], "status": "complete"}).status_code == 200
    task = state(a, wid)["tasks"][0]
    assert a.post(task_url + "/artifacts", headers=ah, json={"revision": task["revision"], "content": "Revised result"}).status_code == 201
    revised = state(a, wid)["tasks"][0]
    assert revised["version"] == 2
    assert not revised["clientApproved"] and not revised["developerApproved"]
    decision["revision"] = revised["revision"]
    assert a.post(task_url + "/approvals", headers=ah, json=decision).status_code == 409
    original = a.get(PREFIX + f"/workspaces/{wid}/artifacts/{artifact.json()['id']}")
    assert original.text == "First result"
    assert original.headers["content-type"].startswith("text/plain")


def test_same_person_cannot_approve_both_steps(clients: tuple[TestClient, TestClient]) -> None:
    a, _ = clients
    ah = register(a, "owner@example.com")
    wid = workspace(a, ah)
    task = make_task(a, ah, wid)
    url = PREFIX + f"/workspaces/{wid}/tasks/{task['id']}"
    a.post(url + "/artifacts", headers=ah, json={"revision": task["revision"], "content": "Result"})
    task = state(a, wid)["tasks"][0]
    body = {"revision": task["revision"], "version": task["version"], "content_hash": task["content_hash"], "kind": "client"}
    assert a.post(url + "/approvals", headers=ah, json=body).status_code == 201
    body.update(revision=state(a, wid)["tasks"][0]["revision"], kind="developer")
    assert a.post(url + "/approvals", headers=ah, json=body).json()["detail"]["code"] == "independent_approver_required"


def test_stale_writes_viewer_permissions_and_messages(clients: tuple[TestClient, TestClient]) -> None:
    a, b = clients
    ah, bh = register(a, "owner@example.com"), register(b, "viewer@example.com")
    wid = workspace(a, ah)
    share(a, b, ah, bh, wid, "viewer")
    task = make_task(a, ah, wid)
    url = PREFIX + f"/workspaces/{wid}/tasks/{task['id']}"
    assert a.patch(url, headers=ah, json={"revision": 1, "status": "progress"}).status_code == 200
    assert a.patch(url, headers=ah, json={"revision": 1, "status": "review"}).status_code == 409
    assert b.post(PREFIX + f"/workspaces/{wid}/tasks", headers=bh,
                  json={"title": "Blocked", "project": "Website"}).status_code == 403
    assert b.post(PREFIX + f"/workspaces/{wid}/invitations", headers=bh, json={"role": "developer"}).status_code == 403
    message = "<script>alert('test')</script>"
    assert a.post(PREFIX + f"/workspaces/{wid}/messages", headers=ah, json={"text": message}).status_code == 201
    assert state(a, wid)["messages"][0]["text"] == message


def test_contact_intake_and_body_limit(clients: tuple[TestClient, TestClient]) -> None:
    a, _ = clients
    headers = session(a)
    result = a.post(PREFIX + "/contact", headers=headers,
                    json={"name": "Test", "email": "contact@example.com", "text": "Deployment question"})
    assert result.status_code == 201
    assert result.json()["status"] == "received"
    assert "sent" not in result.text
    oversized = a.post(PREFIX + "/contact", headers={**headers, "Content-Type": "application/json"},
                       content="x" * 70000)
    assert oversized.status_code == 413


def test_secure_settings_fail_closed() -> None:
    with pytest.raises(ValueError):
        Settings(_env_file=None, database_url=SecretStr("sqlite://"), session_secret=SecretStr("test-key"), public_origin=ORIGIN)
    with pytest.raises(ValueError):
        Settings(_env_file=None, database_url=SecretStr("sqlite://"), session_secret=SecretStr("test-key" * 8), public_origin=ORIGIN)
