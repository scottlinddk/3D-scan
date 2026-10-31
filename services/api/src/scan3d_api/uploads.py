"""Bounded resumable uploads. The client PATCHes chunks at the offset the server reports."""

import hashlib
import os
import sqlite3
import uuid
from pathlib import Path, PurePosixPath

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from scan3d_api import auth
from scan3d_api.schemas import Artifact, Upload, UploadCreate

router = APIRouter(prefix="/api")


def _upload(row: sqlite3.Row) -> Upload:
    return Upload(
        id=row["id"],
        job_id=row["job_id"],
        filename=row["filename"],
        size=row["size"],
        offset=row["received"],
        status=row["status"],
    )


def _artifact(row: sqlite3.Row) -> Artifact:
    return Artifact(
        id=row["id"],
        job_id=row["job_id"],
        kind=row["kind"],
        filename=row["filename"],
        size=row["size"],
        sha256=row["sha256"],
        protected=bool(row["protected"]),
    )


def _own_upload(conn: sqlite3.Connection, upload_id: str, p: auth.Principal) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM uploads WHERE id=? AND owner_id=?", (upload_id, p.user_id)
    ).fetchone()
    if row is None:
        raise HTTPException(404, "upload not found")
    assert isinstance(row, sqlite3.Row)
    return row


def usage(conn: sqlite3.Connection, user_id: int) -> int:
    """Stored artifact bytes plus the declared size of open uploads."""
    a = conn.execute("SELECT COALESCE(SUM(size),0) FROM artifacts WHERE owner_id=?", (user_id,))
    u = conn.execute(
        "SELECT COALESCE(SUM(size),0) FROM uploads WHERE owner_id=? AND status='open'", (user_id,)
    )
    return int(a.fetchone()[0]) + int(u.fetchone()[0])


def partial_path(data_dir: Path, upload_id: str) -> Path:
    return data_dir / "uploads" / f"{upload_id}.part"


@router.post("/jobs/{job_id}/uploads", status_code=201, operation_id="createUpload")
def create_upload(
    job_id: str,
    body: UploadCreate,
    request: Request,
    p: auth.Principal = Depends(auth.require("uploads:write")),
    conn: sqlite3.Connection = Depends(auth.get_db),
) -> Upload:
    limits = request.app.state.limits
    if not conn.execute(
        "SELECT 1 FROM jobs WHERE id=? AND owner_id=?", (job_id, p.user_id)
    ).fetchone():
        raise HTTPException(404, "job not found")
    if body.size > limits.max_file_bytes:
        raise HTTPException(413, f"file exceeds {limits.max_file_bytes} bytes")
    upload_id, stamp = uuid.uuid4().hex, auth.now().isoformat()
    # Only the basename is kept, and only as metadata. Disk paths come from ids.
    name = PurePosixPath(body.filename.replace("\\", "/")).name or "file"
    # Check and reserve in one write transaction so concurrent requests cannot both fit.
    conn.execute("BEGIN IMMEDIATE")
    try:
        if usage(conn, p.user_id) + body.size > limits.user_quota_bytes:
            raise HTTPException(413, "storage quota exceeded")
        conn.execute(
            "INSERT INTO uploads(id, job_id, owner_id, kind, filename, size, sha256, created_at,"
            " updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (upload_id, job_id, p.user_id, body.kind, name, body.size, body.sha256, stamp, stamp),
        )
        conn.execute(
            "UPDATE jobs SET status='uploading' WHERE id=? AND status='created'", (job_id,)
        )
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    part = partial_path(request.app.state.data_dir, upload_id)
    part.parent.mkdir(parents=True, exist_ok=True)
    part.touch()
    return _upload(_own_upload(conn, upload_id, p))


@router.get("/uploads/{upload_id}", operation_id="getUpload")
def get_upload(
    upload_id: str,
    p: auth.Principal = Depends(auth.require("uploads:write")),
    conn: sqlite3.Connection = Depends(auth.get_db),
) -> Upload:
    return _upload(_own_upload(conn, upload_id, p))


