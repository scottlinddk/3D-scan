"""The iOS client decodes fixtures under apps/capture-ios; they must match the real responses."""

import json
from pathlib import Path

from scan3d_api.testing import Harness

FIXTURES = Path(__file__).parents[3] / "apps/capture-ios/Tests/CaptureKitTests/Fixtures"


def keys(name: str) -> set[str]:
    return set(json.loads((FIXTURES / f"{name}.json").read_text()))


def test_ios_fixtures_match_api_responses(h: Harness) -> None:
    c = h.new_user("a@x.io")
    job = c.post("/api/jobs", json={"name": "j", "source_kind": "photos"}).json()
    up = c.post(f"/api/jobs/{job['id']}/uploads", json={"filename": "a", "size": 1}).json()
    c.patch(f"/api/uploads/{up['id']}", params={"offset": 0}, content=b"x")
    art = c.post(f"/api/uploads/{up['id']}/complete").json()
    task = c.post(
        f"/api/jobs/{job['id']}/tasks", json={"capability": "reconstruct", "input_revision": "r1"}
    ).json()
    assert set(job) == keys("job")
    assert set(up) == keys("upload")
    assert set(art) == keys("artifact")
    assert set(task) == keys("task")
