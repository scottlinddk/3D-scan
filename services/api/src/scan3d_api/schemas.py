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
