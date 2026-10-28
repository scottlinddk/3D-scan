# Implementation plan

Read [ARCHITECTURE.md](./ARCHITECTURE.md) first. Work is tracked as GitHub issues, one epic per phase with sub-issues.

## Guiding principles

1. **Pipeline before UI.** The mesh pipeline and a CLI must produce a valid 3MF end to end before the web app depends on it.
2. **Bring your own scan first.** Phase 1 accepts files from existing scanner apps. Photogrammetry (phase 2) and a native iOS app (phase 3) come only after the pipeline proves itself.
3. **Every stage is testable in isolation** with small fixture meshes. No stage is "done" without tests.
4. **Validation is a hard gate.** Export refuses to write a 3MF from a non-manifold or out-of-bed mesh unless explicitly forced, and the report says why.

## Phases

### Phase 0: Foundation
Monorepo, tooling, CI, pipeline skeleton, printer profiles.
**Exit:** `pnpm test` and `uv run pytest` pass in CI on an empty skeleton.

### Phase 1: MVP, scan file to print-ready 3MF
Ingest USDZ/GLB/OBJ/PLY, clean, repair, scale, orient, decimate, validate, export 3MF. CLI first, then API, worker and web UI.
**Exit:** a scan from Polycam/Scaniverse/Reality Composer goes through the web UI and the resulting 3MF imports into Bambu Studio as a single solid object at the correct size, sitting flat on the plate, with no repair prompts.

### Phase 2: Photos to mesh
Reconstructor adapters (COLMAP + OpenMVS in Docker, Apple Object Capture on macOS) and a capture guide.
**Exit:** a zip of photos of a test object produces a printable 3MF.

### Phase 3: Native capture app (optional)
SwiftUI app using Object Capture, exporting `capture-bundle/1`.
**Exit:** capture on iPhone, AirDrop to Mac, printable 3MF without manual steps.

### Phase 4: Agent skill and advanced output
`scan-to-print` agent skill, parametric remodel for functional parts, oversize splitting, and research spikes on multi-color and Bambu project 3MF.

## Issue map

| # | Phase | Issue | Depends on |
| --- | --- | --- | --- |
| 1 | 0 | Epic: Foundation | |
| 2 | 1 | Epic: MVP scan to 3MF | |
| 3 | 2 | Epic: Photos to mesh | |
| 4 | 3 | Epic: Native iOS capture | |
| 5 | 4 | Epic: Agent skill and advanced output | |
| 6 | 0 | Scaffold monorepo, tooling and CI | |
| 7 | 0 | Pipeline package skeleton, stage runner, fixtures | 6 |
| 8 | 0 | Printer profiles package | 6 |
| 9 | 1 | Stage: ingest | 7 |
| 10 | 1 | Stages: normalize + clean | 9 |
| 11 | 1 | Stage: repair | 10 |
| 12 | 1 | Stages: scale + orient | 11 |
| 13 | 1 | Stages: decimate + validate | 12, 8 |
| 14 | 1 | Stage: export 3MF + STL, Bambu Studio import checklist | 13 |
| 15 | 1 | CLI: end-to-end run | 14 |
| 16 | 1 | API service and OpenAPI contract | 7 |
| 17 | 1 | Worker and SQLite job queue | 15, 16 |
| 18 | 1 | Web: scaffold, upload, job list and status | 6, 16 |
| 19 | 1 | Web: 3D viewer with stage compare and issue overlays | 18 |
| 20 | 1 | Web: interactive fixes and re-run from stage | 19, 17 |
| 21 | 1 | Local-first packaging (docker compose) | 17, 18 |
| 22 | 2 | Reconstructor interface + COLMAP/OpenMVS adapter | 17 |
| 23 | 2 | macOS Object Capture reconstructor CLI | 22 |
| 24 | 2 | Capture guide documentation | 22 |
| 25 | 3 | iOS capture app (capture-bundle/1) | 23 |
| 26 | 4 | Agent skill: scan-to-print | 15 |
| 27 | 4 | Parametric remodel path for functional parts | 26 |
| 28 | 4 | Spike: multi-color 3MF for Bambu Studio (AMS) | 14 |
| 29 | 4 | Spike: Bambu Studio project 3MF (plates, settings) | 14 |
| 30 | 4 | Split oversize models to fit the bed | 13, 14 |

Issues 9 to 14 are a chain, but 16 and 18 can run in parallel with them.

## Working with Claude on issues

Each issue mentions `@claude`. To have Claude implement an issue via GitHub:

1. Install the Claude GitHub app and workflow (run `/install-github-app` in Claude Code, or follow the [Claude Code GitHub Actions docs](https://docs.claude.com/en/docs/claude-code/github-actions)).
2. Comment `@claude implement this` on the issue **once its dependencies are merged**. Mentions in the original issue body only trigger if the workflow is installed when the issue is opened.
3. Review the PR like any other. `CLAUDE.md` holds the conventions Claude follows.

Work one dependency layer at a time to avoid merge conflicts between parallel PRs.
