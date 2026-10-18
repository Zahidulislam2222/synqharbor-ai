"""Durable orchestration acceptance/security tests through the real HTTP contract."""
import json
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel, SecretStr
from sqlalchemy import event, select
from sqlalchemy.orm import Session

from app.brain import Worker, claim
from app.database import migrate
from app.main import create_app
from app.models import AgentRun, Artifact, Membership, now
from app.provider_errors import AgentFailure
from app.settings import Settings
from test_platform import PREFIX, make_task, register, share, state, workspace


class TestProvider:
    __test__ = False

    def __init__(self, accepted: bool = True) -> None:
        self.accepted = accepted
        self.calls: list[dict[str, Any]] = []
        self.hook: Any = None

    def generate(self, model: str, system: str, data: dict[str, Any], schema: type[BaseModel]) -> str:
        self.calls.append({"model": model, "system": system, "data": data})
        if self.hook:
            self.hook()
            self.hook = None
        if "artifact" in data:
            return json.dumps({"accepted": self.accepted, "findings": [],
                               "criterion_results": [self.accepted for _ in data["criteria"]]})
        return json.dumps({"content": "An accessible navigation proposal with keyboard controls.",
                           "summary": "Drafted the requested proposal"})


@pytest.fixture
def core(tmp_path: Any) -> Iterator[tuple[TestClient, TestClient, Worker, TestProvider]]:
    settings = Settings(_env_file=None, database_url=SecretStr("sqlite:///" + str(tmp_path / "core.sqlite")),
                        session_secret=SecretStr("test-key" * 8), public_origin="http://testserver",
                        secure_cookies=False, cookie_name="test-session", builder_model="test-builder",
                        reviewer_model="test-reviewer", inference_url="http://127.0.0.1:1",
                        session_rate_limit=1000, auth_rate_limit=1000, write_rate_limit=1000)
    app = create_app(settings)
    migrate(app.state.engine)
    provider = TestProvider()
    with TestClient(app) as a, TestClient(app) as b:
        yield a, b, Worker(app.state.engine, settings, provider), provider
    app.state.engine.dispose()


def submit(a: TestClient, headers: dict[str, str], wid: str, task: dict[str, Any],
           key: str = "test-request-key-0001") -> dict[str, Any]:
    response = a.post(PREFIX + f"/workspaces/{wid}/tasks/{task['id']}/runs", headers=headers,
                      json={"revision": task["revision"], "request_key": key, "mode": "draft"})
    assert response.status_code == 201, response.text
    return dict(response.json())


