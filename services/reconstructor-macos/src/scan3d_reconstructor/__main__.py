"""`scan3d-reconstructor`: poll the API for photo-reconstruction tasks.

Environment: SCAN3D_API_URL, SCAN3D_WORKER_TOKEN, SCAN3D_OBJECT_CAPTURE_BIN.
"""

import os
import time
from pathlib import Path

import httpx

from scan3d_reconstructor.client import ApiClient
from scan3d_reconstructor.reconstructor import ObjectCaptureReconstructor
from scan3d_reconstructor.worker import run_once

POLL_SECONDS = 5.0


def main() -> None:
    http = httpx.Client(
        base_url=os.environ["SCAN3D_API_URL"],
        headers={"authorization": f"Bearer {os.environ['SCAN3D_WORKER_TOKEN']}"},
        timeout=httpx.Timeout(30.0, read=300.0),
    )
    rec = ObjectCaptureReconstructor(Path(os.environ["SCAN3D_OBJECT_CAPTURE_BIN"]))
    api = ApiClient(http)
    while True:
        try:
            busy = run_once(api, rec)
        except httpx.TransportError:
            busy = False  # API unreachable: the Mac is outbound-only, so just retry
        if not busy:
            time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
