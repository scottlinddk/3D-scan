import hashlib
from datetime import timedelta
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from scan3d_api import auth, db, retention
from scan3d_api.limits import Limits
from scan3d_api.testing import Harness

DATA = bytes(range(256)) * 40  # 10240 bytes


def start(c: TestClient, **kw: object) -> dict[str, Any]:
    job = c.post("/api/jobs", json={"name": "scan"}).json()
    body = {"filename": "../../etc/scan.ply", "size": len(DATA), **kw}
    r = c.post(f"/api/jobs/{job['id']}/uploads", json=body)
    assert r.status_code == 201, r.text
    result: dict[str, Any] = r.json()
    return result


def test_resume_complete_and_download(tmp_path: Path) -> None:
    h = Harness(tmp_path / "t.sqlite", Limits(max_chunk_bytes=4096))
    c = h.new_user("a@x.io")
    up = start(c, sha256=hashlib.sha256(DATA).hexdigest())
    url = f"/api/uploads/{up['id']}"

    assert c.patch(url, params={"offset": 0}, content=DATA[:4096]).json()["offset"] == 4096
    # Client lost the response and retries a stale offset: server says where it really is.
    stale = c.patch(url, params={"offset": 0}, content=DATA[:4096])
    assert stale.status_code == 409
    assert "4096" in stale.json()["detail"]
    assert c.patch(url, params={"offset": 4096}, content=DATA[:5000]).status_code == 413
    assert c.get(url).json()["offset"] == 4096
    assert c.post(f"{url}/complete").status_code == 409  # incomplete

    assert c.patch(url, params={"offset": 4096}, content=DATA[4096:8192]).status_code == 200
    assert c.patch(url, params={"offset": 8192}, content=DATA[8192:]).json()["offset"] == len(DATA)
    art = c.post(f"{url}/complete").json()
    assert art["filename"] == "scan.ply"
    assert art["protected"] is True
    assert art["sha256"] == hashlib.sha256(DATA).hexdigest()
    assert c.get(f"/api/artifacts/{art['id']}/content").content == DATA
    assert [a["id"] for a in c.get(f"/api/jobs/{art['job_id']}/artifacts").json()] == [art["id"]]
    assert c.post(f"{url}/complete").status_code == 409


def test_hash_mismatch_discards_and_limits_apply(tmp_path: Path) -> None:
    limits = Limits(max_file_bytes=20000, user_quota_bytes=25000, max_chunk_bytes=16384)
    h = Harness(tmp_path / "t.sqlite", limits)
    c = h.new_user("a@x.io")
    up = start(c, sha256="0" * 64)
    url = f"/api/uploads/{up['id']}"
    assert c.patch(url, params={"offset": 0}, content=DATA).status_code == 200
    assert c.post(f"{url}/complete").status_code == 422
    assert c.get(url).status_code == 404

    job = c.post("/api/jobs", json={"name": "big"}).json()
    too_big = {"filename": "a", "size": 20001}
    assert c.post(f"/api/jobs/{job['id']}/uploads", json=too_big).status_code == 413
    ok = {"filename": "a", "size": 15000}
    assert c.post(f"/api/jobs/{job['id']}/uploads", json=ok).status_code == 201
    assert c.post(f"/api/jobs/{job['id']}/uploads", json=ok).status_code == 413  # quota
    assert (
        c.patch(f"/api/uploads/{up['id']}", params={"offset": 0}, content=b"x").status_code == 404
    )


def test_uploads_are_owner_only(h: Harness) -> None:
    alice, bob = h.new_user("a@x.io"), h.new_user("b@x.io")
    up = start(alice)
    assert bob.get(f"/api/uploads/{up['id']}").status_code == 404
    assert (
        bob.post(f"/api/jobs/{up['job_id']}/uploads", json={"filename": "x", "size": 1}).status_code
        == 404
    )


def test_retention_keeps_protected_and_required_parents(h: Harness) -> None:
    c = h.new_user("a@x.io")
    up = start(c)
    c.patch(f"/api/uploads/{up['id']}", params={"offset": 0}, content=DATA)
    original = c.post(f"/api/uploads/{up['id']}/complete").json()

    conn = db.connect(h.path)
    old = (auth.now() - timedelta(days=60)).isoformat()
    base = (original["job_id"], 1, "x", 1, "0" * 64)
    ins = (
        "INSERT INTO artifacts(id, job_id, owner_id, kind, filename, size, sha256, path,"
        " parent_id, protected, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)"
    )
    for aid, parent, prot in [("free", None, 0), ("parent", None, 0), ("tested", "parent", 1)]:
        conn.execute(
            ins,
            (
                aid,
                base[0],
                base[1],
                "intermediate",
                "f",
                1,
                base[4],
                f"nope/{aid}",
                parent,
                prot,
                old,
            ),
        )
    removed = retention.purge(conn, h.path.parent / "files")
    assert removed["intermediates"] == ["free"]
    left = {r["id"] for r in conn.execute("SELECT id FROM artifacts")}
    assert left == {original["id"], "parent", "tested"}
    conn.close()
