"""Durable dispatch and fenced publication; external work stays outside transactions."""
import json
from dataclasses import dataclass
from difflib import unified_diff
from typing import Any

from sqlalchemy import Engine, func, select, update
from sqlalchemy.orm import Session

from .agent_contracts import Draft, Patch, Review, load_content
from .coordination import lock_workspace
from .models import AgentRun, Artifact, AuditEvent, Membership, RunEvent, Task, now
from .provider import Provider
from .provider_errors import AgentFailure
from .repositories import canonical_patch, run_profile
from .security import token, token_hash
from .settings import Settings

ACTIVE = ("queued", "running")


def event(db: Session, run: AgentRun, action: str) -> None:
    sequence = db.scalar(select(func.max(RunEvent.sequence)).where(RunEvent.run_id == run.id)) or 0
    db.add(RunEvent(run_id=run.id, sequence=sequence + 1, action=action))
    db.flush()


def has_active_run(db: Session, task_id: str) -> bool:
    return db.scalar(select(AgentRun.id).where(AgentRun.task_id == task_id,
                                              AgentRun.status.in_(ACTIVE))) is not None


@dataclass(frozen=True)
class Claim:
    id: str
    fence: str
    inputs: dict[str, Any]
    mode: str
    fixture: str | None


def recover(db: Session, settings: Settings) -> None:
    expired = list(db.scalars(select(AgentRun).where(AgentRun.status == "running",
                                                    AgentRun.lease_until < now()).with_for_update()))
    for run in expired:
        task = db.get(Task, run.task_id)
        run.fence, run.lease_until = None, None
        if task and task.revision == run.task_revision and run.attempt < settings.max_run_attempts:
            run.status = "queued"
            event(db, run, "lease.requeued")
        else:
            run.status, run.error_code, run.finished_at = "failed", "lease_expired", now()
            event(db, run, "lease.failed")


def claim(engine: Engine, settings: Settings) -> Claim | None:
    with Session(engine, expire_on_commit=False) as db, db.begin():
        recover(db, settings)
        candidate = db.scalar(select(AgentRun.id).where(AgentRun.status == "queued")
                              .order_by(AgentRun.created_at, AgentRun.id).limit(1))
        if candidate is None:
            return None
        fence = token()
        # Compare-and-set works on PostgreSQL and SQLite; losing claimants do no work.
        changed = db.execute(update(AgentRun).where(AgentRun.id == candidate,
                                                    AgentRun.status == "queued")
                             .values(status="running", fence=fence,
                                     lease_until=now() + settings.run_lease_seconds,
                                     attempt=AgentRun.attempt + 1).returning(AgentRun.id))
        if changed.scalar_one_or_none() is None:
            return None
        run = db.get(AgentRun, candidate)
        assert run is not None
        event(db, run, "run.claimed")
        return Claim(run.id, fence, run.inputs, run.mode, run.fixture)


