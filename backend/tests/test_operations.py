"""Human operational controls and scoped source lifecycle acceptance tests."""
from typing import Any

from test_brain import core as core
from test_brain import submit
from test_platform import PREFIX, make_task, register, share, workspace


def test_workspace_stop_cancels_runs_and_blocks_new_submissions(core: Any) -> None:
    a, b, worker, _ = core
    ah, bh = register(a, "operator@example.com"), register(b, "client@example.com")
    wid = workspace(a, ah)
    share(a, b, ah, bh, wid, "client")
    task = make_task(a, ah, wid)
    submit(a, ah, wid, task)
    url = PREFIX + f"/workspaces/{wid}/execution"
    assert b.put(url, headers=bh, json={"stopped": True}).status_code == 403
    assert a.put(url, headers=ah, json={"stopped": True}).status_code == 200
    assert not worker.once()
    assert a.get(PREFIX + f"/workspaces/{wid}/runs").json()[0]["status"] == "cancelled"
    newer = make_task(a, ah, wid)
    response = a.post(PREFIX + f"/workspaces/{wid}/tasks/{newer['id']}/runs", headers=ah,
                      json={"revision": 1, "request_key": "stopped-request-key", "mode": "draft"})
    assert response.status_code == 409
    assert a.put(url, headers=ah, json={"stopped": False}).status_code == 200


def test_member_revocation_and_session_revocation_are_immediate(core: Any) -> None:
    a, b, _, _ = core
    ah, bh = register(a, "owner@example.com"), register(b, "member@example.com")
    wid = workspace(a, ah)
    share(a, b, ah, bh, wid, "developer")
    person = b.get(PREFIX + "/auth/session").json()["user"]
    assert a.delete(PREFIX + f"/workspaces/{wid}/members/{person['id']}", headers=ah).status_code == 204
    assert b.get(PREFIX + f"/workspaces/{wid}/state").status_code == 404
    assert b.post(PREFIX + "/auth/revoke-sessions", headers=bh, json={}).status_code == 204
    assert b.get(PREFIX + "/workspaces").status_code == 401


def test_source_versions_are_workspace_scoped_and_revocation_blocks_publication(core: Any) -> None:
    a, b, worker, provider = core
    ah, bh = register(a, "source@example.com"), register(b, "other@example.com")
    wid, other = workspace(a, ah), workspace(b, bh)
    url = PREFIX + f"/workspaces/{wid}/sources"
    source = a.post(url, headers=ah, json={"name": "Client brief", "text": "Keyboard access is required."})
    assert source.status_code == 201, source.text
    sid = source.json()["id"]
    assert b.get(url).status_code == 404
    task = make_task(b, bh, other)
    bad = b.post(PREFIX + f"/workspaces/{other}/tasks/{task['id']}/runs", headers=bh,
                 json={"revision": 1, "request_key": "foreign-source-key", "mode": "draft", "source_ids": [sid]})
    assert bad.status_code == 404
    task = make_task(a, ah, wid)
    run = a.post(PREFIX + f"/workspaces/{wid}/tasks/{task['id']}/runs", headers=ah,
                 json={"revision": 1, "request_key": "source-run-key-0001", "mode": "draft", "source_ids": [sid]})
    assert run.status_code == 201, run.text
    provider.hook = lambda: a.delete(url + "/" + sid, headers=ah)
    assert worker.once()
    result = a.get(PREFIX + f"/workspaces/{wid}/runs").json()[0]
    assert result["status"] == "failed"
    assert result["error_code"] == "source_permission_revoked"
    assert a.get(url).json() == []
