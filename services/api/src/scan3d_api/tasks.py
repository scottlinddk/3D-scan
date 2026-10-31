"""Task queue with fenced leases. Workers pull; they never need an inbound connection."""

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path, PurePosixPath

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import FileResponse

from scan3d_api import auth
from scan3d_api.schemas import (
    Artifact,
    Claim,
    ClaimedTask,
    ClaimResult,
    Complete,
    Fail,
    Heartbeat,
    HeartbeatResult,
    Task,
    TaskCreate,
)
from scan3d_api.uploads import _artifact, usage

router = APIRouter(prefix="/api")


def _task(row: sqlite3.Row) -> Task:
    return Task(
        id=row["id"],
        job_id=row["job_id"],
        capability=row["capability"],
        input_revision=row["input_revision"],
        state=row["state"],
        attempts=row["attempts"],
        error=row["error"],
        result=json.loads(row["result"]) if row["result"] else None,
    )


def _touch() -> str:
    return auth.now().isoformat()


def reap_expired(conn: sqlite3.Connection) -> None:
    """Return abandoned leases to the queue, or fail/cancel them when attempts are spent."""
    conn.execute(
        "UPDATE tasks SET lease_token=NULL, lease_expires=NULL, updated_at=?,"
        " state=CASE WHEN cancel_requested=1 THEN 'cancelled'"
        "            WHEN attempts >= max_attempts THEN 'failed' ELSE 'queued' END,"
        " error=CASE WHEN cancel_requested=0 AND attempts >= max_attempts"
        "            THEN 'lease expired, attempts exhausted' ELSE error END"
        " WHERE state='leased' AND lease_expires < ?",
        (_touch(), _touch()),
    )


def _leased(conn: sqlite3.Connection, task_id: str, token: str, p: auth.Principal) -> sqlite3.Row:
    """The fence: only the current, unexpired lease holder may touch a task."""
    row = conn.execute(
        "SELECT * FROM tasks WHERE id=? AND owner_id=?", (task_id, p.user_id)
    ).fetchone()
    if row is None:
        raise HTTPException(404, "task not found")
    live = (
        row["state"] == "leased"
        and row["lease_token"] is not None
        and hmac.compare_digest(row["lease_token"], token)
        and row["lease_expires"] > _touch()
    )
    if not live:
        raise HTTPException(409, "lease is not current")
    assert isinstance(row, sqlite3.Row)
    return row


