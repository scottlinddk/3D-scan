"""Public API contract. The web client types are generated from these models."""

from datetime import datetime
from enum import StrEnum
from typing import Literal

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
