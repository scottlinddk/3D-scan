# 3d-scan

Turn a physical object scan into a **validated model**, a **Bambu Studio project**, and a prepared **MakerWorld publication**. This is the target workflow; the implementation is still a scaffold.

Inspired by [wesbos/3d-model-anything](https://github.com/wesbos/3d-model-anything), which scans rooms into Three.js scenes. This project applies the same "capture the evidence, then reconstruct" idea to objects, with printability as the goal: watertight, manifold, correctly scaled in mm, flat on the bed, and within the printer's build volume.

## How it will work

1. **Capture** with the native iOS app, a photo set, or an existing scanner app (Polycam, Scaniverse, Reality Composer).
2. **Upload** to the web app (or the iOS app) running on your own VPS.
3. **Prepare:** ingest, normalize, establish scale, clean, repair, orient, simplify and validate.
4. **Review:** check dimensions, protected features, repair changes and warnings.
5. **Generate** a Bambu Studio project with remembered settings and verify slicing.
6. **Test-print** on the P1S and attach photographs of the finished print to that project revision.
7. **Prepare** an editable listing and publication kit for a guided MakerWorld handoff. Publishing integration remains a research task.

## Status

The repo layout, tooling, identity-stage runner and deterministic fixtures exist. Processing, API, viewer, Bambu project generation and publication preparation are not implemented yet. Deliver the external scan-file path first; Mac photo reconstruction follows, with native capture and constrained VPS photogrammetry later.
See:
- [Architecture](docs/ARCHITECTURE.md)
- [Implementation plan and dependency map](docs/IMPLEMENTATION_PLAN.md)
- [Current assessment](docs/REVIEW.md)
- [Issue-ready amendments and missing work](docs/BACKLOG.md)
- [Research evidence](docs/research/scan-to-publication.md) and [verification ledger](docs/VERIFICATION.md)
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
