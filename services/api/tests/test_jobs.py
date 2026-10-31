import json
from pathlib import Path

from fastapi.testclient import TestClient
from scan3d_api.app import create_app


def test_job_lifecycle_and_openapi() -> None:
    client = TestClient(create_app())
    assert client.get("/api/health").json()["status"] == "ok"

    created = client.post("/api/jobs", json={"name": "mug"})
    assert created.status_code == 201
    job = created.json()
    assert job["status"] == "created"
    assert client.get(f"/api/jobs/{job['id']}").json() == job
    assert [j["id"] for j in client.get("/api/jobs").json()] == [job["id"]]

    assert client.get("/api/jobs/nope").status_code == 404
    assert client.post("/api/jobs", json={"name": ""}).status_code == 422
    assert "createJob" in str(client.get("/openapi.json").json())


def test_committed_openapi_is_current() -> None:
    committed = Path(__file__).parents[3] / "apps/web/openapi.json"
    assert json.loads(committed.read_text()) == create_app().openapi(), "run `pnpm gen:api`"
