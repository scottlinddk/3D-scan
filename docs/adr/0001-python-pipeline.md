# ADR 0001: Python for the mesh pipeline

- Status: accepted
- Date: 2026-10-28

## Context

The core of the project repairs and prepares scanned meshes for 3D printing (hole filling, manifold
repair, decimation, boolean operations, 3MF export). The maintainer's main stacks are
TypeScript/React and C#/.NET.

## Decision

Write the mesh pipeline and the API in Python 3.12 (uv, FastAPI, trimesh, PyMeshLab, manifold3d).
The web app stays TypeScript/React. The iOS app and the Mac worker are Swift.

## Why

- The mature mesh-processing libraries (PyMeshLab, pymeshfix, manifold3d, trimesh, usd-core) are in
  Python. The .NET and TypeScript ecosystems would mean writing repair algorithms ourselves.
- The production host is a 4 GB arm64 Hetzner VPS. These libraries ship aarch64 Linux wheels
  (checked against PyPI), with one exception: `lib3mf` does not. The 3MF writer is therefore our own
  small writer, and `lib3mf` is used only as a validator in tests.

## Consequences

- The API and the pipeline share one language and one uv workspace (`services/*`).
- The web app talks to the API only through generated OpenAPI types.
- Python is pinned to 3.12 (`.python-version`), because the PyMeshLab wheels we depend on target it.

## Tooling notes

- **TypeScript is pinned to 6.0.x** (`~6.0`) in `apps/web`. `typescript-eslint` does not support
  TypeScript 7.0 yet, and linting is part of the definition of done. Revisit when
  `typescript-eslint` supports TypeScript 7.
