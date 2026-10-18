"""Controller cleanup is mandatory after both successful and interrupted guests."""

import json
from pathlib import Path

import pytest
from pydantic import SecretStr

from app.provider_errors import AgentFailure
from app.runner import CLEANUP_REQUIRED, CodeRunner
from app.settings import Settings


def configured(tmp_path: Path) -> CodeRunner:
    rootfs = tmp_path / "rootfs"
    (rootfs / "app").mkdir(parents=True)
    (rootfs / "app/harness.py").write_text("# Test harness presence only; execution is mocked.\n")
    return CodeRunner(
        Settings(
            _env_file=None,
            database_url=SecretStr("sqlite://"),
            session_secret=SecretStr("test-key" * 8),
            public_origin="https://example.com",
            runner_binary=tmp_path / "runsc",
            runner_rootfs=rootfs,
            runner_directory=tmp_path / "jobs",
        )
    )


@pytest.mark.parametrize("interrupted", [False, True])
def test_job_scoped_sandbox_is_deleted_before_scratch_removal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, interrupted: bool
) -> None:
    runner = configured(tmp_path)
    calls = []
    listed = False

    def execute(command: list[str], *_: object) -> bytes:
        nonlocal listed
        if "bwrap" in command:
            calls.append("run")
            if interrupted:
                raise AgentFailure("process_output_limit")
            return b"1"
        if "list" in command:
            calls.append("list")
            result = [] if listed else [{"id": "job-sandbox"}]
            listed = True
            return json.dumps(result).encode()
        assert command[-3:] == ["delete", "--force", "job-sandbox"]
        calls.append("delete")
        return b""

    monkeypatch.setattr("app.runner.execute", execute)
    if interrupted:
        with pytest.raises(AgentFailure, match="process_output_limit"):
            runner.invoke("def solve(value): return 1", None)
    else:
        assert runner.invoke("def solve(value): return 1", None) == 1
    assert calls == ["run", "list", "delete", "list"]
    assert list((tmp_path / "jobs").iterdir()) == []


def test_cleanup_failure_preserves_state_and_blocks_later_code_jobs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = configured(tmp_path)
    calls = []

    def execute(command: list[str], *_: object) -> bytes:
        calls.append(command)
        if "bwrap" in command:
            return b"1"
        if "list" in command:
            return b'[{"id":"job-sandbox"}]'
        raise AgentFailure("process_timeout")

    monkeypatch.setattr("app.runner.execute", execute)
    with pytest.raises(AgentFailure, match="runner_cleanup_failed"):
        runner.invoke("def solve(value): return 1", None)
    job = next((tmp_path / "jobs").iterdir())
    assert (job / CLEANUP_REQUIRED).exists()
    assert (job / "project/solution.py").exists()
    before = len(calls)
    with pytest.raises(AgentFailure, match="runner_cleanup_required"):
        runner.invoke("def solve(value): return 1", None)
    assert len(calls) == before


def test_empty_runsc_null_inventory_is_successful_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = configured(tmp_path)

    def execute(command: list[str], *_: object) -> bytes:
        return b"1" if "bwrap" in command else b"null"

    monkeypatch.setattr("app.runner.execute", execute)
    assert runner.invoke("def solve(value): return 1", None) == 1
    assert list((tmp_path / "jobs").iterdir()) == []
