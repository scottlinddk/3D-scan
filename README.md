# 3d-scan

Scan a physical object and get a **print-ready 3MF** for **Bambu Studio** (Bambu Lab printers).

Inspired by [wesbos/3d-model-anything](https://github.com/wesbos/3d-model-anything), which scans rooms into Three.js scenes. This project applies the same "capture the evidence, then reconstruct" idea to objects, with printability as the goal: watertight, manifold, correctly scaled in mm, flat on the bed, and within the printer's build volume.

## How it will work

1. **Capture** with the native iOS app, a photo set, or an existing scanner app (Polycam, Scaniverse, Reality Composer).
2. **Upload** to the web app (or the iOS app) running on your own VPS.
3. **Pipeline:** ingest, clean, repair, scale, orient, decimate, validate.
4. **Review** in the 3D viewer, fix orientation or scale if needed.
5. **Export** 3MF (and STL) and open it in Bambu Studio.

## Status

Early scaffolding. The repo layout, tooling and CI are in place, the features are tracked in the issues.
See:
- [Architecture](docs/ARCHITECTURE.md)
- [Implementation plan](docs/IMPLEMENTATION_PLAN.md)
- [Issues](https://github.com/scottlinddk/3d-scan/issues) for the task breakdown

## Development

Requirements: Node 22 (`.nvmrc`), pnpm 10 (via Corepack), and [uv](https://docs.astral.sh/uv/) (installs Python 3.12 from `.python-version`).

```sh
corepack enable
pnpm install          # web dependencies
uv sync               # Python dependencies (services/*)

pnpm dev              # web app on http://localhost:5173
pnpm check            # lint, typecheck and tests for web and Python

pnpm test             # web tests only
pnpm test:py          # Python tests only (uv run pytest)
pnpm lint             # ESLint, Prettier, ruff, mypy
```

Layout: `apps/web` (React), `services/api` and `services/pipeline` (Python), `apps/capture-ios` and
`services/reconstructor-macos` (Swift, later), `packages/printer-profiles`, `deploy`, `docs`.
