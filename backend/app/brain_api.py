"""Authenticated job submission, evidence and approved internal delivery."""
import json
from collections.abc import Callable, Iterator
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .agent_contracts import load_content
from .brain import event, has_active_run
from .models import (
    AgentRun,
    Approval,
    Artifact,
    Delivery,
    Membership,
    ReleaseIntent,
    RepositoryGrant,
    RunEvent,
    Task,
    User,
    Workspace,
    now,
)
from .schemas import DeliveryInput, RunInput
from .security import token_hash
from .settings import Settings


def reject(status: int, code: str) -> None:
    raise HTTPException(status_code=status, detail={"code": code})


def run_data(db: Session, run: AgentRun) -> dict[str, Any]:
    events = db.scalars(select(RunEvent).where(RunEvent.run_id == run.id)
                        .order_by(RunEvent.sequence))
    return {"id": run.id, "task_id": run.task_id, "mode": run.mode, "status": run.status,
            "attempt": run.attempt, "artifact_id": run.artifact_id, "evidence": run.evidence,
            "error_code": run.error_code, "created_at": run.created_at,
            "finished_at": run.finished_at,
            "events": [{"sequence": e.sequence, "action": e.action,
                        "created_at": e.created_at} for e in events]}


def receipt(db: Session, delivery: Delivery) -> dict[str, Any]:
    release = db.scalar(select(ReleaseIntent).where(ReleaseIntent.delivery_id == delivery.id))
    return {"id": delivery.id, "task_id": delivery.task_id, "artifact_id": delivery.artifact_id,
            "content_hash": delivery.content_hash, "created_at": delivery.created_at,
            "destination": "local_test_repository" if release else "internal_artifact",
            "external_deployment": False,
            "release": {"status": release.status, "error_code": release.error_code,
                        "receipt": release.receipt} if release else None}


