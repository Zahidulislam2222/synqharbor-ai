"""External-action ambiguity and approval-version reservation regression tests.

Transport is mocked here; real Git/security-hook evidence is in the retained manual verifier.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import AgentRun
from app.provider_errors import AgentFailure
from app.releases import LocalRepository
from app.repositories import update_repository_grant
from app.runner import CodeRunner
from test_brain import core as core
from test_platform import PREFIX, make_task, register, share, state, workspace


def prepared(core: Any, monkeypatch: pytest.MonkeyPatch,
             deliverer: tuple[Any, dict[str, str]] | None = None) -> tuple[Any, ...]:
    a, b, worker, _ = core
    worker.settings.release_repository = Path("test-operator-target")
    worker.settings.runner_binary = Path("test-runsc")
    worker.settings.runner_rootfs = Path("test-rootfs")
    worker.settings.runner_directory = Path("test-jobs")
    monkeypatch.setattr(LocalRepository, "snapshot", lambda *_: {
        "commit": "test-original-head", "source": "test-source", "output_path": "solution.py"})
    monkeypatch.setattr(CodeRunner, "test", lambda *_: {"passed": 4, "total": 4, "runtime": "test-provider"})
    ah, bh = register(a, "developer@example.com"), register(b, "client@example.com")
    wid = workspace(a, ah)
    share(a, b, ah, bh, wid, "client")
    if deliverer:
        share(a, deliverer[0], ah, deliverer[1], wid, "developer")
    task = make_task(a, ah, wid)
    url = PREFIX + f"/workspaces/{wid}/tasks/{task['id']}"
    result = a.post(url + "/runs", headers=ah,
                    json={"revision": 1, "request_key": "test-release-run-0001", "mode": "code", "fixture": "normalize-tags"})
    assert result.status_code == 201, result.text
    # Legacy single-file release recovery compatibility; new HTTP repository
    # submissions use an explicit operator grant and multi-file artifact.
    with Session(worker.engine) as db, db.begin():
        historical = db.get(AgentRun, result.json()["id"])
        assert historical is not None
        historical.inputs = {**historical.inputs, "repository": {
            "commit": "test-original-head", "source": "test-source", "output_path": "solution.py"}}
    assert worker.once()
    task = state(a, wid)["tasks"][0]
    body = {"revision": task["revision"], "version": task["version"], "content_hash": task["content_hash"]}
    assert b.post(url + "/approvals", headers=bh, json={**body, "kind": "client"}).status_code == 201
    body["revision"] = state(a, wid)["tasks"][0]["revision"]
    assert a.post(url + "/approvals", headers=ah, json={**body, "kind": "developer"}).status_code == 201
    body["revision"] = state(a, wid)["tasks"][0]["revision"]
    delivery_client, delivery_headers = deliverer or (a, ah)
    delivery = delivery_client.post(url + "/deliveries", headers=delivery_headers,
                      json={**body, "request_key": "test-release-delivery-0001"})
    assert delivery.status_code == 201, delivery.text
    return a, worker, ah, wid, url, delivery.json()


def test_uncertain_release_is_reconciled_without_repeating_write(core: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    a, worker, headers, wid, url, delivery = prepared(core, monkeypatch)
    effects = []

    def accepted_then_timeout(self: Any, *arguments: Any) -> Any:
        effects.append("committed")
        raise AgentFailure("process_timeout")

    monkeypatch.setattr(LocalRepository, "apply", accepted_then_timeout)
    assert worker.once()
    result = a.get(PREFIX + f"/workspaces/{wid}/deliveries").json()[0]
    assert result["release"]["status"] == "uncertain"
    task = state(a, wid)["tasks"][0]
    blocked = a.post(url + "/artifacts", headers=headers, json={"revision": task["revision"], "content": "Changed"})
    assert blocked.json()["detail"]["code"] == "release_in_progress"
    monkeypatch.setattr(LocalRepository, "reconcile", lambda *_: {"commit": "test-accepted-commit"})
    reconcile = a.post(PREFIX + f"/workspaces/{wid}/deliveries/{delivery['id']}/reconcile", headers=headers, json={})
    assert reconcile.status_code == 200
    assert worker.once()
    assert effects == ["committed"]
    result = a.get(PREFIX + f"/workspaces/{wid}/deliveries").json()[0]
    assert result["release"]["status"] == "succeeded"
    assert state(a, wid)["tasks"][0]["status"] == "complete"


def test_changed_repository_head_fails_without_completing_task(core: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    a, worker, _, wid, _, _ = prepared(core, monkeypatch)

    def changed(self: Any, *arguments: Any) -> Any:
        raise AgentFailure("release_head_changed")

    monkeypatch.setattr(LocalRepository, "apply", changed)
    assert worker.once()
    result = a.get(PREFIX + f"/workspaces/{wid}/deliveries").json()[0]
    assert result["release"]["status"] == "failed"
    assert state(a, wid)["tasks"][0]["status"] == "review"


def test_revoked_delivery_submitter_cannot_trigger_approved_release(core: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    owner = core[0]
    with TestClient(owner.app) as developer:
        headers = register(developer, "delivery-submitter@example.com")
        actor_id = developer.get(PREFIX + "/auth/session").json()["user"]["id"]
        a, worker, ah, wid, _, _ = prepared(core, monkeypatch, (developer, headers))
        assert a.delete(PREFIX + f"/workspaces/{wid}/members/{actor_id}", headers=ah).status_code == 204
        effects = []
        monkeypatch.setattr(LocalRepository, "apply", lambda *_: effects.append("committed") or {"commit": "test-commit"})
        assert worker.once()
        result = a.get(PREFIX + f"/workspaces/{wid}/deliveries").json()[0]
        assert effects == []
        assert result["release"]["status"] == "failed"


@pytest.mark.parametrize("multiple", [False, True])
def test_post_commit_verification_errors_are_uncertain(core: Any, monkeypatch: pytest.MonkeyPatch,
                                                     tmp_path: Path, multiple: bool) -> None:
    settings = core[2].settings.model_copy(update={"release_repository": tmp_path})
    (tmp_path / ".git/hooks").mkdir(parents=True)
    (tmp_path / ".git/hooks/pre-commit").write_text("Test hook presence; Git transport is mocked")
    (tmp_path / ".git/index").write_bytes(b"test-index-transport-is-mocked")
    (tmp_path / "solution.py").write_text("old")
    repository = LocalRepository(settings)
    commits = []

    def git(*arguments: str, **kwargs: Any) -> str:
        if arguments[0] == "update-ref":
            commits.append("accepted")
        return ""

    def reconcile(*args: Any) -> Any:
        if commits:
            raise AgentFailure("release_target_dirty")
        return None

    monkeypatch.setattr(repository, "git", git)
    monkeypatch.setattr(repository, "reconcile", reconcile)
    monkeypatch.setattr(repository, "reconcile_files", reconcile)
    monkeypatch.setattr(repository, "prepare_files", lambda *_: ("test-new-commit", b"test-index"))
    monkeypatch.setattr(repository, "snapshot", lambda *_: {"commit": "test-base"})
    monkeypatch.setattr(repository, "snapshot_files", lambda *_: {"commit": "test-base", "ref": "refs/heads/main", "files": {"solution.py": "old"}})
    with pytest.raises(AgentFailure, match="release_outcome_uncertain"):
        if multiple:
            repository.apply_files("test-intent", {"commit": "test-base", "ref": "refs/heads/main", "files": {"solution.py": "old"}},
                                   {"solution.py": "new"}, "test-digest")
        else:
            repository.apply_locked("test-intent", {"commit": "test-base", "ref": "refs/heads/main", "source": "old", "output_path": "solution.py"}, "new")
    assert commits == ["accepted"]


@pytest.mark.parametrize("control", ["stop", "member", "source", "grant"])
def test_acknowledged_controls_cannot_overtake_external_write(core: Any, monkeypatch: pytest.MonkeyPatch,
                                                           control: str) -> None:
    a, worker, ah, wid, _, _ = prepared(core, monkeypatch)
    entered, continue_write, attempted, acknowledged = Event(), Event(), Event(), Event()
    source = a.post(PREFIX + f"/workspaces/{wid}/sources", headers=ah,
                    json={"name": "Test source", "text": "Test input"}).json()["id"]
    client_id = core[1].get(PREFIX + "/auth/session").json()["user"]["id"]
    order = []

    def apply(*args: Any) -> Any:
        entered.set()
        assert continue_write.wait(10)
        order.append("write")
        assert not acknowledged.is_set()
        return {"commit": "test-commit"}

    def change_control() -> None:
        attempted.set()
        if control == "stop":
            result = a.put(PREFIX + f"/workspaces/{wid}/execution", headers=ah, json={"stopped": True})
        elif control == "member":
            result = a.delete(PREFIX + f"/workspaces/{wid}/members/{client_id}", headers=ah)
        elif control == "source":
            result = a.delete(PREFIX + f"/workspaces/{wid}/sources/{source}", headers=ah)
        else:
            with Session(worker.engine) as db, db.begin():
                update_repository_grant(db, worker.settings, wid, "test-target", "test-profile", allowed=False)
            result = None
        if result is not None:
            assert result.status_code in {200, 204}, result.text
        order.append("acknowledgement")
        acknowledged.set()

    monkeypatch.setattr(LocalRepository, "apply", apply)
    with ThreadPoolExecutor(max_workers=2) as pool:
        writing = pool.submit(worker.once)
        try:
            assert entered.wait(10)
            controlling = pool.submit(change_control)
            assert attempted.wait(10)
            assert not acknowledged.wait(0.2)
        finally:
            continue_write.set()
        assert writing.result(timeout=15)
        controlling.result(timeout=15)
    assert order == ["write", "acknowledgement"]


def test_acknowledged_stop_prevents_queued_release(core: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    a, worker, ah, wid, _, _ = prepared(core, monkeypatch)
    assert a.put(PREFIX + f"/workspaces/{wid}/execution", headers=ah, json={"stopped": True}).status_code == 200
    effects = []
    monkeypatch.setattr(LocalRepository, "apply", lambda *_: effects.append("committed"))
    assert worker.once()
    assert effects == []
    assert a.get(PREFIX + f"/workspaces/{wid}/deliveries").json()[0]["release"]["status"] == "failed"
