"""No-op stage for exercising the runner."""

from scan3d_pipeline.models import JsonValue, Mesh, StageReport, StageResult


class Identity:
    name = "identity"

    def run(self, mesh: Mesh, params: dict[str, JsonValue]) -> StageResult:
        return StageResult(mesh.copy(), StageReport())