def install_brain_routes(
    app: FastAPI, config: Settings, database: Callable[[], Iterator[Session]],
    actor: Callable[..., User], member: Callable[..., Membership],
    task_record: Callable[[Session, str, str, int], Task],
    audit: Callable[[Session, str, User, str, str], None],
) -> None:
    prefix = config.api_prefix

    @app.get(prefix + "/capabilities")
    def capabilities(user: Annotated[User, Depends(actor)]) -> dict[str, Any]:
        _, fixtures = load_content(config)
        inference = bool(config.inference_url and config.builder_model and config.reviewer_model)
        runner = bool(config.runner_binary and config.runner_rootfs and config.runner_directory)
        return {"inference_configured": inference, "runner_configured": runner,
                "execution": "separate_worker", "paid_providers": False,
                "fixtures": [{"id": key, "name": fixture.name,
                              "specification": fixture.specification} for key, fixture in fixtures.items()]}

    @app.get(prefix + "/workspaces/{workspace_id}/repositories")
    def repositories(workspace_id: str, user: Annotated[User, Depends(actor)],
                     db: Annotated[Session, Depends(database, scope="function")]) -> list[dict[str, Any]]:
        member(db, workspace_id, user)
        from .provider_errors import AgentFailure
        from .repositories import authorized_profile

        result = []
        for grant in db.scalars(select(RepositoryGrant).where(RepositoryGrant.workspace_id == workspace_id)):
            try:
                profile = authorized_profile(db, config, workspace_id, grant.target, grant.profile)
            except AgentFailure:
                continue
            result.append({"target": grant.target, "profile": grant.profile, **profile.public_specification()})
        return result

    @app.post(prefix + "/workspaces/{workspace_id}/tasks/{task_id}/runs", status_code=201)
    def submit(workspace_id: str, task_id: str, payload: RunInput,
               user: Annotated[User, Depends(actor)],
               db: Annotated[Session, Depends(database, scope="function")]) -> dict[str, Any]:
        member(db, workspace_id, user, {"owner", "developer"})
        fingerprint = token_hash(json.dumps({"task_id": task_id, **payload.model_dump(exclude={"request_key"})}, sort_keys=True))
        previous = db.scalar(select(AgentRun).where(AgentRun.workspace_id == workspace_id,
                                                   AgentRun.request_key == payload.request_key))
        if previous:
            if previous.request_hash != fingerprint:
                reject(409, "idempotency_conflict")
            return run_data(db, previous)
        from .operations import execution_allowed, source_snapshots
        from .provider_errors import AgentFailure

        db.scalar(select(Workspace).where(Workspace.id == workspace_id).with_for_update())
        try:
            execution_allowed(db, workspace_id)
        except AgentFailure as exc:
            reject(409, str(exc))
        active = db.scalar(select(func.count()).select_from(AgentRun).where(
            AgentRun.workspace_id == workspace_id, AgentRun.status.in_(["queued", "running"]))) or 0
        if active >= config.max_active_runs:
            reject(409, "workspace_queue_limit")
        task = task_record(db, workspace_id, task_id, payload.revision)
        if not task.criteria:
            reject(409, "acceptance_criteria_required")
        if has_active_run(db, task.id):
            reject(409, "run_already_active")
        if not config.inference_url or not config.builder_model or not config.reviewer_model:
            reject(503, "inference_not_configured")
        repository_profile = None
        if payload.repository is not None or payload.profile is not None:
            if payload.mode != "code" or payload.fixture or not payload.repository or not payload.profile:
                reject(422, "invalid_repository_request")
            from .provider_errors import AgentFailure
            from .repositories import authorized_profile

            try:
                assert payload.repository is not None and payload.profile is not None
                repository_profile = authorized_profile(db, config, workspace_id, payload.repository, payload.profile)
            except AgentFailure as exc:
                reject(403, str(exc))
        if payload.mode == "code":
            _, fixtures = load_content(config)
            if not repository_profile and payload.fixture not in fixtures:
                reject(422, "fixture_unavailable")
            if not config.runner_binary or not config.runner_rootfs or not config.runner_directory:
                reject(503, "runner_not_configured")
        elif payload.fixture is not None:
            reject(422, "unexpected_fixture")
        count = db.scalar(select(func.count()).select_from(AgentRun)
                          .where(AgentRun.workspace_id == workspace_id)) or 0
        if count >= config.max_runs:
            reject(409, "collection_limit")
        inputs: dict[str, Any] = {"title": task.title, "description": task.description, "criteria": task.criteria}
        if payload.source_ids:
            try:
                inputs["sources"] = source_snapshots(db, workspace_id, payload.source_ids)
            except AgentFailure:
                reject(404, "not_found")
            if len(json.dumps(inputs["sources"]).encode()) > config.source_context_bytes:
                reject(422, "source_context_limit")
        if repository_profile:
            from .provider_errors import AgentFailure
            from .releases import LocalRepository
            from .repositories import scope_hash, target_path

            try:
                assert payload.repository is not None
                inputs["repository"] = LocalRepository(config, target_path(config, payload.repository)).snapshot_files(
                    repository_profile.files)
                inputs["repository"].update({"target": payload.repository, "profile": payload.profile,
                    "scope_hash": scope_hash(config, payload.repository, repository_profile)})
            except AgentFailure as exc:
                reject(409, str(exc))
        task.status, task.revision = "progress", task.revision + 1
        db.flush()
        run = AgentRun(workspace_id=workspace_id, task_id=task.id, actor_id=user.id,
                       request_key=payload.request_key, request_hash=fingerprint,
                       mode=payload.mode, fixture=payload.fixture,
                       inputs=inputs, task_revision=task.revision)
        db.add(run)
        db.flush()
        event(db, run, "run.queued")
        audit(db, workspace_id, user, "run.queued", run.id)
        return run_data(db, run)

    @app.get(prefix + "/workspaces/{workspace_id}/runs")
    def runs(workspace_id: str, user: Annotated[User, Depends(actor)],
             db: Annotated[Session, Depends(database, scope="function")]) -> list[dict[str, Any]]:
        member(db, workspace_id, user)
        rows = db.scalars(select(AgentRun).where(AgentRun.workspace_id == workspace_id)
                          .order_by(AgentRun.created_at.desc(), AgentRun.id).limit(config.list_limit))
        return [run_data(db, run) for run in rows]

    @app.post(prefix + "/workspaces/{workspace_id}/runs/{run_id}/cancel")
    def cancel(workspace_id: str, run_id: str, user: Annotated[User, Depends(actor)],
               db: Annotated[Session, Depends(database, scope="function")]) -> dict[str, Any]:
        member(db, workspace_id, user, {"owner", "developer"})
        task_id = db.scalar(select(AgentRun.task_id).where(AgentRun.id == run_id,
                                                          AgentRun.workspace_id == workspace_id))
        # Same lock order as publication/delivery: task, then run.
        db.scalar(select(Task).where(Task.id == task_id).with_for_update())
        run = db.scalar(select(AgentRun).where(AgentRun.id == run_id,
                                              AgentRun.workspace_id == workspace_id).with_for_update())
        if not run:
            reject(404, "not_found")
        assert run is not None
        if run.status in {"queued", "running"}:
            run.status, run.fence, run.lease_until, run.finished_at = "cancelled", None, None, now()
            event(db, run, "run.cancelled")
            audit(db, workspace_id, user, "run.cancelled", run.id)
        return run_data(db, run)

    @app.post(prefix + "/workspaces/{workspace_id}/tasks/{task_id}/deliveries", status_code=201)
    def deliver(workspace_id: str, task_id: str, payload: DeliveryInput,
                user: Annotated[User, Depends(actor)],
                db: Annotated[Session, Depends(database, scope="function")]) -> dict[str, Any]:
        member(db, workspace_id, user, {"owner", "developer"})
        existing = db.scalar(select(Delivery).where(Delivery.workspace_id == workspace_id,
                                                    Delivery.request_key == payload.request_key))
        if existing:
            previous_artifact = db.get(Artifact, existing.artifact_id)
            if (existing.task_id != task_id or existing.content_hash != payload.content_hash
                    or not previous_artifact or previous_artifact.version != payload.version):
                reject(409, "idempotency_conflict")
            return receipt(db, existing)
        task = task_record(db, workspace_id, task_id, payload.revision)
        artifact = db.scalar(select(Artifact).where(Artifact.task_id == task.id,
                                                    Artifact.version == task.version,
                                                    Artifact.content_hash == payload.content_hash))
        if not artifact or task.version != payload.version or task.status != "review":
            reject(409, "stale_delivery")
        assert artifact is not None
        run = db.scalar(select(AgentRun).where(AgentRun.artifact_id == artifact.id,
                                              AgentRun.status == "succeeded"))
        if not run:
            reject(409, "verified_run_required")
        assert run is not None
        from .operations import execution_allowed, recheck_sources
        from .provider_errors import AgentFailure

        try:
            execution_allowed(db, workspace_id)
            recheck_sources(db, workspace_id, run.inputs)
        except AgentFailure as exc:
            reject(409, str(exc))
        if "target" in run.inputs.get("repository", {}):
            from .provider_errors import AgentFailure
            from .repositories import run_profile

            try:
                run_profile(db, config, workspace_id, run.inputs["repository"])
            except AgentFailure as exc:
                reject(409, str(exc))
        approvals = list(db.scalars(select(Approval).where(Approval.artifact_id == artifact.id)))
        if {a.kind for a in approvals} != {"client", "developer"} or len({a.actor_id for a in approvals}) != 2:
            reject(409, "approvals_required")
        for approval in approvals:
            roles = {"owner", "client"} if approval.kind == "client" else {"owner", "developer"}
            member_record = db.get(Membership, (workspace_id, approval.actor_id))
            if not member_record or member_record.role not in roles:
                reject(409, "approval_permission_revoked")
        delivery = Delivery(workspace_id=workspace_id, task_id=task.id, artifact_id=artifact.id,
                            actor_id=user.id, request_key=payload.request_key,
                            content_hash=artifact.content_hash)
        db.add(delivery)
        task.status, task.revision = "complete", task.revision + 1
        db.flush()
        if run.mode == "code" and "repository" in run.inputs:
            db.add(ReleaseIntent(delivery_id=delivery.id, workspace_id=workspace_id, run_id=run.id))
            task.status = "progress"
            db.flush()
        audit(db, workspace_id, user, "delivery.recorded", delivery.id)
        return receipt(db, delivery)

    @app.get(prefix + "/workspaces/{workspace_id}/deliveries")
    def deliveries(workspace_id: str, user: Annotated[User, Depends(actor)],
                   db: Annotated[Session, Depends(database, scope="function")]) -> list[dict[str, Any]]:
        member(db, workspace_id, user)
        return [receipt(db, d) for d in db.scalars(select(Delivery)
                .where(Delivery.workspace_id == workspace_id)
                .order_by(Delivery.created_at.desc()).limit(config.list_limit))]

    @app.post(prefix + "/workspaces/{workspace_id}/deliveries/{delivery_id}/reconcile")
    def reconcile_delivery(workspace_id: str, delivery_id: str,
                           user: Annotated[User, Depends(actor)],
                           db: Annotated[Session, Depends(database, scope="function")]) -> dict[str, Any]:
        member(db, workspace_id, user, {"owner", "developer"})
        delivery = db.scalar(select(Delivery).where(Delivery.id == delivery_id,
                                                    Delivery.workspace_id == workspace_id))
        if not delivery:
            reject(404, "not_found")
        assert delivery is not None
        db.scalar(select(Task).where(Task.id == delivery.task_id).with_for_update())
        intent = db.scalar(select(ReleaseIntent).where(ReleaseIntent.delivery_id == delivery.id)
                           .with_for_update())
        if intent and intent.status == "uncertain":
            intent.status, intent.lease_until = "applying", now() - 1
            audit(db, workspace_id, user, "release.reconciliation_requested", intent.id)
            db.flush()
        return receipt(db, delivery)

    @app.get(prefix + "/workspaces/{workspace_id}/deliveries/{delivery_id}/report")
    def delivery_report(workspace_id: str, delivery_id: str, user: Annotated[User, Depends(actor)],
                        db: Annotated[Session, Depends(database, scope="function")]) -> JSONResponse:
        member(db, workspace_id, user)
        delivery = db.scalar(select(Delivery).where(Delivery.id == delivery_id,
                                                    Delivery.workspace_id == workspace_id))
        if not delivery:
            reject(404, "not_found")
        assert delivery is not None
        artifact = db.get(Artifact, delivery.artifact_id)
        run = db.scalar(select(AgentRun).where(AgentRun.artifact_id == delivery.artifact_id))
        if not artifact or not run:
            reject(409, "delivery_evidence_missing")
        assert artifact is not None and run is not None
        decisions = list(db.scalars(select(Approval).where(Approval.artifact_id == artifact.id)))
        report = {"schema": "synqharbor.delivery.v1", "delivery": receipt(db, delivery),
            "request": {"task_id": run.task_id, "title": run.inputs["title"],
                        "description": run.inputs["description"], "criteria": run.inputs["criteria"]},
            "artifact": {"id": artifact.id, "version": artifact.version, "content_hash": artifact.content_hash},
            "run": {"id": run.id, "status": run.status, "attempt": run.attempt,
                    "created_at": run.created_at, "finished_at": run.finished_at},
            "evidence": {key: run.evidence.get(key) for key in
                         ["tests", "review", "citations", "repository", "builder_model", "reviewer_model"]},
            "approvals": [{"kind": decision.kind, "actor_id": decision.actor_id,
                           "artifact_id": decision.artifact_id, "created_at": decision.created_at} for decision in decisions]}
        return JSONResponse(report, headers={"Content-Disposition": "attachment; filename=delivery-report.json"})
