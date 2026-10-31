"""Thin API client for the worker endpoints. Takes any httpx.Client so tests can inject one."""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx

CHUNK = 1024 * 1024


class LeaseLost(Exception):
    """The API no longer recognises our lease (expired, superseded or already completed)."""


class ApiClient:
    def __init__(self, http: httpx.Client) -> None:
        self.http = http

    def _check(self, r: httpx.Response) -> httpx.Response:
        if r.status_code == 409:
            raise LeaseLost(r.text)
        r.raise_for_status()
        return r

    def claim(self, capabilities: list[str], lease_seconds: int = 60) -> dict[str, Any] | None:
        r = self._check(
            self.http.post(
                "/api/worker/claim",
                json={"capabilities": capabilities, "lease_seconds": lease_seconds},
            )
        )
        task: dict[str, Any] | None = r.json()["task"]
        return task

    def heartbeat(self, task_id: str, lease: str, extend: int = 60) -> bool:
        r = self._check(
            self.http.post(
                f"/api/worker/tasks/{task_id}/heartbeat",
                json={"lease_token": lease, "extend_seconds": extend},
            )
        )
        return bool(r.json()["cancel_requested"])

    def download_input(self, task_id: str, lease: str, artifact_id: str, dest: Path) -> None:
        url = f"/api/worker/tasks/{task_id}/inputs/{artifact_id}"
        with self.http.stream("GET", url, headers={"x-lease-token": lease}) as r:
            self._check(r)
            with dest.open("wb") as f:
                for block in r.iter_bytes(CHUNK):
                    f.write(block)

    def upload_artifact(
        self,
        task_id: str,
        lease: str,
        path: Path,
        *,
        filename: str,
        kind: str,
        parent_id: str | None,
    ) -> dict[str, Any]:
        def blocks() -> Iterator[bytes]:
            with path.open("rb") as f:
                while block := f.read(CHUNK):
                    yield block

        params = {"filename": filename, "kind": kind}
        if parent_id:
            params["parent_id"] = parent_id
        r = self._check(
            self.http.put(
                f"/api/worker/tasks/{task_id}/artifacts",
                params=params,
                content=blocks(),
                headers={"x-lease-token": lease},
            )
        )
        artifact: dict[str, Any] = r.json()
        return artifact

    def complete(self, task_id: str, lease: str, revision: str, result: dict[str, Any]) -> None:
        self._check(
            self.http.post(
                f"/api/worker/tasks/{task_id}/complete",
                json={"lease_token": lease, "input_revision": revision, "result": result},
            )
        )

    def fail(self, task_id: str, lease: str, error: str, *, retryable: bool = False) -> None:
        self._check(
            self.http.post(
                f"/api/worker/tasks/{task_id}/fail",
                json={"lease_token": lease, "error": error[:2000], "retryable": retryable},
            )
        )
