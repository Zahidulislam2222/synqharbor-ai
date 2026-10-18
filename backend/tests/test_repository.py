"""Repository patches bind approved file sets, base trees and workspace grants."""
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.agent_contracts import Patch, RepositoryProfile, load_profiles
from app.models import AgentRun, RepositoryGrant
from app.provider_errors import AgentFailure
from app.releases import LocalRepository
from app.repositories import canonical_patch, patch_files, scope_hash
from app.runner import CodeRunner
from test_brain import core as core
from test_platform import PREFIX, make_task, register, state, workspace


def profile() -> RepositoryProfile:
    return RepositoryProfile(name="Order totals", specification="Compute order totals",
                             files=["store/pricing.py", "store/discounts.py"],
                             entrypoint="store.pricing:quote",
                             cases=[{"input": [], "expected": 0}])

def test_patch_is_canonical_and_cannot_escape_operator_file_scope() -> None:
    approved = profile()
    patch = Patch(files={"store/discounts.py": "RATE = 0\n", "store/pricing.py": "def quote(x): return 0\n"},
                  summary="Implement pricing")
    content = canonical_patch(patch, "a" * 40, approved)
    assert patch_files(content, approved, "a" * 40) == patch.files
    reordered = Patch(files=dict(reversed(list(patch.files.items()))), summary="Other summary")
    assert canonical_patch(reordered, "a" * 40, approved) == content
    with pytest.raises(AgentFailure, match="patch_base_mismatch"):
        patch_files(content, approved, "b" * 40)
    for path in ["../escape.py", ".git/config", "/outside/escape.py", "store/unapproved.py"]:
        with pytest.raises(AgentFailure, match="patch_scope_mismatch"):
            canonical_patch(Patch(files={path: "pass"}, summary="Invalid"), "a" * 40, approved)
    with pytest.raises(AgentFailure, match="patch_scope_mismatch"):
        canonical_patch(Patch(files={"store/pricing.py": "pass"}, summary="Incomplete"), "a" * 40, approved)


@pytest.mark.parametrize("files,entrypoint", [(["../bad.py"], "bad:solve"),
    ([".git/hooks.py"], "hooks:solve"), (["package.py", "package.py"], "package:solve"),
    (["ok.py"], "other:solve"), (["ok.py"], "ok:__dict__")])
def test_invalid_repository_profiles_fail_validation(files: list[str], entrypoint: str) -> None:
    with pytest.raises(ValidationError):
        RepositoryProfile(name="Invalid", specification="Invalid", files=files, entrypoint=entrypoint,
                          cases=[{"input": 1, "expected": 1}])


def test_protected_expectations_are_not_part_of_model_context() -> None:
    approved = profile()
    assert "cases" not in approved.public_specification()
    assert "expected" not in json.dumps(approved.public_specification())
    assert approved.public_specification()["files"] == approved.files


@pytest.mark.parametrize("change", ["none", "revoke", "reconfigure", "escape"])
def test_scoped_repository_submission_and_fenced_publication(core: Any, monkeypatch: pytest.MonkeyPatch,
                                                            change: str) -> None:
    a, b, worker, provider = core
    ah, bh = register(a, "owner@example.com"), register(b, "other@example.com")
    wid, other = workspace(a, ah), workspace(b, bh)
    worker.settings.repository_targets = {"test-repository": Path("operator-repository")}
    worker.settings.runner_binary = Path("test-runner")
    worker.settings.runner_rootfs = Path("test-rootfs")
    worker.settings.runner_directory = Path("test-jobs")
    approved = load_profiles(worker.settings)["order-quote"]
    with Session(worker.engine) as db, db.begin():
        db.add(RepositoryGrant(workspace_id=wid, target="test-repository", profile="order-quote",
                               scope_hash=scope_hash(worker.settings, "test-repository", approved)))
    assert len(a.get(PREFIX + f"/workspaces/{wid}/repositories").json()) == 1
    assert b.get(PREFIX + f"/workspaces/{other}/repositories").json() == []
    body = {"revision": 1, "request_key": "repository-run-key-0001", "mode": "code",
            "repository": "test-repository", "profile": "order-quote"}
    foreign_task = make_task(b, bh, other)
    assert b.post(PREFIX + f"/workspaces/{other}/tasks/{foreign_task['id']}/runs", headers=bh,
                  json=body).status_code == 403
    monkeypatch.setattr(LocalRepository, "snapshot_files", lambda *_: {
        "commit": "a" * 40, "files": {path: "pass\n" for path in approved.files}})
    monkeypatch.setattr(CodeRunner, "test_files", lambda *_: {"passed": 5, "total": 5, "runtime": "test-adapter"})
    task = make_task(a, ah, wid)
    response = a.post(PREFIX + f"/workspaces/{wid}/tasks/{task['id']}/runs", headers=ah, json=body)
    assert response.status_code == 201, response.text
    old_generate = provider.generate

    def generate(model: str, system: str, data: Any, schema: Any) -> str:
        if schema is Patch:
            if change == "revoke":
                with Session(worker.engine) as db, db.begin():
                    grant = db.get(RepositoryGrant, (wid, "test-repository", "order-quote"))
                    assert grant is not None
                    db.delete(grant)
            paths = ["../escape.py"] if change == "escape" else approved.files
            return json.dumps({"files": {path: "pass\n" for path in paths}, "summary": "Test adapter output"})
        return str(old_generate(model, system, data, schema))

    monkeypatch.setattr(provider, "generate", generate)
    if change == "reconfigure":
        worker.settings.repository_targets = {"test-repository": Path("different-operator-repository")}
    assert worker.once()
    run = a.get(PREFIX + f"/workspaces/{wid}/runs").json()[0]
    assert run["status"] == ("succeeded" if change == "none" else "failed"), run
    assert bool(state(a, wid)["tasks"][0]["artifact_id"]) == (change == "none")
    if change == "none":
        with Session(worker.engine) as db:
            record = db.get(AgentRun, response.json()["id"])
            assert record is not None and "cases" not in json.dumps(record.inputs)
        assert set(run["evidence"]["repository"]["changes"]) == set(approved.files)
