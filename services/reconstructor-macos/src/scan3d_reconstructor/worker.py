"""Claim a `reconstruct` task, preflight the photos, reconstruct, upload, complete.

Payload: {"photos": [{"artifact_id": str, "filename": str}], "detail": "full",
          "skip_preflight": false}
"""

import json
import re
import tempfile
import time
from contextlib import suppress
from pathlib import Path
from typing import Any

import httpx
from scan3d_pipeline.preflight import run_preflight

from scan3d_reconstructor.client import ApiClient, LeaseLost
from scan3d_reconstructor.reconstructor import Cancelled, ReconstructionError, Reconstructor

CAPABILITY = "reconstruct"
HEARTBEAT_EVERY = 15.0
SAFE = re.compile(r"[^A-Za-z0-9._-]")


def run_once(api: ApiClient, rec: Reconstructor) -> bool:
    """Process at most one task. Returns False when the queue had nothing for us."""
    task = api.claim([CAPABILITY])
    if task is None:
        return False
    tid, lease = task["id"], task["lease_token"]
    # A failure report is best effort: if the lease is already gone, nothing of ours may advance it.
    gone = (LeaseLost, httpx.HTTPError)
    try:
        _process(api, rec, task)
    except LeaseLost:
        pass  # someone else owns this task now
    except Cancelled:
        with suppress(*gone):
            api.complete(tid, lease, task["input_revision"], {"cancelled": True})
    except ReconstructionError as e:
        with suppress(*gone):
            api.fail(tid, lease, str(e))
    except httpx.TransportError as e:
        with suppress(*gone):
            api.fail(tid, lease, f"transport: {e}", retryable=True)
    return True


def _process(api: ApiClient, rec: Reconstructor, task: dict[str, Any]) -> None:
    tid, lease, payload = task["id"], task["lease_token"], task["payload"]
    photos = payload.get("photos") or []
    if not photos:
        raise ReconstructionError("payload has no photos")
    with tempfile.TemporaryDirectory(prefix="scan3d-") as tmp:
        root = Path(tmp)
        photos_dir = root / "photos"
        photos_dir.mkdir()
        for i, ph in enumerate(photos):
            name = SAFE.sub("_", Path(ph["filename"]).name) or "photo"
            api.download_input(tid, lease, ph["artifact_id"], photos_dir / f"{i:04d}_{name}")

        report = run_preflight(sorted(photos_dir.iterdir()))
        if report.retake and not payload.get("skip_preflight"):
            raise ReconstructionError(
                "preflight_blocked: " + json.dumps(report.to_dict()["retake"])
            )

        last_beat = time.monotonic()

        def tick() -> bool:
            nonlocal last_beat
            if time.monotonic() - last_beat < HEARTBEAT_EVERY:
                return False
            last_beat = time.monotonic()
            return api.heartbeat(tid, lease)

        out = root / "model.usdz"
        rec.reconstruct(photos_dir, out, detail=payload.get("detail", "full"), tick=tick)
        artifact = api.upload_artifact(
            tid,
            lease,
            out,
            filename="model.usdz",
            kind="reconstruction",
            parent_id=photos[0]["artifact_id"],
        )
        api.complete(
            tid,
            lease,
            task["input_revision"],
            {
                "artifact_id": artifact["id"],
                "reconstructor": rec.name,
                "preflight": {
                    "qc_version": report.qc_version,
                    "warnings": report.warnings,
                    "flagged": report.retake,
                },
            },
        )