class Worker:
    def __init__(self, engine: Engine, settings: Settings, provider: Provider) -> None:
        self.engine, self.settings, self.provider = engine, settings, provider

    def checkpoint(self, assignment: Claim, action: str) -> None:
        with Session(self.engine) as db, db.begin():
            run = db.scalar(select(AgentRun).where(AgentRun.id == assignment.id).with_for_update())
            if (not run or run.status != "running" or run.fence != assignment.fence
                    or not run.lease_until or run.lease_until <= now()):
                raise AgentFailure("claim_lost")
            task = db.get(Task, run.task_id)
            membership = db.get(Membership, (run.workspace_id, run.actor_id))
            if not task or task.revision != run.task_revision:
                raise AgentFailure("task_changed")
            if not membership or membership.role not in {"owner", "developer"}:
                raise AgentFailure("permission_revoked")
            if "target" in run.inputs.get("repository", {}):
                run_profile(db, self.settings, run.workspace_id, run.inputs["repository"])
            from .operations import execution_allowed, recheck_sources

            execution_allowed(db, run.workspace_id)
            recheck_sources(db, run.workspace_id, run.inputs)
            run.lease_until = now() + self.settings.run_lease_seconds
            event(db, run, action)

    def process(self, assignment: Claim) -> None:
        evidence: dict[str, Any] = {}
        try:
            prompts, fixtures = load_content(self.settings)
            builder_model = self.settings.builder_for(assignment.mode)
            if not builder_model or not self.settings.reviewer_model:
                raise AgentFailure("models_not_configured")
            data = dict(assignment.inputs)
            repository = assignment.inputs.get("repository", {})
            profile = None
            if "target" in repository:
                with Session(self.engine) as db:
                    run = db.get(AgentRun, assignment.id)
                    assert run is not None
                    profile = run_profile(db, self.settings, run.workspace_id, repository)
                data["profile"] = profile.public_specification()
            if assignment.mode == "code":
                if profile:
                    data["specification"] = profile.specification
                elif not assignment.fixture or assignment.fixture not in fixtures:
                    raise AgentFailure("fixture_unavailable")
                else:
                    fixture = fixtures[assignment.fixture]
                    data["specification"] = fixture.specification
                    data["source"] = repository.get("source", fixture.source)
            history: list[dict[str, Any]] = []
            evidence = {"iterations": history}
            for iteration in range(self.settings.max_builder_iterations):
                attempt: dict[str, Any] = {}
                history.append(attempt)
                try:
                    self.checkpoint(assignment, "builder.started")
                    if profile:
                        patch = Patch.model_validate_json(self.provider.generate(
                            builder_model, prompts.repository_coder, data, Patch))
                        draft = Draft(content=canonical_patch(patch, repository["commit"], profile,
                                                              repository["scope_hash"]), summary=patch.summary)
                        attempt["repository"] = {"target": repository["target"], "profile": repository["profile"],
                            "base_commit": repository["commit"], "scope_hash": repository["scope_hash"],
                            "changes": {path: {"before": token_hash(repository["files"][path]),
                                "after": token_hash(value), "diff": "".join(unified_diff(
                                    repository["files"][path].splitlines(keepends=True), value.splitlines(keepends=True),
                                    fromfile="a/" + path, tofile="b/" + path))} for path, value in patch.files.items()}}
                    else:
                        draft = Draft.model_validate_json(self.provider.generate(
                            builder_model,
                            prompts.coder if assignment.mode == "code" else prompts.builder, data, Draft))
                    attempt.update({"builder_model": builder_model,
                                    "reviewer_model": self.settings.reviewer_model,
                                    "content_hash": token_hash(draft.content),
                                    "summary": draft.summary, "candidate": draft.content})
                    self.checkpoint(assignment, "builder.finished")
                    citations = {s["id"]: s for s in assignment.inputs.get("sources", [])}
                    if (set(draft.citations) - citations.keys()
                            or (citations and assignment.mode == "draft" and not draft.citations)):
                        raise AgentFailure("invalid_model_output")
                    attempt["citations"] = [{k: citations[source][k] for k in ("id", "name", "content_hash", "created_at")}
                                            for source in dict.fromkeys(draft.citations)]
                    if assignment.mode == "code":
                        from .runner import CodeRunner

                        self.checkpoint(assignment, "tests.started")
                        if profile:
                            attempt["tests"] = CodeRunner(self.settings).test_files(
                                patch.files, profile, profile.entrypoint)
                        else:
                            attempt["tests"] = CodeRunner(self.settings).test(draft.content, fixture)
                        self.checkpoint(assignment, "tests.passed")
                    self.checkpoint(assignment, "reviewer.started")
                    # Reviewer sees original task and exact candidate, without Builder's
                    # corrective conversation or prior Reviewer judgments.
                    review_data = {**assignment.inputs, "artifact": draft.content,
                                   "protected_tests": attempt.get("tests"), "citations": attempt["citations"]}
                    if profile:
                        # A structured candidate is distinct from the base source.
                        # Double-encoding a patch as text makes small reviewers
                        # confuse the original tree with the proposed artifact.
                        review_data.pop("repository", None)
                        review_data["original_files"] = repository["files"]
                        review_data["artifact"] = json.loads(draft.content)
                        review_data["profile"] = profile.public_specification()
                    if assignment.mode == "code":
                        review_data["specification"] = profile.specification if profile else fixture.specification
                    review = Review.model_validate_json(self.provider.generate(
                        self.settings.reviewer_model, prompts.reviewer, review_data, Review))
                    attempt["review"] = review.model_dump()
                    if (not review.accepted or review.findings or not all(review.criterion_results)
                            or len(review.criterion_results) != len(data["criteria"])):
                        raise AgentFailure("review_rejected")
                    self.checkpoint(assignment, "reviewer.accepted")
                    evidence.update(attempt)
                    self.publish(assignment, draft.content, evidence)
                    return
                except AgentFailure as exc:
                    attempt["error_code"] = str(exc)
                    if (str(exc) not in {"protected_tests_failed", "review_rejected", "invalid_model_output"}
                            or iteration + 1 >= self.settings.max_builder_iterations):
                        raise
                    data["previous_candidate"] = attempt.get("candidate")
                    data["feedback"] = {"code": str(exc), "review": attempt.get("review")}
                    self.checkpoint(assignment, "builder.correction_requested")
        except AgentFailure as exc:
            self.fail(assignment, str(exc), evidence)
        except Exception:
            # Persist a safe diagnostic code, never model output, URLs or host paths.
            self.fail(assignment, "worker_error", evidence)

    def publish(self, assignment: Claim, content: str, evidence: dict[str, Any]) -> None:
        with Session(self.engine) as db, db.begin():
            task_id = db.scalar(select(AgentRun.task_id).where(AgentRun.id == assignment.id))
            workspace_id = db.scalar(select(AgentRun.workspace_id).where(AgentRun.id == assignment.id))
            if workspace_id is None:
                raise AgentFailure("claim_lost")
            lock_workspace(db, workspace_id)
            task = db.scalar(select(Task).where(Task.id == task_id).with_for_update())
            run = db.scalar(select(AgentRun).where(AgentRun.id == assignment.id).with_for_update())
            if (not run or run.status != "running" or run.fence != assignment.fence
                    or not run.lease_until or run.lease_until <= now()):
                raise AgentFailure("claim_lost")
            if not task or task.revision != run.task_revision:
                raise AgentFailure("task_changed")
            member = db.get(Membership, (run.workspace_id, run.actor_id))
            if not member or member.role not in {"owner", "developer"}:
                raise AgentFailure("permission_revoked")
            if "target" in run.inputs.get("repository", {}):
                run_profile(db, self.settings, run.workspace_id, run.inputs["repository"])
            from .operations import execution_allowed, recheck_sources

            execution_allowed(db, run.workspace_id)
            recheck_sources(db, run.workspace_id, run.inputs)
            if db.scalar(select(Artifact.id).where(Artifact.task_id == task.id,
                                                  Artifact.version == task.version)):
                task.version += 1
            artifact = Artifact(workspace_id=run.workspace_id, task_id=task.id,
                                version=task.version, content=content,
                                content_hash=token_hash(content), created_by=run.actor_id)
            db.add(artifact)
            db.flush()
            task.revision += 1
            task.status = "review"
            run.status, run.artifact_id, run.evidence = "succeeded", artifact.id, evidence
            run.finished_at, run.fence, run.lease_until = now(), None, None
            event(db, run, "artifact.published")
            db.add(AuditEvent(workspace_id=run.workspace_id, actor_id=run.actor_id,
                              action="run.succeeded", resource_id=run.id))

    def fail(self, assignment: Claim, code: str, evidence: dict[str, Any]) -> None:
        with Session(self.engine) as db, db.begin():
            run = db.scalar(select(AgentRun).where(AgentRun.id == assignment.id).with_for_update())
            if not run or run.status != "running" or run.fence != assignment.fence:
                return
            run.status, run.error_code, run.evidence = "failed", code, evidence
            run.finished_at, run.fence, run.lease_until = now(), None, None
            event(db, run, "run.failed")

    def once(self) -> bool:
        assignment = claim(self.engine, self.settings)
        if assignment is None:
            from .releases import process_release

            return process_release(self.engine, self.settings)
        self.process(assignment)
        return True
