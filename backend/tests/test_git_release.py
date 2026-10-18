"""Real Git interleavings; fixture hooks are not a security qualification."""
import subprocess
from pathlib import Path
from typing import Any

import pytest
from pydantic import SecretStr

from app.provider_errors import AgentFailure
from app.releases import LocalRepository
from app.security import token_hash
from app.settings import Settings


def repository(tmp_path: Path) -> LocalRepository:
    def git(*args: str) -> None:
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)

    git("init", "-b", "main")
    git("config", "user.name", "Test author")
    git("config", "user.email", "test-author@example.com")
    git("config", "core.autocrlf", "false")
    (tmp_path / "solution.py").write_text("original\n")
    hook = tmp_path / ".git/hooks/pre-commit"
    hook.write_text("#!/bin/sh\n# Synthetic fixture validation, not a security scan.\ntest -f solution.py\n")
    hook.chmod(0o700)
    git("add", "solution.py")
    git("commit", "-m", "Test original")
    return LocalRepository(Settings(_env_file=None, database_url=SecretStr("sqlite://"),
        session_secret=SecretStr("test-key" * 8), public_origin="https://example.com", release_repository=tmp_path))


def test_concurrent_normal_git_commit_is_never_overwritten(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = repository(tmp_path)
    snapshot = {**repo.snapshot_files(["solution.py"]), "target": "test-target"}
    original_snapshot = repo.snapshot_files
    concurrent = []

    def preflight(paths: list[str]) -> Any:
        result = original_snapshot(paths)
        if not concurrent:
            (tmp_path / "solution.py").write_text("newer human change\n")
            repo.git("add", "solution.py")
            repo.git("commit", "-m", "Concurrent human change")
            concurrent.append(repo.git("rev-parse", "HEAD"))
        return result

    monkeypatch.setattr(repo, "snapshot_files", preflight)
    with pytest.raises(AgentFailure):
        repo.apply_files("test-race", snapshot, {"solution.py": "stale approved proposal\n"}, "test-digest")
    assert repo.git("rev-parse", "HEAD") == concurrent[0]
    assert (tmp_path / "solution.py").read_text() == "newer human change\n"
    assert not repo.git("status", "--porcelain")


@pytest.mark.parametrize("proposed", ["approved\n", "approved\r\n"])
def test_atomic_release_commits_exact_approved_files(tmp_path: Path, proposed: str) -> None:
    repo = repository(tmp_path)
    snapshot = {**repo.snapshot_files(["solution.py"]), "target": "test-target"}
    result = repo.apply_files("test-success", snapshot, {"solution.py": proposed}, token_hash(proposed))
    assert result["base_commit"] == snapshot["commit"]
    assert repo.git("rev-parse", "HEAD^") == snapshot["commit"]
    assert repo.git("show", "HEAD:solution.py", strip=False) == proposed
    assert (tmp_path / "solution.py").read_bytes() == proposed.encode()
    assert not repo.git("status", "--porcelain")


def test_ref_comparison_rejection_never_installs_proposed_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = repository(tmp_path)
    snapshot = {**repo.snapshot_files(["solution.py"]), "target": "test-target"}
    (tmp_path / "solution.py").write_text("newer change\n")
    repo.git("add", "solution.py")
    repo.git("commit", "-m", "Prepare concurrent commit")
    newer = repo.git("rev-parse", "HEAD")
    repo.git("reset", "--hard", snapshot["commit"])
    original_git = repo.git

    def race(*arguments: str, **kwargs: Any) -> str:
        if arguments[0] == "update-ref":
            # Simulate even a writer using plumbing despite the native index
            # lock. The target ref comparison must still reject our proposal.
            original_git("update-ref", snapshot["ref"], newer, snapshot["commit"])
            (tmp_path / "solution.py").write_text("newer change\n")
        return original_git(*arguments, **kwargs)

    monkeypatch.setattr(repo, "git", race)
    with pytest.raises(AgentFailure, match="release_outcome_uncertain"):
        repo.apply_files("test-cas-race", snapshot, {"solution.py": "stale proposal\n"}, "test-digest")
    assert original_git("rev-parse", "HEAD") == newer
    assert (tmp_path / "solution.py").read_text() == "newer change\n"


def test_reconciliation_checks_working_bytes_despite_git_line_filters(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    snapshot = {**repo.snapshot_files(["solution.py"]), "target": "test-target"}
    files = {"solution.py": "approved\n"}
    digest = token_hash(files["solution.py"])
    repo.apply_files("test-byte-exact", snapshot, files, digest)
    repo.git("config", "core.autocrlf", "true")
    (tmp_path / "solution.py").write_bytes(b"approved\r\n")
    repo.git("add", "--renormalize", "--", "solution.py")
    assert not repo.git("status", "--porcelain")
    with pytest.raises(AgentFailure, match="release_digest_mismatch"):
        repo.reconcile_files("test-byte-exact", snapshot, files, digest)


def test_publication_preserves_operator_index_read_permissions(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    index = tmp_path / '.git/index'
    index.chmod(0o640)
    snapshot = {**repo.snapshot_files(['solution.py']), 'target': 'test-target'}
    proposed = 'approved read boundary\n'
    repo.apply_files('test-index-mode', snapshot, {'solution.py': proposed}, token_hash(proposed))
    assert index.stat().st_mode & 0o777 == 0o640
    assert (tmp_path / 'solution.py').read_bytes() == proposed.encode()
