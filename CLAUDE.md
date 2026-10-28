# CLAUDE.md

Guidance for Claude (and humans) working in this repository.

## Read first
- `docs/ARCHITECTURE.md`: components, pipeline stages, data contracts.
- `docs/IMPLEMENTATION_PLAN.md`: phases and issue dependencies. Do not start an issue whose dependencies are not merged.

## Writing style
- No em-dashes in docs, comments, commit messages or UI text. Use a period or a comma instead.
- English for code, docs and commits.

## Stack
- **Web (`apps/web`):** React + TypeScript (strict), Vite, TanStack Query v5, React Router v7, @react-three/fiber. pnpm.
- **iOS (`apps/capture-ios`):** Swift, SwiftUI, RealityKit Object Capture. Claude cannot build or run it here, so keep logic in small unit-tested types and list manual device checks in the PR.
- **Hosting:** Hetzner VPS, docker compose, Caddy, SQLite (WAL). See `deploy/`.
- **Python (`services/*`):** Python 3.12, uv, FastAPI, trimesh, pymeshlab, manifold3d, lib3mf. ruff + mypy (strict) + pytest.

## Conventions
- **Separation of concerns.** Web: `features/<name>/{api,components,hooks,pages}`, shared UI in `shared/ui`, styling in `shared/styles` (CSS modules + design tokens). No mesh math in the browser.
- **API types are generated** from the FastAPI OpenAPI schema into `apps/web/src/shared/api`. Never hand-write them.
- **TanStack Query:** query keys via a key factory per feature (`jobKeys.detail(id)`), no inline string keys.
- **Pipeline stages** are pure: `(mesh, params) -> StageResult(mesh, report)`. Never mutate inputs or earlier stage artifacts. One module per stage in `stages/`, each with tests in `tests/stages/`.
- **Units:** pipeline works in millimeters, +Z up, object resting on Z=0 after `orient`.
- **Validation is a gate.** Do not weaken validation to make a test pass.
- Printer data lives in `packages/printer-profiles/*.json`, never hard-coded.

## Definition of done
- Tests added and passing (`pnpm -r test`, `uv run pytest`).
- Lint and typecheck clean.
- Docs updated if a contract (capture bundle, job layout, API) changed.
- PR description links the issue (`Closes #N`) and states anything not done.
