import json
from pathlib import Path

from scan3d_api.openapi import schema
from scan3d_api.testing import Harness


def test_job_lifecycle_and_ownership(h: Harness) -> None:
    assert h.client.get("/api/health").json()["status"] == "ok"
    assert h.client.get("/api/jobs").status_code == 401

    alice, bob = h.new_user("a@x.io"), h.new_user("b@x.io")
    created = alice.post("/api/jobs", json={"name": "mug"})
    assert created.status_code == 201
    job = created.json()
    assert job["status"] == "created"
    assert alice.get(f"/api/jobs/{job['id']}").json() == job
    assert [j["id"] for j in alice.get("/api/jobs").json()] == [job["id"]]

    assert bob.get(f"/api/jobs/{job['id']}").status_code == 404
    assert bob.get("/api/jobs").json() == []
    assert alice.get("/api/jobs/nope").status_code == 404
    assert alice.post("/api/jobs", json={"name": ""}).status_code == 422


def test_committed_openapi_is_current() -> None:
    committed = Path(__file__).parents[3] / "apps/web/openapi.json"
    assert json.loads(committed.read_text()) == schema(), "run `pnpm gen:api`"
