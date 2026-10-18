"""Same-origin authenticated collaboration API. No model or shell execution."""
import hmac
from collections.abc import Iterator
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from pwdlib import PasswordHash
from sqlalchemy import delete, func, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .brain_api import install_brain_routes
from .database import make_engine, schema_current
from .models import (
    Approval,
    Artifact,
    AuditEvent,
    ContactRequest,
    Delivery,
    Invitation,
    LoginSession,
    Membership,
    Message,
    Preferences,
    RateBucket,
    ReleaseIntent,
    Task,
    User,
    Workspace,
    now,
)
from .operations import install_operations
from .schemas import (
    TEXT_MAX,
    AcceptInvitation,
    ApprovalInput,
    ArtifactInput,
    ContactInput,
    Credentials,
    InvitationInput,
    MessageInput,
    PreferencesInput,
    Registration,
    TaskChange,
    TaskInput,
    WorkspaceInput,
)
from .security import BodyLimit, csrf_token, token, token_hash
from .settings import Settings, get_settings


def reject(status: int, code: str) -> None:
    raise HTTPException(status_code=status, detail={"code": code})


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or get_settings()
    engine = make_engine(config)
    app = FastAPI(title=config.api_title, version=config.release,
                  docs_url=None,
                  openapi_url=config.api_prefix + "/openapi.json", redoc_url=None)
    app.state.engine, app.state.settings = engine, config
    password_hash = PasswordHash.recommended()
    dummy_password = password_hash.hash(token())
    secret = config.session_secret.get_secret_value()
    prefix = config.api_prefix

    def database() -> Iterator[Session]:
        with Session(engine, expire_on_commit=False) as db:
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise

    def throttle(key: str, limit: int) -> None:
        window = now() // config.rate_window_seconds
        identity = token_hash(str(window) + ":" + key)
        with Session(engine) as db:
            db.execute(delete(RateBucket).where(RateBucket.expires_at < now()))
            # Atomic increment; unique insertion races reject rather than exceed the cap.
            result = db.execute(update(RateBucket).where(RateBucket.id == identity)
                                .values(count=RateBucket.count + 1).returning(RateBucket.count))
            count = result.scalar_one_or_none()
            if count is None:
                db.add(RateBucket(id=identity, count=1,
                                  expires_at=(window + 1) * config.rate_window_seconds))
                try:
                    db.commit()
                except IntegrityError:
                    reject(429, "rate_limit")
                count = 1
            else:
                db.commit()
            if count > limit:
                reject(429, "rate_limit")

    def session_record(request: Request, db: Session) -> LoginSession:
        raw = request.cookies.get(config.cookie_name, "")
        session = db.get(LoginSession, token_hash(raw)) if raw else None
        if not session or session.expires_at <= now():
            reject(401, "authentication_required")
        assert session is not None
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            expected = csrf_token(secret, raw)
            if (request.headers.get("origin") != config.public_origin
                    or not hmac.compare_digest(request.headers.get("x-csrf-token", ""), expected)):
                reject(403, "csrf_failed")
        return session

    def actor(request: Request, db: Annotated[Session, Depends(database, scope="function")]) -> User:
        session = session_record(request, db)
        user = db.get(User, session.user_id) if session.user_id else None
        if not user:
            reject(401, "authentication_required")
        assert user is not None
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            throttle("write:" + user.id, config.write_rate_limit)
        return user

    def member(db: Session, workspace_id: str, user: User,
               roles: set[str] | None = None) -> Membership:
        membership = db.get(Membership, (workspace_id, user.id))
        if not membership:
            reject(404, "not_found")
        assert membership is not None
        if roles and membership.role not in roles:
            reject(403, "permission_denied")
        return membership

    def task_record(db: Session, workspace_id: str, task_id: str, revision: int) -> Task:
        task = db.scalar(select(Task).where(Task.id == task_id, Task.workspace_id == workspace_id)
                         .with_for_update())
        if not task:
            reject(404, "not_found")
        assert task is not None
        if task.revision != revision:
            reject(409, "stale_revision")
        pending_release = db.scalar(select(ReleaseIntent.id).join(Delivery)
                                   .where(Delivery.task_id == task.id,
                                          ReleaseIntent.status.in_(["queued", "applying", "uncertain"])))
        if pending_release:
            reject(409, "release_in_progress")
        return task

    def audit(db: Session, workspace: str, user: User, action: str, resource: str) -> None:
        db.add(AuditEvent(workspace_id=workspace, actor_id=user.id,
                          action=action, resource_id=resource))

    def new_session(db: Session, response: Response, user_id: str | None) -> str:
        raw = token()
        db.add(LoginSession(token_hash=token_hash(raw), user_id=user_id,
                            expires_at=now() + config.session_hours * 3600))
        response.set_cookie(config.cookie_name, raw, httponly=True, secure=config.secure_cookies,
                            samesite="lax", path="/", max_age=config.session_hours * 3600)
        return csrf_token(secret, raw)

    def user_data(user: User) -> dict[str, str]:
        return {"id": user.id, "name": user.name, "email": user.email}

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, __: RequestValidationError) -> JSONResponse:
        return JSONResponse({"detail": {"code": "invalid_input"}}, status_code=422)

    @app.exception_handler(StaleDataError)
    async def stale_error(_: Request, __: StaleDataError) -> JSONResponse:
        return JSONResponse({"detail": {"code": "stale_revision"}}, status_code=409)

    @app.exception_handler(IntegrityError)
    async def conflict_error(_: Request, __: IntegrityError) -> JSONResponse:
        return JSONResponse({"detail": {"code": "conflict"}}, status_code=409)

    @app.middleware("http")
    async def headers(request: Request, call_next: Any) -> Response:
        response: Response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        return response

    @app.get(prefix + "/health")
    def health(db: Annotated[Session, Depends(database, scope="function")]) -> dict[str, str]:
        db.execute(text("SELECT 1"))
        if not schema_current(db.connection()):
            reject(503, "migration_required")
        return {"status": "available", "release": config.release}

    @app.get(prefix + "/auth/session")
    def current_session(request: Request, response: Response,
                        db: Annotated[Session, Depends(database, scope="function")]) -> dict[str, Any]:
        # Proxy identity is deliberately not accepted from arbitrary forwarded headers.
        raw = request.cookies.get(config.cookie_name, "")
        session = db.get(LoginSession, token_hash(raw)) if raw else None
        valid_session = session is not None and session.expires_at > now()
        host = request.client.host if request.client else "unknown"
        # An established browser has its own budget even when a trusted reverse
        # proxy connects every request from the same loopback address.
        throttle("session:" + (token_hash(raw) if valid_session else host), config.session_rate_limit)
        db.execute(delete(LoginSession).where(LoginSession.expires_at < now()))
        if session and session.expires_at > now():
            user = db.get(User, session.user_id) if session.user_id else None
            return {"user": user_data(user) if user else None, "csrf": csrf_token(secret, raw)}
        return {"user": None, "csrf": new_session(db, response, None)}

    @app.post(prefix + "/auth/register", status_code=201)
    def register(payload: Registration, request: Request, response: Response,
                 db: Annotated[Session, Depends(database, scope="function")]) -> dict[str, Any]:
        old = session_record(request, db)
        if not config.registration_enabled:
            reject(403, "registration_closed")
        email = str(payload.email).lower()
        throttle("registration:" + token_hash(request.cookies.get(config.cookie_name, "")), config.auth_rate_limit)
        throttle("auth:" + email, config.auth_rate_limit)
        if db.scalar(select(User.id).where(User.email == email)):
            reject(409, "account_unavailable")
        user = User(email=email, name=payload.name, password_hash=password_hash.hash(payload.password))
        db.add(user)
        db.flush()
        db.delete(old)
        return {"user": user_data(user), "csrf": new_session(db, response, user.id)}

    @app.post(prefix + "/auth/login")
    def login(payload: Credentials, request: Request, response: Response,
              db: Annotated[Session, Depends(database, scope="function")]) -> dict[str, Any]:
        old = session_record(request, db)
        email = str(payload.email).lower()
        throttle("auth:" + email, config.auth_rate_limit)
        user = db.scalar(select(User).where(User.email == email))
        if not password_hash.verify(payload.password, user.password_hash if user else dummy_password):
            reject(401, "invalid_credentials")
        assert user is not None
        db.delete(old)
        return {"user": user_data(user), "csrf": new_session(db, response, user.id)}

    @app.post(prefix + "/auth/logout", status_code=204)
    def logout(request: Request, response: Response,
               db: Annotated[Session, Depends(database, scope="function")]) -> None:
        db.delete(session_record(request, db))
        response.delete_cookie(config.cookie_name, path="/", secure=config.secure_cookies,
                               httponly=True, samesite="lax")

    @app.get(prefix + "/workspaces")
    def workspaces(user: Annotated[User, Depends(actor)], db: Annotated[Session, Depends(database, scope="function")]) -> list[dict[str, str]]:
        records = db.execute(select(Workspace, Membership).join(Membership)
                             .where(Membership.user_id == user.id)
                             .order_by(Workspace.created_at).limit(config.list_limit))
        return [{"id": w.id, "name": w.name, "role": m.role} for w, m in records]

    @app.post(prefix + "/workspaces", status_code=201)
    def create_workspace(payload: WorkspaceInput, user: Annotated[User, Depends(actor)],
                         db: Annotated[Session, Depends(database, scope="function")]) -> dict[str, str]:
        count = db.scalar(select(func.count()).select_from(Membership).where(Membership.user_id == user.id))
        if count and count >= config.list_limit:
            reject(409, "collection_limit")
        workspace = Workspace(name=payload.name, owner_id=user.id)
        db.add(workspace)
        db.flush()
        db.add(Membership(workspace_id=workspace.id, user_id=user.id, role="owner"))
        audit(db, workspace.id, user, "workspace.created", workspace.id)
        return {"id": workspace.id, "name": workspace.name, "role": "owner"}

    @app.post(prefix + "/workspaces/{workspace_id}/invitations", status_code=201)
    def invite(workspace_id: str, payload: InvitationInput, user: Annotated[User, Depends(actor)],
               db: Annotated[Session, Depends(database, scope="function")]) -> dict[str, Any]:
        member(db, workspace_id, user, {"owner"})
        count = db.scalar(select(func.count()).select_from(Membership).where(Membership.workspace_id == workspace_id))
        if count and count >= config.list_limit:
            reject(409, "collection_limit")
        raw = token()
        expires = now() + config.invite_hours * 3600
        db.add(Invitation(token_hash=token_hash(raw), workspace_id=workspace_id,
                          role=payload.role, expires_at=expires))
        audit(db, workspace_id, user, "invitation.created", workspace_id)
        return {"token": raw, "expires_at": expires}

    @app.post(prefix + "/invitations/accept")
    def accept_invite(payload: AcceptInvitation, user: Annotated[User, Depends(actor)],
                      db: Annotated[Session, Depends(database, scope="function")]) -> dict[str, str]:
        invite = db.scalar(select(Invitation).where(Invitation.token_hash == token_hash(payload.token))
                           .with_for_update())
        if not invite or invite.used_at or invite.expires_at <= now():
            reject(404, "invitation_unavailable")
        assert invite is not None
        if db.get(Membership, (invite.workspace_id, user.id)):
            reject(409, "already_a_member")
        db.add(Membership(workspace_id=invite.workspace_id, user_id=user.id, role=invite.role))
        invite.used_at = now()
        audit(db, invite.workspace_id, user, "member.joined", user.id)
        return {"workspace_id": invite.workspace_id}

    @app.get(prefix + "/workspaces/{workspace_id}/state")
    def state(workspace_id: str, user: Annotated[User, Depends(actor)],
              db: Annotated[Session, Depends(database, scope="function")]) -> dict[str, Any]:
        membership = member(db, workspace_id, user)
        workspace = db.get(Workspace, workspace_id)
        assert workspace is not None
        people = {u.id: {"id": u.id, "name": u.name, "role": m.role}
                  for u, m in db.execute(select(User, Membership).join(Membership)
                                        .where(Membership.workspace_id == workspace_id)
                                        .limit(config.list_limit))}
        artifacts = list(db.scalars(select(Artifact).where(Artifact.workspace_id == workspace_id)
                                    .order_by(Artifact.created_at.desc()).limit(config.max_tasks)))
        approvals = list(db.scalars(select(Approval).where(Approval.workspace_id == workspace_id)
                                    .order_by(Approval.created_at.desc()).limit(config.max_tasks * 2)))
        task_rows = list(db.scalars(select(Task).where(Task.workspace_id == workspace_id)
                                   .order_by(Task.created_at.desc()).limit(config.max_tasks)))
        task_data = []
        for task in task_rows:
            artifact = next((a for a in artifacts if a.task_id == task.id and a.version == task.version), None)
            decisions = [a for a in approvals if artifact and a.artifact_id == artifact.id]
            task_data.append({"id": task.id, "title": task.title, "description": task.description,
                              "criteria": task.criteria, "project": task.project, "priority": task.priority,
                              "status": task.status, "version": task.version, "revision": task.revision,
                              "owner": people.get(task.owner_id, {}).get("name", ""),
                              "content_hash": artifact.content_hash if artifact else None,
                              "artifact_id": artifact.id if artifact else None,
                              "clientApproved": any(a.kind == "client" for a in decisions),
                              "developerApproved": any(a.kind == "developer" for a in decisions)})
        messages = list(db.scalars(select(Message).where(Message.workspace_id == workspace_id)
                                  .order_by(Message.created_at.desc()).limit(config.list_limit)))
        events = list(db.scalars(select(AuditEvent).where(AuditEvent.workspace_id == workspace_id)
                                .order_by(AuditEvent.created_at.desc()).limit(config.list_limit)))
        preferences = db.get(Preferences, user.id)
        return {"workspace": {"id": workspace.id, "name": workspace.name, "role": membership.role},
                "members": list(people.values()), "tasks": task_data,
                "messages": [{"id": m.id, "text": m.text, "name": people.get(m.user_id, {}).get("name", ""),
                              "created_at": m.created_at} for m in reversed(messages)],
                "artifacts": [{"id": a.id, "task_id": a.task_id, "version": a.version,
                               "content_hash": a.content_hash, "created_at": a.created_at} for a in artifacts],
                "activity": [{"id": e.id, "action": e.action, "resource_id": e.resource_id,
                              "actor": people.get(e.actor_id, {}).get("name", ""), "created_at": e.created_at} for e in events],
                "preferences": preferences.values if preferences else {}}

    @app.post(prefix + "/workspaces/{workspace_id}/tasks", status_code=201)
    def create_task(workspace_id: str, payload: TaskInput, user: Annotated[User, Depends(actor)],
                    db: Annotated[Session, Depends(database, scope="function")]) -> dict[str, str]:
        member(db, workspace_id, user, {"owner", "developer", "client"})
        if any(not criterion.strip() or len(criterion) > TEXT_MAX for criterion in payload.criteria):
            reject(422, "invalid_input")
        count = db.scalar(select(func.count()).select_from(Task).where(Task.workspace_id == workspace_id))
        if count and count >= config.max_tasks:
            reject(409, "collection_limit")
        task = Task(**payload.model_dump(), workspace_id=workspace_id, owner_id=user.id)
        db.add(task)
        db.flush()
        audit(db, workspace_id, user, "task.created", task.id)
        return {"id": task.id}

    @app.patch(prefix + "/workspaces/{workspace_id}/tasks/{task_id}")
    def change_task(workspace_id: str, task_id: str, payload: TaskChange,
                    user: Annotated[User, Depends(actor)], db: Annotated[Session, Depends(database, scope="function")]) -> dict[str, int]:
        member(db, workspace_id, user, {"owner", "developer"})
        task = task_record(db, workspace_id, task_id, payload.revision)
        artifact = db.scalar(select(Artifact).where(Artifact.task_id == task.id,
                                                    Artifact.version == task.version))
        if payload.status in {"review", "complete"} and not artifact:
            reject(409, "artifact_required")
        if payload.status == "complete":
            decisions = list(db.scalars(select(Approval.kind).where(Approval.artifact_id == artifact.id))) if artifact else []
            if set(decisions) != {"client", "developer"}:
                reject(409, "approvals_required")
        task.status = payload.status
        task.revision += 1
        audit(db, workspace_id, user, "task.status_changed", task.id)
        db.flush()
        return {"revision": task.revision}

    @app.post(prefix + "/workspaces/{workspace_id}/tasks/{task_id}/artifacts", status_code=201)
    def create_artifact(workspace_id: str, task_id: str, payload: ArtifactInput,
                        user: Annotated[User, Depends(actor)], db: Annotated[Session, Depends(database, scope="function")]) -> dict[str, Any]:
        member(db, workspace_id, user, {"owner", "developer"})
        task = task_record(db, workspace_id, task_id, payload.revision)
        if db.scalar(select(Artifact.id).where(Artifact.task_id == task.id, Artifact.version == task.version)):
            task.version += 1
        task.revision += 1
        task.status = "review"
        artifact = Artifact(workspace_id=workspace_id, task_id=task.id, version=task.version,
                            content=payload.content, content_hash=token_hash(payload.content), created_by=user.id)
        db.add(artifact)
        db.flush()
        audit(db, workspace_id, user, "artifact.created", artifact.id)
        return {"id": artifact.id, "version": artifact.version, "content_hash": artifact.content_hash}

    @app.get(prefix + "/workspaces/{workspace_id}/artifacts/{artifact_id}", response_class=PlainTextResponse)
    def download(workspace_id: str, artifact_id: str, user: Annotated[User, Depends(actor)],
                 db: Annotated[Session, Depends(database, scope="function")]) -> PlainTextResponse:
        member(db, workspace_id, user)
        artifact = db.scalar(select(Artifact).where(Artifact.id == artifact_id,
                                                    Artifact.workspace_id == workspace_id))
        if not artifact:
            reject(404, "not_found")
        assert artifact is not None
        return PlainTextResponse(artifact.content, headers={"Content-Disposition": "attachment; filename=artifact.txt"})

    @app.post(prefix + "/workspaces/{workspace_id}/tasks/{task_id}/approvals", status_code=201)
    def approve(workspace_id: str, task_id: str, payload: ApprovalInput,
                user: Annotated[User, Depends(actor)], db: Annotated[Session, Depends(database, scope="function")]) -> dict[str, str]:
        roles = {"owner", "client"} if payload.kind == "client" else {"owner", "developer"}
        member(db, workspace_id, user, roles)
        task = task_record(db, workspace_id, task_id, payload.revision)
        artifact = db.scalar(select(Artifact).where(Artifact.task_id == task.id, Artifact.version == payload.version,
                                                    Artifact.content_hash == payload.content_hash))
        if not artifact or task.version != payload.version or task.status != "review":
            reject(409, "stale_approval")
        assert artifact is not None
        if payload.kind == "developer":
            previous = db.scalar(select(Approval).where(Approval.artifact_id == artifact.id, Approval.kind == "client"))
            if not previous:
                reject(409, "content_approval_required")
            assert previous is not None
            if previous.actor_id == user.id:
                reject(409, "independent_approver_required")
        db.add(Approval(workspace_id=workspace_id, task_id=task.id, artifact_id=artifact.id,
                        kind=payload.kind, actor_id=user.id))
        task.revision += 1
        audit(db, workspace_id, user, "approval." + payload.kind, artifact.id)
        db.flush()
        return {"status": "recorded"}

    @app.post(prefix + "/workspaces/{workspace_id}/messages", status_code=201)
    def post_message(workspace_id: str, payload: MessageInput, user: Annotated[User, Depends(actor)],
                     db: Annotated[Session, Depends(database, scope="function")]) -> dict[str, str]:
        member(db, workspace_id, user, {"owner", "developer", "client"})
        count = db.scalar(select(func.count()).select_from(Message).where(Message.workspace_id == workspace_id))
        if count and count >= config.max_messages:
            reject(409, "collection_limit")
        message = Message(workspace_id=workspace_id, user_id=user.id, text=payload.text)
        db.add(message)
        db.flush()
        audit(db, workspace_id, user, "message.created", message.id)
        return {"id": message.id}

    @app.put(prefix + "/preferences")
    def preferences(payload: PreferencesInput, user: Annotated[User, Depends(actor)],
                    db: Annotated[Session, Depends(database, scope="function")]) -> dict[str, str]:
        row = db.get(Preferences, user.id)
        if row:
            row.values = payload.model_dump()
        else:
            db.add(Preferences(user_id=user.id, values=payload.model_dump()))
        return {"status": "saved"}

    @app.post(prefix + "/contact", status_code=201)
    def contact(payload: ContactInput, request: Request,
                db: Annotated[Session, Depends(database, scope="function")]) -> dict[str, str]:
        session_record(request, db)
        email = str(payload.email).lower()
        throttle("contact:" + email, config.contact_rate_limit)
        throttle("contact-session:" + token_hash(request.cookies.get(config.cookie_name, "")), config.contact_rate_limit)
        row = ContactRequest(name=payload.name, email=email, message=payload.text)
        db.add(row)
        db.flush()
        return {"id": row.id, "status": "received"}

    install_brain_routes(app, config, database, actor, member, task_record, audit)
    install_operations(app, config, database, actor, member, audit)
    if config.frontend_directory:
        from starlette.staticfiles import StaticFiles

        app.mount("/", StaticFiles(directory=config.frontend_directory, html=True), name="frontend")
    app.add_middleware(BodyLimit, maximum=config.max_body_bytes)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.allowed_hosts)
    return app
