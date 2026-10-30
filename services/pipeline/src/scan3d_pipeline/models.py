"""Shared stage contracts. Coordinates are millimeters, +Z up."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Protocol

import trimesh

type JsonValue = str | int | float | bool | list[JsonValue] | dict[str, JsonValue] | None


@dataclass
class Mesh:
    geometry: trimesh.Trimesh

    def copy(self) -> Mesh:
        return Mesh(self.geometry.copy())


@dataclass
class StageReport:
    metrics: dict[str, JsonValue] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    params: dict[str, JsonValue] = field(default_factory=dict)
    duration: float = 0.0

    def to_dict(self) -> dict[str, JsonValue]:
        return asdict(self)


@dataclass
class StageResult:
    mesh: Mesh
    report: StageReport


class Stage(Protocol):
    @property
    def name(self) -> str: ...

    def run(self, mesh: Mesh, params: dict[str, JsonValue]) -> StageResult: ...
