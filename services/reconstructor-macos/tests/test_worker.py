import io
import stat
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from scan3d_api import auth, db
from scan3d_api.testing import Harness
from scan3d_reconstructor import worker
from scan3d_reconstructor.client import ApiClient
from scan3d_reconstructor.reconstructor import (
    Cancelled,
    ObjectCaptureReconstructor,
    ReconstructionError,
)


def jpeg(seed: int, *, blur: bool = False) -> bytes:
    rng = np.random.default_rng(seed)
    img = Image.fromarray(rng.integers(0, 256, (1200, 1200), dtype=np.uint8)).convert("RGB")
    if blur:
        img = img.resize((12, 12)).resize((1200, 1200))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=95)
    return buf.getvalue()


class Env:
    def __init__(self, h: Harness, photos: list[bytes], **payload: Any) -> None:
        self.h = h
        self.user = h.new_user("a@x.io")
        tok = self.user.post("/api/tokens", json={"kind": "worker", "label": "mac"}).json()["token"]
        http = TestClient(h.client.app)
        http.headers["authorization"] = f"Bearer {tok}"
        self.api = ApiClient(http)
        self.job = self.user.post("/api/jobs", json={"name": "j", "source_kind": "photos"}).json()
        refs = []
        for i, data in enumerate(photos):
            up = self.user.post(
                f"/api/jobs/{self.job['id']}/uploads",
                json={"filename": f"p{i}.jpg", "size": len(data), "kind": "photo"},
            ).json()
            self.user.patch(f"/api/uploads/{up['id']}", params={"offset": 0}, content=data)
            art = self.user.post(f"/api/uploads/{up['id']}/complete").json()
            refs.append({"artifact_id": art["id"], "filename": f"p{i}.jpg"})
        self.task = self.user.post(
            f"/api/jobs/{self.job['id']}/tasks",
            json={
                "capability": "reconstruct",
                "input_revision": "r1",
                "payload": {"photos": refs, **payload},
            },
        ).json()

    def state(self) -> dict[str, Any]:
        tasks: list[dict[str, Any]] = self.user.get(f"/api/jobs/{self.job['id']}/tasks").json()
        return tasks[0]


class Fake:
    name = "fake"

    def __init__(self, behaviour: Callable[[Path, Callable[[], bool]], None] | None = None) -> None:
        self.behaviour = behaviour

    def reconstruct(
        self, photos_dir: Path, out_path: Path, *, detail: str, tick: Callable[[], bool]
    ) -> None:
        assert len(list(photos_dir.iterdir())) >= 1
        if self.behaviour:
            self.behaviour(out_path, tick)
        out_path.write_bytes(b"usdz")


def test_happy_path_uploads_model_with_provenance(h: Harness) -> None:
    env = Env(h, [jpeg(1), jpeg(2), jpeg(3)])
    assert worker.run_once(env.api, Fake()) is True
    state = env.state()
    assert state["state"] == "succeeded"
    assert state["result"]["reconstructor"] == "fake"
    assert state["result"]["preflight"]["flagged"] == []
    arts = env.user.get(f"/api/jobs/{env.job['id']}/artifacts").json()
    model = next(a for a in arts if a["kind"] == "reconstruction")
    assert model["id"] == state["result"]["artifact_id"]
    assert model["protected"] is False
    assert env.user.get(f"/api/artifacts/{model['id']}/content").content == b"usdz"
    assert worker.run_once(env.api, Fake()) is False  # queue is empty


def test_preflight_blocks_until_user_overrides(h: Harness) -> None:
    env = Env(h, [jpeg(1), jpeg(2, blur=True)])
    called = []
    worker.run_once(env.api, Fake(lambda *_: called.append(1)))
    state = env.state()
    assert state["state"] == "failed"
    assert state["error"].startswith("preflight_blocked")
    assert "p1.jpg" in state["error"]
    assert called == []

    env2 = Env(
        Harness(h.path.parent / "b.sqlite"), [jpeg(1), jpeg(2, blur=True)], skip_preflight=True
    )
    worker.run_once(env2.api, Fake())
    assert env2.state()["state"] == "succeeded"


def test_cancel_request_stops_reconstruction(h: Harness, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(worker, "HEARTBEAT_EVERY", 0.0)
    env = Env(h, [jpeg(1), jpeg(2)])

    def behaviour(_out: Path, tick: Callable[[], bool]) -> None:
        env.user.post(f"/api/tasks/{env.task['id']}/cancel")
        if tick():
            raise Cancelled

    worker.run_once(env.api, Fake(behaviour))
    assert env.state()["state"] == "cancelled"


def test_lost_lease_never_advances_the_task(h: Harness) -> None:
    env = Env(h, [jpeg(1), jpeg(2)])

    def behaviour(_out: Path, _tick: Callable[[], bool]) -> None:
        conn = db.connect(h.path)
        past = (auth.now() - timedelta(seconds=5)).isoformat()
        conn.execute("UPDATE tasks SET lease_expires=?", (past,))
        conn.close()

    worker.run_once(env.api, Fake(behaviour))  # upload is rejected with 409, swallowed
    assert env.state()["state"] != "succeeded"
    assert [
        a
        for a in env.user.get(f"/api/jobs/{env.job['id']}/artifacts").json()
        if a["kind"] == "reconstruction"
    ] == []


def script(path: Path, body: str) -> Path:
    path.write_text(f"#!/bin/sh\n{body}\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


def test_object_capture_adapter_runs_fixed_binary(tmp_path: Path) -> None:
    ok = script(tmp_path / "ok", 'echo model > "$2"')
    out = tmp_path / "m.usdz"
    ObjectCaptureReconstructor(ok).reconstruct(tmp_path, out, detail="full", tick=lambda: False)
    assert out.read_text() == "model\n"

    bad = script(tmp_path / "bad", "echo boom >&2; exit 3")
    with pytest.raises(ReconstructionError, match="exit 3: boom"):
        ObjectCaptureReconstructor(bad).reconstruct(
            tmp_path, tmp_path / "x", detail="full", tick=lambda: False
        )
    with pytest.raises(ReconstructionError, match="unsupported detail"):
        ObjectCaptureReconstructor(ok).reconstruct(
            tmp_path, tmp_path / "y", detail="full; rm -rf /", tick=lambda: False
        )
    slow = script(tmp_path / "slow", "sleep 30")
    with pytest.raises(Cancelled):
        ObjectCaptureReconstructor(slow).reconstruct(
            tmp_path, tmp_path / "z", detail="full", tick=lambda: True
        )
