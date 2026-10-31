"""FastAPI application. Requests never perform mesh processing."""

import uuid
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException

from scan3d_api import __version__
from scan3d_api.schemas import Health, Job, JobCreate, JobStatus

# ponytail: in-memory store, replaced by SQLite (WAL) with #32/#33.
_jobs: dict[str, Job] = {}


def create_app() -> FastAPI:
    app = FastAPI(title="3d-scan API", version=__version__)

    @app.get("/api/health", operation_id="getHealth")
    def health() -> Health:
        return Health(status="ok", version=__version__)

    @app.post("/api/jobs", status_code=201, operation_id="createJob")
    def create_job(body: JobCreate) -> Job:
        job = Job(
            id=uuid.uuid4().hex,
            name=body.name,
            source_kind=body.source_kind,
            status=JobStatus.created,
            created_at=datetime.now(UTC),
        )
        _jobs[job.id] = job
        return job

    @app.get("/api/jobs", operation_id="listJobs")
    def list_jobs() -> list[Job]:
        return list(_jobs.values())

    @app.get("/api/jobs/{job_id}", operation_id="getJob")
    def get_job(job_id: str) -> Job:
        if job_id not in _jobs:
            raise HTTPException(status_code=404, detail="job not found")
        return _jobs[job_id]

    return app


app = create_app()
