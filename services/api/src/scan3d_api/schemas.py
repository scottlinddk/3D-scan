"""Public API contract. The web client types are generated from these models."""

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    created = "created"
    uploading = "uploading"
    queued = "queued"
    running = "running"
    needs_review = "needs_review"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class JobCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    source_kind: Literal["mesh", "photos"] = "mesh"


class Job(BaseModel):
    id: str
    name: str
    source_kind: Literal["mesh", "photos"]
    status: JobStatus
    created_at: datetime


class Health(BaseModel):
    status: Literal["ok"]
    version: str


class Register(BaseModel):
    invite: str
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=10, max_length=200)


class Login(BaseModel):
    email: str
    password: str


class Me(BaseModel):
    user_id: int
    is_admin: bool
    csrf: str | None = None


class InviteCreate(BaseModel):
    is_admin: bool = False


class InviteOut(BaseModel):
    code: str


class TokenCreate(BaseModel):
    kind: Literal["device", "worker"]
    label: str = Field(min_length=1, max_length=100)


class TokenOut(BaseModel):
    id: str
    token: str


class UploadCreate(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    size: int = Field(gt=0)
    kind: Literal["original", "photo", "capture_bundle"] = "original"
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")


class Upload(BaseModel):
    id: str
    job_id: str
    filename: str
    size: int
    offset: int
    status: Literal["open", "complete"]


class Artifact(BaseModel):
    id: str
    job_id: str
    kind: str
    filename: str
    size: int
    sha256: str
    protected: bool


type TaskState = Literal["queued", "leased", "succeeded", "failed", "cancelled"]


class TaskCreate(BaseModel):
    capability: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9_.-]+$")
    input_revision: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any] = Field(default_factory=dict)


class Task(BaseModel):
    id: str
    job_id: str
    capability: str
    input_revision: str
    state: TaskState
    attempts: int
    error: str | None = None
    result: dict[str, Any] | None = None


class Claim(BaseModel):
    capabilities: list[str] = Field(min_length=1, max_length=20)
    lease_seconds: int = Field(default=60, ge=5, le=900)


class ClaimedTask(Task):
    lease_token: str
    lease_expires: datetime
    payload: dict[str, Any]


class ClaimResult(BaseModel):
    task: ClaimedTask | None = None


class Heartbeat(BaseModel):
    lease_token: str
    extend_seconds: int = Field(default=60, ge=5, le=900)


class HeartbeatResult(BaseModel):
    cancel_requested: bool


class Complete(BaseModel):
    lease_token: str
    input_revision: str
    result: dict[str, Any] = Field(default_factory=dict)


class Fail(BaseModel):
    lease_token: str
    error: str = Field(max_length=2000)
    retryable: bool = False