@contextmanager
def lease_txn(
    conn: sqlite3.Connection, task_id: str, token: str, p: auth.Principal
) -> Iterator[sqlite3.Row]:
    """Check the lease and apply the caller's writes in one write transaction (no TOCTOU)."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield _leased(conn, task_id, token, p)
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise


@router.post("/jobs/{job_id}/tasks", status_code=201, operation_id="createTask")
def create_task(
    job_id: str,
    body: TaskCreate,
    p: auth.Principal = Depends(auth.require("jobs:write")),
    conn: sqlite3.Connection = Depends(auth.get_db),
) -> Task:
    if not conn.execute(
        "SELECT 1 FROM jobs WHERE id=? AND owner_id=?", (job_id, p.user_id)
    ).fetchone():
        raise HTTPException(404, "job not found")
    task_id, stamp = uuid.uuid4().hex, _touch()
    conn.execute("BEGIN IMMEDIATE")
    # A newer request for the same work supersedes older ones (their inputs are stale).
    conn.execute(
        "UPDATE tasks SET state='cancelled', updated_at=? WHERE job_id=? AND capability=?"
        " AND state='queued'",
        (stamp, job_id, body.capability),
    )
    conn.execute(
        "UPDATE tasks SET cancel_requested=1, updated_at=? WHERE job_id=? AND capability=?"
        " AND state='leased'",
        (stamp, job_id, body.capability),
    )
    conn.execute(
        "INSERT INTO tasks(id, job_id, owner_id, capability, input_revision, payload, created_at,"
        " updated_at) VALUES (?,?,?,?,?,?,?,?)",
        (
            task_id,
            job_id,
            p.user_id,
            body.capability,
            body.input_revision,
            json.dumps(body.payload),
            stamp,
            stamp,
        ),
    )
    conn.execute("COMMIT")
    return _task(conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone())


@router.get("/jobs/{job_id}/tasks", operation_id="listTasks")
def list_tasks(
    job_id: str,
    p: auth.Principal = Depends(auth.require("jobs:read")),
    conn: sqlite3.Connection = Depends(auth.get_db),
) -> list[Task]:
    rows = conn.execute(
        "SELECT * FROM tasks WHERE job_id=? AND owner_id=? ORDER BY created_at", (job_id, p.user_id)
    )
    return [_task(r) for r in rows]


@router.post("/tasks/{task_id}/cancel", operation_id="cancelTask")
def cancel_task(
    task_id: str,
    p: auth.Principal = Depends(auth.require("jobs:write")),
    conn: sqlite3.Connection = Depends(auth.get_db),
) -> Task:
    conn.execute("BEGIN IMMEDIATE")
    conn.execute(
        "UPDATE tasks SET state=CASE state WHEN 'queued' THEN 'cancelled' ELSE state END,"
        " cancel_requested=CASE state WHEN 'leased' THEN 1 ELSE cancel_requested END,"
        " updated_at=? WHERE id=? AND owner_id=? AND state IN ('queued','leased')",
        (_touch(), task_id, p.user_id),
    )
    conn.execute("COMMIT")
    row = conn.execute(
        "SELECT * FROM tasks WHERE id=? AND owner_id=?", (task_id, p.user_id)
    ).fetchone()
    if row is None:
        raise HTTPException(404, "task not found")
    return _task(row)


@router.post("/worker/claim", operation_id="claimTask")
def claim(
    body: Claim,
    p: auth.Principal = Depends(auth.require("worker:claim")),
    conn: sqlite3.Connection = Depends(auth.get_db),
) -> ClaimResult:
    conn.execute("BEGIN IMMEDIATE")
    try:
        reap_expired(conn)
        marks = ",".join("?" * len(body.capabilities))
        row = conn.execute(
            f"SELECT * FROM tasks WHERE state='queued' AND owner_id=? AND capability IN ({marks})"
            " ORDER BY created_at LIMIT 1",
            (p.user_id, *body.capabilities),
        ).fetchone()
        if row is None:
            conn.execute("COMMIT")
            return ClaimResult()
        token = secrets.token_urlsafe(24)
        expires = auth.now() + timedelta(seconds=body.lease_seconds)
        conn.execute(
            "UPDATE tasks SET state='leased', attempts=attempts+1, lease_token=?, lease_expires=?,"
            " updated_at=? WHERE id=?",
            (token, expires.isoformat(), _touch(), row["id"]),
        )
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    fresh = conn.execute("SELECT * FROM tasks WHERE id=?", (row["id"],)).fetchone()
    return ClaimResult(
        task=ClaimedTask(
            **_task(fresh).model_dump(),
            lease_token=token,
            lease_expires=expires,
            payload=json.loads(fresh["payload"]),
        )
    )


@router.post("/worker/tasks/{task_id}/heartbeat", operation_id="heartbeatTask")
def heartbeat(
    task_id: str,
    body: Heartbeat,
    p: auth.Principal = Depends(auth.require("worker:claim")),
    conn: sqlite3.Connection = Depends(auth.get_db),
) -> HeartbeatResult:
    with lease_txn(conn, task_id, body.lease_token, p) as row:
        expires = (auth.now() + timedelta(seconds=body.extend_seconds)).isoformat()
        conn.execute("UPDATE tasks SET lease_expires=? WHERE id=?", (expires, task_id))
    return HeartbeatResult(cancel_requested=bool(row["cancel_requested"]))


def _finish(conn: sqlite3.Connection, task_id: str, state: str, **cols: str | None) -> Task:
    sets = "".join(f", {k}=?" for k in cols)
    conn.execute(
        f"UPDATE tasks SET state=?, lease_token=NULL, lease_expires=NULL, updated_at=?{sets}"
        " WHERE id=?",
        (state, _touch(), *cols.values(), task_id),
    )
    return _task(conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone())


@router.post("/worker/tasks/{task_id}/complete", operation_id="completeTask")
def complete(
    task_id: str,
    body: Complete,
    p: auth.Principal = Depends(auth.require("worker:claim")),
    conn: sqlite3.Connection = Depends(auth.get_db),
) -> Task:
    with lease_txn(conn, task_id, body.lease_token, p) as row:
        if body.input_revision != row["input_revision"]:
            raise HTTPException(409, "input revision mismatch")
        if row["cancel_requested"]:
            return _finish(conn, task_id, "cancelled")
        return _finish(conn, task_id, "succeeded", result=json.dumps(body.result))


@router.post("/worker/tasks/{task_id}/fail", operation_id="failTask")
def fail(
    task_id: str,
    body: Fail,
    p: auth.Principal = Depends(auth.require("worker:claim")),
    conn: sqlite3.Connection = Depends(auth.get_db),
) -> Task:
    with lease_txn(conn, task_id, body.lease_token, p) as row:
        if row["cancel_requested"]:
            return _finish(conn, task_id, "cancelled")
        retry = body.retryable and row["attempts"] < row["max_attempts"]
        return _finish(conn, task_id, "queued" if retry else "failed", error=body.error)


@router.get("/worker/tasks/{task_id}/inputs/{artifact_id}", operation_id="getTaskInput")
def task_input(
    task_id: str,
    artifact_id: str,
    request: Request,
    x_lease_token: str = Header(),
    p: auth.Principal = Depends(auth.require("worker:claim")),
    conn: sqlite3.Connection = Depends(auth.get_db),
) -> FileResponse:
    task = _leased(conn, task_id, x_lease_token, p)
    row = conn.execute(
        "SELECT * FROM artifacts WHERE id=? AND job_id=?", (artifact_id, task["job_id"])
    ).fetchone()
    if row is None:
        raise HTTPException(404, "artifact not found")
    return FileResponse(
        request.app.state.data_dir / row["path"], media_type="application/octet-stream"
    )


@router.put("/worker/tasks/{task_id}/artifacts", status_code=201, operation_id="putTaskArtifact")
async def put_artifact(
    task_id: str,
    filename: str,
    request: Request,
    kind: str = "intermediate",
    parent_id: str | None = None,
    x_lease_token: str = Header(),
    p: auth.Principal = Depends(auth.require("worker:claim")),
    conn: sqlite3.Connection = Depends(auth.get_db),
) -> Artifact:
    task = _leased(conn, task_id, x_lease_token, p)
    limits = request.app.state.limits
    if (
        parent_id
        and not conn.execute(
            "SELECT 1 FROM artifacts WHERE id=? AND job_id=?", (parent_id, task["job_id"])
        ).fetchone()
    ):
        raise HTTPException(404, "parent artifact not found")
    data_dir: Path = request.app.state.data_dir
    artifact_id = uuid.uuid4().hex
    rel = Path("artifacts") / task["job_id"] / artifact_id
    tmp = data_dir / "uploads" / f"{artifact_id}.part"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    digest, size = hashlib.sha256(), 0
    try:
        with tmp.open("wb") as f:
            async for chunk in request.stream():
                size += len(chunk)
                if size > limits.max_file_bytes:
                    raise HTTPException(413, "artifact too large")
                digest.update(chunk)
                f.write(chunk)
            f.flush()
            os.fsync(f.fileno())
        if size == 0:
            raise HTTPException(422, "empty artifact")
        name = PurePosixPath(filename.replace("\\", "/")).name or "file"
        # Check the quota and record the artifact in one write transaction.
        conn.execute("BEGIN IMMEDIATE")
        try:
            _leased(conn, task_id, x_lease_token, p)  # re-fence: the lease may have moved on
            if usage(conn, p.user_id) + size > limits.user_quota_bytes:
                raise HTTPException(413, "storage quota exceeded")
            final = data_dir / rel
            final.parent.mkdir(parents=True, exist_ok=True)
            tmp.replace(final)
            conn.execute(
                "INSERT INTO artifacts(id, job_id, owner_id, kind, filename, size, sha256, path,"
                " parent_id, task_id, protected, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,0,?)",
                (
                    artifact_id,
                    task["job_id"],
                    p.user_id,
                    kind,
                    name,
                    size,
                    digest.hexdigest(),
                    str(rel),
                    parent_id,
                    task_id,
                    _touch(),
                ),
            )
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
    finally:
        tmp.unlink(missing_ok=True)
    return _artifact(conn.execute("SELECT * FROM artifacts WHERE id=?", (artifact_id,)).fetchone())
