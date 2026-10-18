"""Operator-owned repository scopes and canonical multi-file artifacts."""
import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from .agent_contracts import Patch, RepositoryProfile, load_profiles
from .coordination import lock_workspace
from .models import RepositoryGrant, Workspace
from .provider_errors import AgentFailure
from .schemas import ARTIFACT_MAX
from .security import token_hash
from .settings import Settings


def target_path(settings: Settings, target: str) -> Path:
    path = settings.repository_targets.get(target)
    if path is None:
        raise AgentFailure("repository_unavailable")
    return path.resolve()


def scope_hash(settings: Settings, target: str, profile: RepositoryProfile) -> str:
    return token_hash(json.dumps({"target": str(target_path(settings, target)),
                                  "profile": profile.model_dump()}, sort_keys=True))


def authorized_profile(db: Session, settings: Settings, workspace_id: str,
                       target: str, profile_id: str) -> RepositoryProfile:
    grant = db.get(RepositoryGrant, (workspace_id, target, profile_id))
    profile = load_profiles(settings).get(profile_id)
    if not grant or not profile or grant.scope_hash != scope_hash(settings, target, profile):
        raise AgentFailure("repository_permission_revoked")
    return profile


def update_repository_grant(db: Session, settings: Settings, workspace_id: str,
                            target: str, profile_id: str, *, allowed: bool) -> None:
    """Host-operator transaction; serializes grant changes with external writes."""
    lock_workspace(db, workspace_id)
    if db.get(Workspace, workspace_id) is None:
        raise ValueError("Workspace does not exist")
    record = db.get(RepositoryGrant, (workspace_id, target, profile_id))
    if not allowed:
        if record:
            db.delete(record)
        return
    profile = load_profiles(settings)[profile_id]
    digest = scope_hash(settings, target, profile)
    if record:
        record.scope_hash = digest
    else:
        db.add(RepositoryGrant(workspace_id=workspace_id, target=target,
                               profile=profile_id, scope_hash=digest))


def canonical_patch(patch: Patch, base_commit: str, profile: RepositoryProfile, scope: str = "") -> str:
    if set(patch.files) != set(profile.files) or any(not value for value in patch.files.values()):
        raise AgentFailure("patch_scope_mismatch")
    content = json.dumps({"base_commit": base_commit, "scope_hash": scope, "files": patch.files},
                         sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    if len(content.encode()) > ARTIFACT_MAX:
        raise AgentFailure("patch_size_limit")
    return content


def patch_files(content: str, profile: RepositoryProfile, base_commit: str, scope: str = "") -> dict[str, str]:
    try:
        data: dict[str, Any] = json.loads(content)
        if (set(data) != {"base_commit", "scope_hash", "files"}
                or data["base_commit"] != base_commit or data["scope_hash"] != scope):
            raise AgentFailure("patch_base_mismatch")
        patch = Patch(files=data["files"], summary="Validated artifact")
        if canonical_patch(patch, base_commit, profile, scope) != content:
            raise AgentFailure("patch_not_canonical")
        return patch.files
    except (ValueError, TypeError) as exc:
        raise AgentFailure("invalid_patch") from exc


def run_profile(db: Session, settings: Settings, workspace_id: str,
                snapshot: dict[str, Any]) -> RepositoryProfile:
    profile = authorized_profile(db, settings, workspace_id, snapshot["target"], snapshot["profile"])
    if snapshot["scope_hash"] != scope_hash(settings, snapshot["target"], profile):
        raise AgentFailure("repository_scope_changed")
    return profile
