import json
from pathlib import Path

import numpy as np
import pytest
import trimesh
from scan3d_pipeline.models import JsonValue, Mesh, Stage, StageReport, StageResult
from scan3d_pipeline.runner import run
from scan3d_pipeline.stages.identity import Identity

from .fixtures import cube, debris, ground_plane, meters, non_manifold, open_cube


class Translate:
    name = "translate"

    def run(self, mesh: Mesh, params: dict[str, JsonValue]) -> StageResult:
        mesh.geometry.apply_translation((1, 0, 0))
        params["mutated"] = True
        return StageResult(mesh, StageReport(metrics={"faces": len(mesh.geometry.faces)}))


def test_layout_isolation_and_resume(tmp_path: Path) -> None:
    mesh = Mesh(cube())
    original = mesh.geometry.vertices.copy()
    params: dict[str, dict[str, JsonValue]] = {"translate": {"distance": 1}}
    stages: list[Stage] = [Identity(), Translate()]
    reports = run(stages, mesh, tmp_path, params)
    np.testing.assert_array_equal(mesh.geometry.vertices, original)
    assert params == {"translate": {"distance": 1}}
    assert reports[1].duration >= 0
    first = tmp_path / "stages/01-identity"
    snapshots = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in first.iterdir()}
    for name in ["01-identity", "02-translate"]:
        directory = tmp_path / "stages" / name
        assert {p.name for p in directory.iterdir()} == {"mesh.ply", "preview.glb", "report.json"}
        preview = trimesh.load(directory / "preview.glb")
        assert isinstance(preview, trimesh.Scene)
    report = json.loads((tmp_path / "stages/02-translate/report.json").read_text())
    assert report["params"] == {"distance": 1}
    run(stages, None, tmp_path, start_from="translate")
    assert snapshots == {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in first.iterdir()}
    output = trimesh.load_mesh(tmp_path / "stages/02-translate/mesh.ply")
    np.testing.assert_allclose(output.bounds, [[0.5, -0.5, -0.5], [1.5, 0.5, 0.5]])


def test_invalid_requests(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown"):
        run([Identity()], Mesh(cube()), tmp_path, start_from="missing")
    with pytest.raises(ValueError, match="unique"):
        run([Identity(), Identity()], Mesh(cube()), tmp_path)
    with pytest.raises(ValueError, match="input mesh"):
        run([Identity()], None, tmp_path)
    with pytest.raises((OSError, ValueError)):
        run([Identity(), Translate()], None, tmp_path, start_from="translate")
    assert not (tmp_path / "stages").exists()


def test_report_serialization() -> None:
    report = StageReport(metrics={"bounds": [1, 2, 3]}, warnings=["unknown units"])
    assert StageReport(**json.loads(json.dumps(report.to_dict()))) == report


def test_fixtures() -> None:
    assert cube().is_watertight
    assert not open_cube().is_watertight
    assert not non_manifold().is_watertight
    np.testing.assert_allclose(meters().extents, [0.02, 0.03, 0.04])
    assert len(debris().split()) == 2
    assert len(ground_plane().faces) == len(cube().faces) + 2
