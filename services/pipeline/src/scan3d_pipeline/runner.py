"""Ordered stage execution and resumable artifacts."""

import json
import re
from collections.abc import Sequence
from copy import deepcopy
from pathlib import Path
from time import perf_counter

import trimesh

from scan3d_pipeline.models import JsonValue, Mesh, Stage, StageReport


def run(
    stages: Sequence[Stage],
    mesh: Mesh | None,
    job_dir: Path,
    params: dict[str, dict[str, JsonValue]] | None = None,
    *,
    start_from: str | None = None,
) -> list[StageReport]:
    """Run stages, isolating their inputs. Reruns load the preceding saved PLY.

    Stage numbering starts at 01. Earlier artifacts are never rewritten.
    The caller owns job.json, input/ and export/ lifecycle.
    """
    names = [stage.name for stage in stages]
    if len(set(names)) != len(names) or any(
        re.fullmatch(r"[a-z][a-z0-9_-]*", name) is None for name in names
    ):
        raise ValueError("Stage names must be unique, safe path components")
    if start_from is not None and start_from not in names:
        raise ValueError(f"Unknown stage: {start_from}")
    start = names.index(start_from) if start_from is not None else 0
    if start:
        previous = job_dir / "stages" / f"{start:02d}-{names[start - 1]}" / "mesh.ply"
        mesh = Mesh(trimesh.load_mesh(previous, process=False))
    if mesh is None:
        raise ValueError("An input mesh is required when starting at the first stage")
    reports = []
    for index in range(start, len(stages)):
        stage = stages[index]
        used_params = deepcopy((params or {}).get(stage.name, {}))
        started = perf_counter()
        result = stage.run(mesh.copy(), deepcopy(used_params))
        result.report.duration = perf_counter() - started
        result.report.params = used_params
        # Serialize before writing so invalid report data does not leave partial artifacts.
        report_json = json.dumps(result.report.to_dict(), indent=2, allow_nan=False)
        directory = job_dir / "stages" / f"{index + 1:02d}-{stage.name}"
        directory.mkdir(parents=True, exist_ok=True)
        result.mesh.geometry.export(directory / "mesh.ply")
        result.mesh.geometry.export(directory / "preview.glb")
        (directory / "report.json").write_text(report_json + "\n", encoding="utf-8")
        reports.append(result.report)
        mesh = result.mesh.copy()
    return reports