def test_end_to_end_draft_review_dual_approval_delivery(core: Any) -> None:
    a, b, worker, provider = core
    ah, bh = register(a, "developer@example.com"), register(b, "client@example.com")
    wid = workspace(a, ah)
    share(a, b, ah, bh, wid, "client")
    task = make_task(a, ah, wid)
    url = PREFIX + f"/workspaces/{wid}/tasks/{task['id']}"
    original = submit(a, ah, wid, task)
    assert submit(a, ah, wid, task)["id"] == original["id"]
    assert worker.once()
    assert not worker.once()
    run = a.get(PREFIX + f"/workspaces/{wid}/runs").json()[0]
    assert run["status"] == "succeeded", run
    assert run["evidence"]["review"]["accepted"]
    assert len(provider.calls) == 2
    assert provider.calls[0]["model"] != provider.calls[1]["model"]
    assert "artifact" not in provider.calls[0]["data"]
    assert provider.calls[1]["data"]["artifact"] == a.get(
        PREFIX + f"/workspaces/{wid}/artifacts/{run['artifact_id']}").text
    task = state(a, wid)["tasks"][0]
    delivery = {"revision": task["revision"], "version": task["version"],
                "content_hash": task["content_hash"], "request_key": "test-delivery-key-0001"}
    assert a.post(url + "/deliveries", headers=ah, json=delivery).status_code == 409
    decision = {k: delivery[k] for k in ("revision", "version", "content_hash")}
    assert b.post(url + "/approvals", headers=bh, json={**decision, "kind": "client"}).status_code == 201
    decision["revision"] = state(a, wid)["tasks"][0]["revision"]
    assert a.post(url + "/approvals", headers=ah, json={**decision, "kind": "developer"}).status_code == 201
    delivery["revision"] = state(a, wid)["tasks"][0]["revision"]
    result = a.post(url + "/deliveries", headers=ah, json=delivery)
    assert result.status_code == 201, result.text
    assert result.json()["external_deployment"] is False
    assert a.post(url + "/deliveries", headers=ah, json=delivery).json()["id"] == result.json()["id"]
    assert a.post(url + "/deliveries", headers=ah,
                  json={**delivery, "version": delivery["version"] + 1}).status_code == 409
    assert state(a, wid)["tasks"][0]["status"] == "complete"
    assert len(a.get(PREFIX + f"/workspaces/{wid}/deliveries").json()) == 1
    report = a.get(PREFIX + f"/workspaces/{wid}/deliveries/{result.json()['id']}/report")
    assert report.status_code == 200 and "attachment" in report.headers["content-disposition"]
    assert report.json()["artifact"]["content_hash"] == task["content_hash"]
    assert len(report.json()["approvals"]) == 2
    with TestClient(a.app) as outsider:
        register(outsider, "report-outsider@example.com")
        assert outsider.get(PREFIX + f"/workspaces/{wid}/deliveries/{result.json()['id']}/report").status_code == 404


@pytest.mark.parametrize("reason", ["review", "cancel", "stale", "revoked", "provider"])
def test_failed_or_cancelled_work_never_publishes(core: Any, reason: str) -> None:
    a, _, worker, provider = core
    ah = register(a, "developer@example.com")
    wid = workspace(a, ah)
    task = make_task(a, ah, wid)
    run = submit(a, ah, wid, task)
    if reason == "review":
        provider.accepted = False
    elif reason == "cancel":
        provider.hook = lambda: a.post(PREFIX + f"/workspaces/{wid}/runs/{run['id']}/cancel", headers=ah)
    elif reason == "stale":
        provider.hook = lambda: a.patch(PREFIX + f"/workspaces/{wid}/tasks/{task['id']}", headers=ah,
                                       json={"revision": state(a, wid)["tasks"][0]["revision"], "status": "planned"})
    elif reason == "revoked":
        def revoke() -> None:
            with Session(worker.engine) as db, db.begin():
                membership = db.scalar(select(Membership).where(Membership.workspace_id == wid))
                assert membership is not None
                membership.role = "viewer"
        provider.hook = revoke
    else:
        def fail() -> None:
            raise AgentFailure("inference_unavailable")
        provider.hook = fail
    assert worker.once()
    with Session(worker.engine) as db:
        record = db.get(AgentRun, run["id"])
        assert record is not None and record.status in {"failed", "cancelled"}
        assert db.scalar(select(Artifact.id)) is None


def test_lease_recovery_fences_old_worker(core: Any) -> None:
    a, _, worker, _ = core
    ah = register(a, "developer@example.com")
    wid = workspace(a, ah)
    run = submit(a, ah, wid, make_task(a, ah, wid))
    old = claim(worker.engine, worker.settings)
    assert old is not None
    with Session(worker.engine) as db, db.begin():
        record = db.get(AgentRun, run["id"])
        assert record is not None
        record.lease_until = now() - 1
    replacement = claim(worker.engine, worker.settings)
    assert replacement is not None and replacement.fence != old.fence
    worker.process(old)
    worker.process(replacement)
    with Session(worker.engine) as db:
        record = db.get(AgentRun, run["id"])
        assert record is not None and record.status == "succeeded" and record.attempt == 2


