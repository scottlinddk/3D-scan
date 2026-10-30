"""Deterministic small meshes for stage tests."""

from typing import cast

import numpy as np
import trimesh


def cube() -> trimesh.Trimesh:
    return cast(trimesh.Trimesh, trimesh.creation.box(extents=(1, 1, 1)))


def open_cube() -> trimesh.Trimesh:
    mesh = cube()
    mesh.update_faces(np.arange(len(mesh.faces)) >= 2)
    mesh.remove_unreferenced_vertices()
    return mesh


def non_manifold() -> trimesh.Trimesh:
    mesh = cube()
    return trimesh.Trimesh(
        vertices=mesh.vertices.copy(),
        faces=np.vstack([mesh.faces, mesh.faces[:1]]),
        process=False,
    )


def meters() -> trimesh.Trimesh:
    return cast(trimesh.Trimesh, trimesh.creation.box(extents=(0.02, 0.03, 0.04)))


def debris() -> trimesh.Trimesh:
    small = trimesh.creation.box(extents=(0.05, 0.05, 0.05))
    small.apply_translation((2, 0, 0))
    return cast(trimesh.Trimesh, trimesh.util.concatenate([cube(), small]))


def ground_plane() -> trimesh.Trimesh:
    plane = trimesh.Trimesh(
        vertices=[[-2, -2, -0.5], [2, -2, -0.5], [2, 2, -0.5], [-2, 2, -0.5]],
        faces=[[0, 1, 2], [0, 2, 3]],
        process=False,
    )
    return cast(trimesh.Trimesh, trimesh.util.concatenate([cube(), plane]))
