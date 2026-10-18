"""Relational records; private workspace scope is explicit on every resource."""
import time
import uuid
from typing import Any

from sqlalchemy import JSON, BigInteger, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def identity() -> str:
    return str(uuid.uuid4())


def now() -> int:
    return int(time.time())


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identity)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80))
    password_hash: Mapped[str] = mapped_column(Text)
    created_at: Mapped[int] = mapped_column(BigInteger, default=now)


class LoginSession(Base):
    __tablename__ = "login_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    expires_at: Mapped[int] = mapped_column(BigInteger, index=True)


class Workspace(Base):
    __tablename__ = "workspaces"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identity)
    name: Mapped[str] = mapped_column(String(80))
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[int] = mapped_column(BigInteger, default=now)


class Membership(Base):
    __tablename__ = "memberships"
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String(20))


class Invitation(Base):
    __tablename__ = "invitations"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"))
    role: Mapped[str] = mapped_column(String(20))
    expires_at: Mapped[int] = mapped_column(BigInteger)
    used_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identity)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="")
    criteria: Mapped[list[str]] = mapped_column(JSON, default=list)
    project: Mapped[str] = mapped_column(String(80))
    priority: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="planned")
    version: Mapped[int] = mapped_column(Integer, default=1)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[int] = mapped_column(BigInteger, default=now)
    __mapper_args__ = {"version_id_col": revision}


class Artifact(Base):
    __tablename__ = "artifacts"
    __table_args__ = (UniqueConstraint("task_id", "version"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identity)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[int] = mapped_column(BigInteger, default=now)


class Approval(Base):
    __tablename__ = "approvals"
    __table_args__ = (UniqueConstraint("artifact_id", "kind"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identity)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), index=True)
    artifact_id: Mapped[str] = mapped_column(ForeignKey("artifacts.id"))
    kind: Mapped[str] = mapped_column(String(20))
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[int] = mapped_column(BigInteger, default=now)


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identity)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[int] = mapped_column(BigInteger, default=now)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identity)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(80))
    resource_id: Mapped[str] = mapped_column(String(36))
    created_at: Mapped[int] = mapped_column(BigInteger, default=now)


class Preferences(Base):
    __tablename__ = "preferences"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    values: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class ContactRequest(Base):
    __tablename__ = "contact_requests"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identity)
    name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(254))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[int] = mapped_column(BigInteger, default=now, index=True)


class RateBucket(Base):
    __tablename__ = "rate_buckets"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    count: Mapped[int] = mapped_column(Integer)
    expires_at: Mapped[int] = mapped_column(BigInteger, index=True)


class AgentRun(Base):
    __tablename__ = "agent_runs"
    __table_args__ = (UniqueConstraint("workspace_id", "request_key"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identity)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), index=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    request_key: Mapped[str] = mapped_column(String(80))
    request_hash: Mapped[str] = mapped_column(String(64))
    mode: Mapped[str] = mapped_column(String(20))
    fixture: Mapped[str | None] = mapped_column(String(80), nullable=True)
    inputs: Mapped[dict[str, Any]] = mapped_column(JSON)
    task_revision: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    attempt: Mapped[int] = mapped_column(Integer, default=0)
    fence: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lease_until: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    artifact_id: Mapped[str | None] = mapped_column(ForeignKey("artifacts.id"), nullable=True)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[int] = mapped_column(BigInteger, default=now)
    finished_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class RunEvent(Base):
    __tablename__ = "run_events"
    __table_args__ = (UniqueConstraint("run_id", "sequence"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identity)
    run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[int] = mapped_column(BigInteger, default=now)


class Delivery(Base):
    __tablename__ = "deliveries"
    __table_args__ = (UniqueConstraint("workspace_id", "request_key"), UniqueConstraint("artifact_id"))
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identity)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"))
    artifact_id: Mapped[str] = mapped_column(ForeignKey("artifacts.id"))
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    request_key: Mapped[str] = mapped_column(String(80))
    content_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[int] = mapped_column(BigInteger, default=now)


class WorkspaceExecution(Base):
    __tablename__ = "workspace_execution"
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), primary_key=True)
    stopped: Mapped[bool] = mapped_column(default=False)


class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identity)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    text: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[int] = mapped_column(BigInteger, default=now)
    revoked_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class RepositoryGrant(Base):
    __tablename__ = "repository_grants"
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), primary_key=True)
    target: Mapped[str] = mapped_column(String(80), primary_key=True)
    profile: Mapped[str] = mapped_column(String(80), primary_key=True)
    scope_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[int] = mapped_column(BigInteger, default=now)


class ReleaseIntent(Base):
    __tablename__ = "release_intents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identity)
    delivery_id: Mapped[str] = mapped_column(ForeignKey("deliveries.id"), unique=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id"))
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    lease_until: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    receipt: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