def test_concurrent_dispatchers_claim_one_execution_only(core: Any) -> None:
    a, _, worker, _ = core
    headers = register(a, "concurrent@example.com")
    wid = workspace(a, headers)
    submit(a, headers, wid, make_task(a, headers, wid))
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: claim(worker.engine, worker.settings), range(4)))
    assignments = [result for result in results if result is not None]
    assert len(assignments) == 1
    worker.process(assignments[0])
    assert a.get(PREFIX + f"/workspaces/{wid}/runs").json()[0]["status"] == "succeeded"


def test_health_does_not_reserve_another_pool_connection(core: Any) -> None:
    a, _, worker, _ = core
    checked_out = 0
    maximum = 0

    def checkout(*args: Any) -> None:
        nonlocal checked_out, maximum
        checked_out += 1
        maximum = max(maximum, checked_out)

    def checkin(*args: Any) -> None:
        nonlocal checked_out
        checked_out -= 1

    event.listen(worker.engine, "checkout", checkout)
    event.listen(worker.engine, "checkin", checkin)
    try:
        assert a.get(PREFIX + "/health").status_code == 200
        assert maximum == 1 and checked_out == 0
    finally:
        event.remove(worker.engine, "checkout", checkout)
        event.remove(worker.engine, "checkin", checkin)


@pytest.mark.parametrize("review", [
    {"accepted": True, "findings": ["Blocking defect"], "criterion_results": [True]},
    {"accepted": True, "findings": [], "criterion_results": [False]},
    {"accepted": True, "findings": [], "criterion_results": [True, True]},
])
def test_inconsistent_reviewer_acceptance_never_publishes(core: Any, monkeypatch: pytest.MonkeyPatch,
                                                        review: dict[str, Any]) -> None:
    a, _, worker, provider = core
    headers = register(a, "review-contract@example.com")
    wid = workspace(a, headers)
    submit(a, headers, wid, make_task(a, headers, wid))
    original = provider.generate

    def generate(model: str, system: str, data: Any, schema: Any) -> str:
        return json.dumps(review) if "artifact" in data else str(original(model, system, data, schema))

    monkeypatch.setattr(provider, "generate", generate)
    assert worker.once()
    record = a.get(PREFIX + f"/workspaces/{wid}/runs").json()[0]
    assert record["status"] == "failed" and record["error_code"] == "review_rejected"
    assert not state(a, wid)["tasks"][0]["artifact_id"]


def test_run_scope_and_duplicate_conflicts(core: Any) -> None:
    a, b, _, _ = core
    ah, bh = register(a, "owner@example.com"), register(b, "other@example.com")
    wid = workspace(a, ah)
    task = make_task(a, ah, wid)
    run = submit(a, ah, wid, task)
    assert b.get(PREFIX + f"/workspaces/{wid}/runs").status_code == 404
    assert b.post(PREFIX + f"/workspaces/{wid}/runs/{run['id']}/cancel", headers=bh).status_code == 404
    assert b.post(PREFIX + f"/workspaces/{wid}/tasks/{task['id']}/deliveries", headers=bh,
                  json={"revision": 1, "version": 1, "content_hash": "0" * 64,
                        "request_key": "test-denied-delivery-0001"}).status_code == 404
    response = a.post(PREFIX + f"/workspaces/{wid}/tasks/{task['id']}/runs", headers=ah,
                      json={"revision": task["revision"], "request_key": "test-request-key-0001", "mode": "code"})
    assert response.status_code == 409
    task = state(a, wid)["tasks"][0]
    response = a.post(PREFIX + f"/workspaces/{wid}/tasks/{task['id']}/runs", headers=ah,
                      json={"revision": task["revision"], "request_key": "test-request-key-0002", "mode": "draft"})
    assert response.status_code == 409


def test_no_remote_or_credential_bearing_inference_urls() -> None:
    for endpoint in ["https://api.example.com", "http://user:pass@127.0.0.1", "http://127.0.0.1?secret=x"]:
        with pytest.raises(ValueError):
            Settings(_env_file=None, database_url=SecretStr("sqlite://"), session_secret=SecretStr("test-key" * 8),
                     public_origin="https://example.com", inference_url=endpoint)
