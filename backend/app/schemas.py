"""Versioned public input contracts; bounds are defined here once."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Stable v1 wire-contract bounds; changing these is an API contract revision.
NAME_MAX = 80
TITLE_MAX = 100
TEXT_MAX = 4000
ARTIFACT_MAX = 20000
PASSWORD_MIN = 12
PASSWORD_MAX = 128
CRITERIA_MAX = 20
INVITE_MAX = 128


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Credentials(Input):
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN, max_length=PASSWORD_MAX)


class Registration(Credentials):
    name: str = Field(min_length=1, max_length=NAME_MAX)


class WorkspaceInput(Input):
    name: str = Field(min_length=1, max_length=NAME_MAX)


class InvitationInput(Input):
    role: Literal["client", "developer", "viewer"]


class AcceptInvitation(Input):
    token: str = Field(min_length=20, max_length=INVITE_MAX)


class TaskInput(Input):
    title: str = Field(min_length=1, max_length=TITLE_MAX)
    description: str = Field(default="", max_length=TEXT_MAX)
    project: str = Field(min_length=1, max_length=NAME_MAX)
    priority: Literal["Normal", "High", "Low"] = "Normal"
    criteria: list[str] = Field(default_factory=list, max_length=CRITERIA_MAX)


class TaskChange(Input):
    revision: int = Field(ge=1)
    status: Literal["planned", "progress", "review", "complete"]


class ArtifactInput(Input):
    revision: int = Field(ge=1)
    content: str = Field(min_length=1, max_length=ARTIFACT_MAX)


class ApprovalInput(Input):
    revision: int = Field(ge=1)
    version: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    kind: Literal["client", "developer"]


class RunInput(Input):
    revision: int = Field(ge=1)
    request_key: str = Field(min_length=16, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    mode: Literal["draft", "code"]
    fixture: str | None = Field(default=None, max_length=NAME_MAX)
    repository: str | None = Field(default=None, min_length=1, max_length=NAME_MAX)
    profile: str | None = Field(default=None, min_length=1, max_length=NAME_MAX)
    source_ids: list[str] = Field(default_factory=list, max_length=CRITERIA_MAX)


class DeliveryInput(Input):
    revision: int = Field(ge=1)
    request_key: str = Field(min_length=16, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    version: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


class MessageInput(Input):
    text: str = Field(min_length=1, max_length=TEXT_MAX)


class SourceInput(MessageInput):
    name: str = Field(min_length=1, max_length=NAME_MAX)


class ExecutionInput(Input):
    stopped: bool = Field(strict=True)


class ContactInput(MessageInput):
    name: str = Field(min_length=1, max_length=NAME_MAX)
    email: EmailStr


class PreferencesInput(Input):
    theme: Literal["midnight", "daylight"]
    calm: bool
    notifications: bool
    timezone: Literal["Asia/Dhaka", "UTC", "Europe/London", "America/New_York"]
