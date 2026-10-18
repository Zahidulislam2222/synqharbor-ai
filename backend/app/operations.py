"""Workspace stop, membership/session revocation and scoped source snapshots."""
from collections.abc import Callable, Iterator
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from .brain import event
from .coordination import lock_workspace
from .models import (
    AgentRun,
    KnowledgeSource,
    LoginSession,
    Membership,
    Task,
    User,
    WorkspaceExecution,
    now,
)
from .provider_errors import AgentFailure
from .schemas import ExecutionInput, SourceInput
from .security import token_hash
from .settings import Settings


def execution_allowed(db: Session, workspace_id: str) -> None:
    control = db.get(WorkspaceExecution, workspace_id)
    if control and control.stopped:
        raise AgentFailure("workspace_stopped")


def source_snapshots(db: Session, workspace_id: str, ids: list[str]) -> list[dict[str, Any]]:
    result = []
    for source_id in dict.fromkeys(ids):
        source = db.get(KnowledgeSource, source_id)
        if not source or source.workspace_id != workspace_id or source.revoked_at:
            raise AgentFailure("source_permission_revoked")
        result.append({"id": source.id, "name": source.name, "text": source.text,
                       "content_hash": source.content_hash, "created_at": source.created_at})
    return result


def recheck_sources(db: Session, workspace_id: str, inputs: dict[str, Any]) -> None:
    original = inputs.get("sources", [])
    current = source_snapshots(db, workspace_id, [s["id"] for s in original])
    if current != original:
        raise AgentFailure("source_permission_revoked")


def install_operations(app: FastAPI, config: Settings, database: Callable[[], Iterator[Session]],
                       actor: Callable[..., User], member: Callable[..., Membership],
                       audit: Callable[[Session, str, User, str, str], None]) -> None:
    prefix = config.api_prefix

    @app.post(prefix + "/auth/revoke-sessions", status_code=204)
    def revoke_sessions(user: Annotated[User, Depends(actor)],
                        db: Annotated[Session, Depends(database, scope="function")]) -> None:
        db.execute(delete(LoginSession).where(LoginSession.user_id == user.id))

    @app.delete(prefix + "/workspaces/{workspace_id}/members/{user_id}", status_code=204)
    def remove_member(workspace_id: str, user_id: str, user: Annotated[User, Depends(actor)],
                      db: Annotated[Session, Depends(database, scope="function")]) -> None:
        lock_workspace(db, workspace_id)
        member(db, workspace_id, user, {"owner"})
        record = db.get(Membership, (workspace_id, user_id))
        if not record:
            raise HTTPException(404, detail={"code": "not_found"})
        if record.role == "owner":
            raise HTTPException(409, detail={"code": "owner_cannot_be_removed"})
        db.delete(record)
        audit(db, workspace_id, user, "member.revoked", user_id)

    @app.get(prefix + "/workspaces/{workspace_id}/execution")
    def execution(workspace_id: str, user: Annotated[User, Depends(actor)],
                  db: Annotated[Session, Depends(database, scope="function")]) -> dict[str, bool]:
        member(db, workspace_id, user)
        record = db.get(WorkspaceExecution, workspace_id)
        return {"stopped": bool(record and record.stopped)}

    @app.put(prefix + "/workspaces/{workspace_id}/execution")
    def set_execution(workspace_id: str, payload: ExecutionInput, user: Annotated[User, Depends(actor)],
                      db: Annotated[Session, Depends(database, scope="function")]) -> dict[str, bool]:
        lock_workspace(db, workspace_id)
        member(db, workspace_id, user, {"owner"})
        record = db.get(WorkspaceExecution, workspace_id)
        if not record:
            record = WorkspaceExecution(workspace_id=workspace_id)
            db.add(record)
        record.stopped = payload.stopped
        if payload.stopped:
            candidates = list(db.scalars(select(AgentRun).where(AgentRun.workspace_id == workspace_id,
                                                                AgentRun.status.in_(["queued", "running"]))))
            for candidate in candidates:
                task = db.scalar(select(Task).where(Task.id == candidate.task_id).with_for_update())
                run = db.scalar(select(AgentRun).where(AgentRun.id == candidate.id).with_for_update()
                                .execution_options(populate_existing=True))
                if run and run.status in {"queued", "running"}:
                    run.status, run.error_code = "cancelled", "workspace_stopped"
                    run.fence, run.lease_until, run.finished_at = None, None, now()
                    event(db, run, "workspace.stopped")
                    if task and task.revision == run.task_revision:
                        task.status, task.revision = "planned", task.revision + 1
        audit(db, workspace_id, user, "workspace.stopped" if payload.stopped else "workspace.resumed", workspace_id)
        return {"stopped": payload.stopped}

    @app.get(prefix + "/workspaces/{workspace_id}/sources")
    def sources(workspace_id: str, user: Annotated[User, Depends(actor)],
                db: Annotated[Session, Depends(database, scope="function")]) -> list[dict[str, Any]]:
        member(db, workspace_id, user)
        rows = db.scalars(select(KnowledgeSource).where(KnowledgeSource.workspace_id == workspace_id,
                                                       KnowledgeSource.revoked_at.is_(None))
                          .order_by(KnowledgeSource.created_at.desc()).limit(config.list_limit))
        return [{"id": row.id, "name": row.name, "text": row.text,
                 "content_hash": row.content_hash, "created_at": row.created_at} for row in rows]

    @app.post(prefix + "/workspaces/{workspace_id}/sources", status_code=201)
    def add_source(workspace_id: str, payload: SourceInput, user: Annotated[User, Depends(actor)],
                   db: Annotated[Session, Depends(database, scope="function")]) -> dict[str, str]:
        member(db, workspace_id, user, {"owner", "developer", "client"})
        if "\x00" in payload.text or "PRIVATE KEY-----" in payload.text:
            raise HTTPException(422, detail={"code": "source_rejected"})
        count = db.scalar(select(func.count()).select_from(KnowledgeSource)
                          .where(KnowledgeSource.workspace_id == workspace_id)) or 0
        if count >= config.max_sources:
            raise HTTPException(409, detail={"code": "collection_limit"})
        source = KnowledgeSource(workspace_id=workspace_id, created_by=user.id, name=payload.name,
                                 text=payload.text, content_hash=token_hash(payload.text))
        db.add(source)
        db.flush()
        audit(db, workspace_id, user, "source.added", source.id)
        return {"id": source.id, "content_hash": source.content_hash}

    @app.delete(prefix + "/workspaces/{workspace_id}/sources/{source_id}", status_code=204)
    def revoke_source(workspace_id: str, source_id: str, user: Annotated[User, Depends(actor)],
                      db: Annotated[Session, Depends(database, scope="function")]) -> None:
        lock_workspace(db, workspace_id)
        member(db, workspace_id, user, {"owner", "developer"})
        source = db.get(KnowledgeSource, source_id)
        if not source or source.workspace_id != workspace_id:
            raise HTTPException(404, detail={"code": "not_found"})
        source.revoked_at = now()
        audit(db, workspace_id, user, "source.revoked", source.id)
