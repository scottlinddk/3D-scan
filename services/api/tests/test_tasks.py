from datetime import timedelta
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from scan3d_api import auth, db, recovery
from scan3d_api.testing import Harness


def setup(h: Harness) -> tuple[TestClient, TestClient, dict[str, str], str]:
    user = h.new_user("a@x.io")
    tok = user.post("/api/tokens", json={"kind": "worker", "label": "mac"}).json()["token"]
    worker = TestClient(h.client.app)
    worker.headers["authorization"] = f"Bearer {tok}"
    job = user.post("/api/jobs", json={"name": "j"}).json()["id"]
    return user, worker, {}, job


def enqueue(
    user: TestClient, job: str, rev: str = "r1", cap: str = "reconstruct"
) -> dict[str, Any]:
    r = user.post(f"/api/jobs/{job}/tasks", json={"capability": cap, "input_revision": rev})
    assert r.status_code == 201, r.text
    result: dict[str, Any] = r.json()
    return result


def claim(
    worker: TestClient, caps: list[str] | None = None, secs: int = 60
) -> dict[str, Any] | None:
    r = worker.post(
        "/api/worker/claim", json={"capabilities": caps or ["reconstruct"], "lease_seconds": secs}
    )
    assert r.status_code == 200, r.text
    task: dict[str, Any] | None = r.json()["task"]
    return task


def expire(h: Harness, task_id: str) -> None:
    conn = db.connect(h.path)
    past = (auth.now() - timedelta(seconds=5)).isoformat()
    conn.execute("UPDATE tasks SET lease_expires=? WHERE id=?", (past, task_id))
    conn.close()


def test_claim_complete_and_capability_match(h: Harness) -> None:
    user, worker, _, job = setup(h)
    t = enqueue(user, job)
    assert claim(worker, ["bambu"]) is None
    got = claim(worker)
    assert got is not None
    assert got["id"] == t["id"]
    assert got["attempts"] == 1
    assert claim(worker) is None  # leased, nothing else queued
    done = worker.post(
        f"/api/worker/tasks/{t['id']}/complete",
        json={"lease_token": got["lease_token"], "input_revision": "r1", "result": {"ok": True}},
    )
    assert done.json()["state"] == "succeeded"
    assert done.json()["result"] == {"ok": True}
    again = worker.post(
        f"/api/worker/tasks/{t['id']}/complete",
        json={"lease_token": got["lease_token"], "input_revision": "r1"},
    )
    assert again.status_code == 409  # duplicate completion cannot advance the job


def test_stale_lease_is_fenced_after_reclaim(h: Harness) -> None:
    user, worker, _, job = setup(h)
    t = enqueue(user, job)
    first = claim(worker)
    assert first is not None
    expire(h, t["id"])
    second = claim(worker)
    assert second is not None
    assert second["attempts"] == 2
    body = {"lease_token": first["lease_token"], "input_revision": "r1"}
    assert worker.post(f"/api/worker/tasks/{t['id']}/complete", json=body).status_code == 409
    body = {"lease_token": second["lease_token"], "input_revision": "r1"}
    assert worker.post(f"/api/worker/tasks/{t['id']}/complete", json=body).status_code == 200


def test_expired_lease_cannot_complete_and_attempts_exhaust(h: Harness) -> None:
    user, worker, _, job = setup(h)
    t = enqueue(user, job)
    for _ in range(3):
        got = claim(worker)
        assert got is not None
        expire(h, t["id"])
    assert claim(worker) is None
    state = user.get(f"/api/jobs/{job}/tasks").json()[0]
    assert state["state"] == "failed"
    assert "exhausted" in state["error"]


def test_wrong_input_revision_and_supersede_and_cancel(h: Harness) -> None:
    user, worker, _, job = setup(h)
    t = enqueue(user, job, "r1")
    got = claim(worker)
    assert got is not None
    bad = {"lease_token": got["lease_token"], "input_revision": "r0"}
    assert worker.post(f"/api/worker/tasks/{t['id']}/complete", json=bad).status_code == 409

    newer = enqueue(user, job, "r2")  # supersedes the running task
    hb = worker.post(
        f"/api/worker/tasks/{t['id']}/heartbeat", json={"lease_token": got["lease_token"]}
    )
    assert hb.json()["cancel_requested"] is True
    done = worker.post(
        f"/api/worker/tasks/{t['id']}/complete",
        json={"lease_token": got["lease_token"], "input_revision": "r1"},
    )
    assert done.json()["state"] == "cancelled"

    assert user.post(f"/api/tasks/{newer['id']}/cancel").json()["state"] == "cancelled"
    assert claim(worker) is None


def test_retryable_failure_requeues(h: Harness) -> None:
    user, worker, _, job = setup(h)
    t = enqueue(user, job)
    got = claim(worker)
    assert got is not None
    fail = {"lease_token": got["lease_token"], "error": "oom", "retryable": True}
    assert worker.post(f"/api/worker/tasks/{t['id']}/fail", json=fail).json()["state"] == "queued"
    got = claim(worker)
    assert got is not None
    fail = {"lease_token": got["lease_token"], "error": "bad input"}
    assert worker.post(f"/api/worker/tasks/{t['id']}/fail", json=fail).json()["state"] == "failed"


def test_worker_only_sees_its_owners_tasks_and_user_cannot_claim(h: Harness) -> None:
    user, worker, _, job = setup(h)
    enqueue(user, job)
    other = h.new_user("b@x.io")
    tok = other.post("/api/tokens", json={"kind": "worker", "label": "w"}).json()["token"]
    bare = TestClient(h.client.app)
    bare.headers["authorization"] = f"Bearer {tok}"
    assert claim(bare) is None
    assert user.post("/api/worker/claim", json={"capabilities": ["reconstruct"]}).status_code == 403
    assert claim(worker) is not None


def test_worker_artifacts_need_lease_and_recovery_cleans_up(h: Harness) -> None:
    user, worker, _, job = setup(h)
    t = enqueue(user, job)
    got = claim(worker)
    assert got is not None
    lease = {"x-lease-token": got["lease_token"]}
    url = f"/api/worker/tasks/{t['id']}/artifacts"

    assert (
        worker.put(
            url, params={"filename": "m.ply"}, content=b"abc", headers={"x-lease-token": "no"}
        ).status_code
        == 409
    )
    r = worker.put(url, params={"filename": "../m.ply"}, content=b"abc", headers=lease)
    assert r.status_code == 201
    art = r.json()
    assert art["filename"] == "m.ply"
    assert art["protected"] is False
    inp = worker.get(f"/api/worker/tasks/{t['id']}/inputs/{art['id']}", headers=lease)
    assert inp.content == b"abc"

    data_dir = h.path.parent / "files"
    orphan = data_dir / "artifacts" / job / "orphan"
    orphan.write_bytes(b"x")
    fail = {"lease_token": got["lease_token"], "error": "boom"}
    worker.post(f"/api/worker/tasks/{t['id']}/fail", json=fail)

    conn = db.connect(h.path)
    report = recovery.reconcile(conn, data_dir)
    conn.close()
    assert report["dropped_artifacts"] == [art["id"]]
    assert not orphan.exists()
    assert len(report["orphan_files"]) == 1
    assert not any(Path(data_dir / "artifacts" / job).iterdir())
