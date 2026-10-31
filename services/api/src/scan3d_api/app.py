"""FastAPI application. Requests never perform mesh processing."""

import os
import sqlite3
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException

from scan3d_api import __version__, auth, db
from scan3d_api.auth_routes import router as auth_router
from scan3d_api.schemas import Health, Job, JobCreate, JobStatus


def _job(row: sqlite3.Row) -> Job:
    return Job(
        id=row["id"],
        name=row["name"],
        source_kind=row["source_kind"],
        status=JobStatus(row["status"]),
        created_at=row["created_at"],
    )


def create_app(db_path: Path | None = None, *, secure_cookies: bool = True) -> FastAPI:
    app = FastAPI(title="3d-scan API", version=__version__)
    app.state.db_path = db_path or Path(os.environ.get("SCAN3D_DB", "data/scan3d.sqlite"))
    app.state.secure_cookies = secure_cookies
    db.init(app.state.db_path)
    app.include_router(auth_router)

    @app.get("/api/health", operation_id="getHealth")
    def health() -> Health:
        return Health(status="ok", version=__version__)

    @app.post("/api/jobs", status_code=201, operation_id="createJob")
    def create_job(
        body: JobCreate,
        p: auth.Principal = Depends(auth.require("jobs:write")),
        conn: sqlite3.Connection = Depends(auth.get_db),
    ) -> Job:
        job_id = uuid.uuid4().hex
        created = auth.now().isoformat()
        conn.execute(
            "INSERT INTO jobs(id, owner_id, name, source_kind, status, created_at)"
            " VALUES (?,?,?,?,?,?)",
            (job_id, p.user_id, body.name, body.source_kind, JobStatus.created, created),
        )
        return _job(conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone())

    @app.get("/api/jobs", operation_id="listJobs")
    def list_jobs(
        p: auth.Principal = Depends(auth.require("jobs:read")),
        conn: sqlite3.Connection = Depends(auth.get_db),
    ) -> list[Job]:
        rows = conn.execute("SELECT * FROM jobs WHERE owner_id=? ORDER BY created_at", (p.user_id,))
        return [_job(r) for r in rows]

    @app.get("/api/jobs/{job_id}", operation_id="getJob")
    def get_job(
        job_id: str,
        p: auth.Principal = Depends(auth.require("jobs:read")),
        conn: sqlite3.Connection = Depends(auth.get_db),
    ) -> Job:
        row = conn.execute(
            "SELECT * FROM jobs WHERE id=? AND owner_id=?", (job_id, p.user_id)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="job not found")
        return _job(row)

    return app