@router.patch("/uploads/{upload_id}", operation_id="appendUploadChunk")
async def append_chunk(
    upload_id: str,
    offset: int,
    request: Request,
    p: auth.Principal = Depends(auth.require("uploads:write")),
    conn: sqlite3.Connection = Depends(auth.get_db),
) -> Upload:
    limits = request.app.state.limits
    row = _own_upload(conn, upload_id, p)
    if row["status"] != "open":
        raise HTTPException(409, "upload already complete")
    if offset != row["received"]:
        raise HTTPException(409, f"offset mismatch, server has {row['received']}")
    # Count while streaming so a missing or false Content-Length cannot buffer an oversized body.
    limit = min(limits.max_chunk_bytes, row["size"] - offset)
    parts: list[bytes] = []
    total = 0
    async for piece in request.stream():
        total += len(piece)
        if total > limit:
            raise HTTPException(413, f"chunk exceeds {limit} bytes")
        parts.append(piece)
    if total == 0:
        raise HTTPException(422, "empty chunk")
    chunk = b"".join(parts)
    part = partial_path(request.app.state.data_dir, upload_id)
    # The DB offset is the truth. A crash may have left extra bytes on disk, so cut back to it.
    with part.open("r+b") as f:
        f.truncate(offset)
        f.seek(offset)
        f.write(chunk)
        f.flush()
        os.fsync(f.fileno())
    conn.execute(
        "UPDATE uploads SET received=?, updated_at=? WHERE id=?",
        (offset + len(chunk), auth.now().isoformat(), upload_id),
    )
    return _upload(_own_upload(conn, upload_id, p))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while block := f.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()


@router.post("/uploads/{upload_id}/complete", operation_id="completeUpload")
def complete_upload(
    upload_id: str,
    request: Request,
    p: auth.Principal = Depends(auth.require("uploads:write")),
    conn: sqlite3.Connection = Depends(auth.get_db),
) -> Artifact:
    row = _own_upload(conn, upload_id, p)
    if row["status"] != "open":
        raise HTTPException(409, "upload already complete")
    if row["received"] != row["size"]:
        raise HTTPException(409, f"incomplete, server has {row['received']} of {row['size']}")
    data_dir: Path = request.app.state.data_dir
    part = partial_path(data_dir, upload_id)
    digest = _sha256(part)
    if row["sha256"] and row["sha256"] != digest:
        part.unlink(missing_ok=True)
        conn.execute("DELETE FROM uploads WHERE id=?", (upload_id,))
        raise HTTPException(422, "sha256 mismatch, upload discarded")
    artifact_id = uuid.uuid4().hex
    rel = Path("artifacts") / row["job_id"] / artifact_id
    final = data_dir / rel
    final.parent.mkdir(parents=True, exist_ok=True)
    part.replace(final)  # atomic publish within one filesystem
    conn.execute("BEGIN IMMEDIATE")
    conn.execute(
        "INSERT INTO artifacts(id, job_id, owner_id, kind, filename, size, sha256, path,"
        " created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (
            artifact_id,
            row["job_id"],
            p.user_id,
            row["kind"],
            row["filename"],
            row["size"],
            digest,
            str(rel),
            auth.now().isoformat(),
        ),
    )
    conn.execute("UPDATE uploads SET status='complete' WHERE id=?", (upload_id,))
    conn.execute("COMMIT")
    return _artifact(conn.execute("SELECT * FROM artifacts WHERE id=?", (artifact_id,)).fetchone())


@router.get("/jobs/{job_id}/artifacts", operation_id="listArtifacts")
def list_artifacts(
    job_id: str,
    p: auth.Principal = Depends(auth.require("jobs:read")),
    conn: sqlite3.Connection = Depends(auth.get_db),
) -> list[Artifact]:
    rows = conn.execute(
        "SELECT * FROM artifacts WHERE job_id=? AND owner_id=? ORDER BY created_at",
        (job_id, p.user_id),
    )
    return [_artifact(r) for r in rows]


@router.get("/artifacts/{artifact_id}/content", operation_id="getArtifactContent")
def artifact_content(
    artifact_id: str,
    request: Request,
    p: auth.Principal = Depends(auth.require("jobs:read")),
    conn: sqlite3.Connection = Depends(auth.get_db),
) -> FileResponse:
    row = conn.execute(
        "SELECT * FROM artifacts WHERE id=? AND owner_id=?", (artifact_id, p.user_id)
    ).fetchone()
    if row is None:
        raise HTTPException(404, "artifact not found")
    return FileResponse(
        request.app.state.data_dir / row["path"],
        filename=row["filename"],
        media_type="application/octet-stream",
    )
