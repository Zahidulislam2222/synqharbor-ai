"""Approved local test-repository release, with a durable uncertain-outcome boundary."""
import fcntl
import os
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

from sqlalchemy import Engine, select, update
from sqlalchemy.orm import Session

from .coordination import lock_workspace
from .models import (
    AgentRun,
    Approval,
    Artifact,
    AuditEvent,
    Delivery,
    Membership,
    ReleaseIntent,
    Task,
    now,
)
from .process import execute
from .provider_errors import AgentFailure
from .security import token_hash
from .settings import Settings


class LocalRepository:
    def __init__(self, settings: Settings, path: Path | None = None) -> None:
        self.settings = settings.model_copy(update={"release_repository": path}) if path else settings

    def git(self, *arguments: str, strip: bool = True) -> str:
        config = self.settings
        if not config.release_repository or not (config.release_repository / ".git").is_dir():
            raise AgentFailure("release_target_unavailable")
        # Normal git commit invokes the repository's installed security hooks.
        result = execute([config.git_binary, "--no-optional-locks", "-C", str(config.release_repository), *arguments], b"",
                         config.git_timeout, config.inference_max_bytes, os.environ).decode()
        return result.strip() if strip else result

    def snapshot(self, output_path: str) -> dict[str, str]:
        path = PurePosixPath(output_path)
        if path.is_absolute() or ".." in path.parts or ".git" in path.parts or output_path.startswith("-"):
            raise AgentFailure("invalid_release_path")
        assert self.settings.release_repository is not None
        root = self.settings.release_repository.resolve()
        target = root / path
        if not target.resolve().is_relative_to(root) or any(
                part.is_symlink() for part in [target, *target.parents] if part.is_relative_to(root)):
            raise AgentFailure("invalid_release_path")
        if self.git("status", "--porcelain"):
            raise AgentFailure("release_target_dirty")
        head = self.git("rev-parse", "HEAD")
        return {"commit": head, "source": self.git("show", head + ":" + output_path, strip=False),
                "output_path": output_path, "ref": self.git("symbolic-ref", "--quiet", "HEAD")}

    def reconcile(self, intent_id: str, digest: str, output_path: str) -> dict[str, Any] | None:
        message = self.git("log", "-1", "--format=%B")
        if "SynqHarbor release " + intent_id not in message:
            return None
        content = self.git("show", "HEAD:" + output_path, strip=False)
        assert self.settings.release_repository is not None
        actual = (self.settings.release_repository / output_path).read_bytes()
        if token_hash(actual.decode()) != digest or content != actual.decode():
            raise AgentFailure("release_digest_mismatch")
        return {"target": "local_test_repository", "commit": self.git("rev-parse", "HEAD"),
                "content_hash": digest, "output_path": output_path}

    def apply(self, intent_id: str, snapshot: dict[str, str], content: str) -> dict[str, Any]:
        return self.apply_locked(intent_id, snapshot, content)

    def apply_locked(self, intent_id: str, snapshot: dict[str, str], content: str) -> dict[str, Any]:
        path = snapshot["output_path"]
        full = {"commit": snapshot["commit"], "files": {path: snapshot["source"]},
                "target": "local_test_repository", "ref": snapshot.get("ref") or self.git("symbolic-ref", "--quiet", "HEAD")}
        result = self.apply_files(intent_id, full, {path: content}, token_hash(content))
        return {"target": "local_test_repository", "commit": result["commit"],
                "content_hash": token_hash(content), "output_path": path}

    def snapshot_files(self, paths: list[str]) -> dict[str, Any]:
        files = {path: self.snapshot(path) for path in paths}
        head = self.git("rev-parse", "HEAD")
        ref = self.git("symbolic-ref", "--quiet", "HEAD")
        if any(file["commit"] != head or file["ref"] != ref for file in files.values()):
            raise AgentFailure("release_head_changed")
        if sum(len(file["source"].encode()) for file in files.values()) > self.settings.repository_context_bytes:
            raise AgentFailure("repository_context_limit")
        return {"commit": head, "ref": ref, "files": {path: file["source"] for path, file in files.items()}}

    def prepare_files(self, directory: Path, intent_id: str, snapshot: dict[str, Any],
                      files: dict[str, str]) -> tuple[str, bytes]:
        """Commit with the actual hooks in a disposable clone, leaving target untouched."""
        assert self.settings.release_repository is not None
        root = self.settings.release_repository.resolve()
        hooks = Path(self.git("config", "--path", "--default", ".git/hooks", "--get", "core.hooksPath"))
        hooks = hooks if hooks.is_absolute() else root / hooks
        if not (hooks / "pre-commit").is_file() or not os.access(hooks / "pre-commit", os.X_OK):
            raise AgentFailure("release_security_hook_missing")
        try:
            self.git("clone", "--shared", "--no-checkout", "--", str(root), str(directory))
            candidate = LocalRepository(self.settings, directory)
            for field in ("user.name", "user.email"):
                candidate.git("config", field, self.git("config", "--get", field))
            candidate.git("checkout", "-B", "synqharbor-preparation", snapshot["commit"])
            candidate.git("config", "core.splitIndex", "false")
            destination = directory / ".git/hooks"
            shutil.copytree(hooks, destination, dirs_exist_ok=True)
            candidate.git("config", "core.hooksPath", str(destination))
            candidate.snapshot_files(list(files))
            for path, content in files.items():
                (directory / path).write_bytes(content.encode("utf-8"))
            candidate.git("add", "--", *files)
            candidate.git("commit", "--allow-empty", "--only", "-m", "SynqHarbor release " + intent_id, "--", *files)
            # Verify commit bytes directly and reject hook-induced changes
            # in the isolated clone before target publication.
            commit = candidate.git("rev-parse", "HEAD")
            if candidate.git("rev-parse", "HEAD^") != snapshot["commit"]:
                raise AgentFailure("release_parent_mismatch")
            changed = set(candidate.git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines())
            if not changed.issubset(files) or candidate.git("status", "--porcelain"):
                raise AgentFailure("release_scope_mismatch")
            for path, content in files.items():
                if candidate.git("show", "HEAD:" + path, strip=False) != content:
                    raise AgentFailure("release_digest_mismatch")
            return commit, (directory / ".git/index").read_bytes()
        except AgentFailure as exc:
            raise AgentFailure("release_preparation_failed") from exc

    def publish_files(self, snapshot: dict[str, Any], files: dict[str, str],
                      commit: str, index: bytes) -> None:
        """CAS the target ref before installing bytes, holding Git's native index lock."""
        assert self.settings.release_repository is not None
        root = self.settings.release_repository
        lock = root / ".git/index.lock"
        # Preserve the operator's existing index access policy, including a
        # read-only ACL for an API snapshot identity distinct from the writer.
        index_mode = (root / ".git/index").stat().st_mode & 0o777
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise AgentFailure("release_target_busy") from exc
        owned = True
        try:
            with os.fdopen(descriptor, "wb") as output:
                os.fchmod(output.fileno(), index_mode)
                current = self.snapshot_files(list(files))
                if (current["commit"] != snapshot["commit"] or current["files"] != snapshot["files"]
                        or current["ref"] != snapshot["ref"]):
                    raise AgentFailure("release_head_changed")
                output.write(index)
                output.flush()
                os.fsync(output.fileno())
            try:
                # Git verifies the expected old OID atomically. No destination
                # working file has been written if this comparison rejects.
                self.git("update-ref", snapshot["ref"], commit, snapshot["commit"])
                for path, content in files.items():
                    (root / path).write_bytes(content.encode("utf-8"))
                os.replace(lock, root / ".git/index")
                owned = False
            except Exception as exc:
                raise AgentFailure("release_outcome_uncertain") from exc
        finally:
            if owned:
                lock.unlink(missing_ok=True)

    def reconcile_files(self, intent_id: str, snapshot: dict[str, Any],
                        files: dict[str, str], digest: str) -> dict[str, Any] | None:
        message = self.git("log", "-1", "--format=%B").splitlines()
        if "SynqHarbor release " + intent_id not in message:
            return None
        if self.git("rev-parse", "HEAD^") != snapshot["commit"]:
            raise AgentFailure("release_parent_mismatch")
        changed = set(self.git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines())
        if not changed.issubset(files):
            raise AgentFailure("release_scope_mismatch")
        hashes = {}
        for path, expected in files.items():
            # snapshot validates live path/symlink and a clean worktree as well.
            actual = self.snapshot(path)["source"]
            assert self.settings.release_repository is not None
            if actual != expected or (self.settings.release_repository / path).read_bytes() != expected.encode("utf-8"):
                raise AgentFailure("release_digest_mismatch")
            hashes[path] = token_hash(actual)
        return {"target": snapshot["target"], "commit": self.git("rev-parse", "HEAD"),
                "base_commit": snapshot["commit"], "content_hash": digest, "files": hashes}

    def apply_files(self, intent_id: str, snapshot: dict[str, Any],
                    files: dict[str, str], digest: str) -> dict[str, Any]:
        assert self.settings.release_repository is not None
        root = self.settings.release_repository
        # Historical multi-file snapshots pinned the base but predate ref names.
        snapshot = {**snapshot, "ref": snapshot.get("ref") or self.git("symbolic-ref", "--quiet", "HEAD")}
        with (root / ".git/synqharbor-release.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise AgentFailure("release_target_busy") from exc
            previous = self.reconcile_files(intent_id, snapshot, files, digest)
            if previous:
                return previous
            current = self.snapshot_files(list(files))
            if current["commit"] != snapshot["commit"] or current["files"] != snapshot["files"]:
                raise AgentFailure("release_head_changed")
            with tempfile.TemporaryDirectory(prefix="synqharbor-release-", dir=root / ".git") as temporary:
                directory = Path(temporary) / "candidate"
                commit, index = self.prepare_files(directory, intent_id, snapshot, files)
                # Transfer only objects, without changing refs or checkout.
                self.git("fetch", "--no-tags", "--no-write-fetch-head", "--", str(directory), commit)
                self.publish_files(snapshot, files, commit, index)
            try:
                result = self.reconcile_files(intent_id, snapshot, files, digest)
            except AgentFailure as exc:
                raise AgentFailure("release_outcome_uncertain") from exc
            if result is None:
                raise AgentFailure("release_outcome_uncertain")
            return result


def process_release(engine: Engine, settings: Settings) -> bool:
    if not settings.release_repository and not settings.repository_targets:
        return False
    # A crashed applying action is reconciled, never blindly replayed.
    with Session(engine) as db, db.begin():
        intent = db.scalar(select(ReleaseIntent).where(
            (ReleaseIntent.status == "queued") | ((ReleaseIntent.status == "applying") &
                                                  (ReleaseIntent.lease_until < now())))
                            .order_by(ReleaseIntent.id).limit(1).with_for_update())
        if not intent:
            return False
        uncertain = intent.status == "applying"
        intent_id = intent.id
        lease_until = now() + settings.run_lease_seconds
        changed = db.execute(update(ReleaseIntent).where(ReleaseIntent.id == intent.id,
                                                         ReleaseIntent.status == intent.status)
                             .values(status="applying", lease_until=lease_until)
                             .returning(ReleaseIntent.id))
        if changed.scalar_one_or_none() is None:
            return False
        delivery = db.get(Delivery, intent.delivery_id)
        run = db.get(AgentRun, intent.run_id)
        artifact = db.get(Artifact, delivery.artifact_id) if delivery else None
        task = db.get(Task, delivery.task_id) if delivery else None
        if not delivery or not run or not artifact or not task:
            raise AgentFailure("release_records_missing")
        content, digest = artifact.content, artifact.content_hash
        task_id, workspace_id, actor_id = task.id, delivery.workspace_id, delivery.actor_id
        run_inputs = run.inputs
        snapshot = run_inputs["repository"]
        artifact_id, run_id = artifact.id, run.id
    status, error, proof = "uncertain", None, {}
    repository = LocalRepository(settings)
    try:
        from .operations import execution_allowed, recheck_sources

        # Control endpoints and the host grant tool take this same database lock.
        # Keep it until Git verification ends: a stop/revocation either commits
        # first and blocks the action, or acknowledges after the action finishes.
        with Session(engine) as db, db.begin():
            lock_workspace(db, workspace_id)
            current = db.get(ReleaseIntent, intent_id)
            if not current or current.status != "applying" or current.lease_until != lease_until:
                raise AgentFailure("claim_lost")
            execution_allowed(db, workspace_id)
            recheck_sources(db, workspace_id, run_inputs)
            files = None
            if "target" in snapshot:
                from .repositories import patch_files, run_profile, target_path

                profile = run_profile(db, settings, workspace_id, snapshot)
                files = patch_files(content, profile, snapshot["commit"], snapshot["scope_hash"])
                repository = LocalRepository(settings, target_path(settings, snapshot["target"]))
            if uncertain:
                existing = (repository.reconcile_files(intent_id, snapshot, files, digest) if files is not None
                            else repository.reconcile(intent_id, digest, snapshot["output_path"]))
                if not existing:
                    raise AgentFailure("release_outcome_uncertain")
                proof, status = existing, "succeeded"
            else:
                requester = db.get(Membership, (workspace_id, actor_id))
                if not requester or requester.role not in {"owner", "developer"}:
                    raise AgentFailure("permission_revoked")
                task = db.get(Task, task_id)
                run = db.get(AgentRun, run_id)
                artifact = db.get(Artifact, artifact_id)
                if not task or not run or not artifact or task.version != artifact.version or run.status != "succeeded":
                    raise AgentFailure("release_approval_stale")
                decisions = list(db.scalars(select(Approval).where(Approval.artifact_id == artifact_id)))
                if {d.kind for d in decisions} != {"client", "developer"} or len({d.actor_id for d in decisions}) != 2:
                    raise AgentFailure("release_approval_stale")
                for decision in decisions:
                    membership = db.get(Membership, (workspace_id, decision.actor_id))
                    roles = {"owner", "client"} if decision.kind == "client" else {"owner", "developer"}
                    if not membership or membership.role not in roles:
                        raise AgentFailure("release_approval_stale")
                proof = (repository.apply_files(intent_id, snapshot, files, digest) if files is not None
                         else repository.apply(intent_id, snapshot, content))
                status = "succeeded"
    except AgentFailure as exc:
        error = str(exc)
        if error in {"release_head_changed", "release_approval_stale", "release_target_dirty",
                     "invalid_release_path", "release_security_hook_missing", "release_target_busy", "release_preparation_failed",
                     "repository_permission_revoked", "repository_scope_changed", "repository_unavailable",
                     "workspace_stopped", "source_permission_revoked", "permission_revoked",
                     "patch_scope_mismatch", "patch_base_mismatch", "invalid_patch", "patch_not_canonical"}:
            status = "failed"
        if uncertain:
            # Revocation or an operator stop must never turn an unknown external
            # outcome into a definite failure. Reconciliation performs no writes.
            status = "uncertain"
        # No retry of an external action with uncertain acceptance.
    except Exception:
        error = "release_outcome_uncertain"
    with Session(engine) as db, db.begin():
        task = db.scalar(select(Task).where(Task.id == task_id).with_for_update())
        result = db.execute(update(ReleaseIntent).where(ReleaseIntent.id == intent_id,
                                               ReleaseIntent.status == "applying",
                                               ReleaseIntent.lease_until == lease_until)
                   .values(status=status, error_code=error, receipt=proof, lease_until=None)
                   .returning(ReleaseIntent.id))
        if result.scalar_one_or_none() is not None:
            if task and status in {"succeeded", "failed"}:
                task.status = "complete" if status == "succeeded" else "review"
                task.revision += 1
            db.add(AuditEvent(workspace_id=workspace_id, actor_id=actor_id,
                              action="release." + status, resource_id=intent_id))
    return True
