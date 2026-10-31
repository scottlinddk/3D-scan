"""Reconstructor contract and the Apple Object Capture adapter.

The adapter runs one fixed executable with structured arguments. It never builds a shell command.
Metric scale from sensor metadata is evidence, not proof of accuracy, so results still need a
measured-reference check downstream.
"""

import os
import signal
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

DETAILS = frozenset({"preview", "reduced", "medium", "full", "raw"})


class ReconstructionError(Exception):
    pass


class Cancelled(Exception):
    pass


class Reconstructor(Protocol):
    name: str

    def reconstruct(
        self, photos_dir: Path, out_path: Path, *, detail: str, tick: Callable[[], bool]
    ) -> None:
        """Write a model to out_path. `tick` runs about once a second and returns True to cancel."""
        ...


class ObjectCaptureReconstructor:
    name = "apple-object-capture"

    def __init__(self, binary: Path) -> None:
        self.binary = binary

    def reconstruct(
        self, photos_dir: Path, out_path: Path, *, detail: str, tick: Callable[[], bool]
    ) -> None:
        if detail not in DETAILS:
            raise ReconstructionError(f"unsupported detail level: {detail}")
        args = [str(self.binary), str(photos_dir), str(out_path), "--detail", detail]
        with subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,  # own process group, so cancel also stops its children
        ) as proc:
            while True:
                try:
                    _, err = proc.communicate(timeout=1)
                    break
                except subprocess.TimeoutExpired:
                    if tick():
                        os.killpg(proc.pid, signal.SIGTERM)
                        try:
                            proc.communicate(timeout=10)
                        except subprocess.TimeoutExpired:
                            os.killpg(proc.pid, signal.SIGKILL)
                            proc.communicate()
                        raise Cancelled from None
            if proc.returncode != 0:
                tail = (err or "").strip().splitlines()[-5:]
                raise ReconstructionError(f"exit {proc.returncode}: {' | '.join(tail)}")
        if not out_path.is_file() or out_path.stat().st_size == 0:
            raise ReconstructionError("reconstructor produced no output")
