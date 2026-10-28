# Implementation plan

Read [ARCHITECTURE.md](./ARCHITECTURE.md) first. Work is tracked as GitHub issues, one epic per milestone with sub-issues.

## Guiding principles

1. **Pipeline before clients.** The mesh pipeline and a CLI must produce a valid 3MF end to end before the web app or iOS app depend on it.
2. **Hosted from day one.** The stack runs on a Hetzner VPS, so auth, upload limits, backups and resource limits are part of phase 1, not afterthoughts.
3. **Every stage is testable in isolation** with small fixture meshes. No stage is "done" without tests.
4. **Validation is a hard gate.** Export refuses to write a 3MF from a non-manifold or out-of-bed mesh unless explicitly forced, and the report says why.
5. **Measure before promising.** CPU photogrammetry on the VPS and iOS capture quality are unknowns. Each has an issue that records real timings and results.

## Phases

### Phase 0: Foundation
Monorepo, tooling, CI, pipeline skeleton, printer profiles.
**Exit:** `pnpm test` and `uv run pytest` pass in CI on an empty skeleton.

### Phase 1: MVP on the VPS, scan file, photos and iOS to print-ready 3MF
Phase 1 is large, so it is split into four milestones that can overlap once the pipeline exists.

| Milestone | Epic | Scope | Exit |
| --- | --- | --- | --- |
| 1a | #2 | Pipeline stages and CLI (scan file to 3MF) | A scan file becomes a valid 3MF from the CLI |
| 1b | #2 | Hosted platform: API, auth, uploads, worker, web app, VPS deployment | Upload a scan file in the browser on the VPS and download a 3MF that imports into Bambu Studio correctly |
| 1c | #3 | Photos to mesh: remote Mac worker (primary), COLMAP + OpenMVS on the 4 GB arm64 VPS (limited fallback), capture guide | A photo set uploaded from the web app becomes a printable 3MF via the Mac worker, and a small set via the VPS fallback, with measured timings recorded |
| 1d | #4 | Native iOS app with Object Capture, on-device and raw-bundle upload, TestFlight | Capture on iPhone, get a printable 3MF back in the app without using a computer |

**Phase 1 exit:** the Bambu Studio checks from #14 pass for a scan file, a photo set and an iPhone capture, all through the VPS.

### Phase 2: Quality and advanced output
Agent skill, parametric remodel for functional parts, oversize splitting, multi-color and Bambu project 3MF research.
(Tracked in epic #5. It was called phase 4 in the first draft of this plan.)

## Issue map

| # | Milestone | Issue | Depends on |
| --- | --- | --- | --- |
| 1 | 0 | Epic: Foundation | |
| 2 | 1a, 1b | Epic: Phase 1, MVP (contains 1a and 1b, and links epics #3 and #4) | |
| 3 | 1c | Epic: Photos to mesh | |
| 4 | 1d | Epic: Native iOS capture app | |
| 5 | Phase 2 | Epic: Agent skill and advanced output | |
| 6 | 0 | Scaffold monorepo, tooling and CI | |
| 7 | 0 | Pipeline package skeleton, stage runner, fixtures | 6 |
| 8 | 0 | Printer profiles package | 6 |
| 9 | 1a | Stage: ingest | 7 |
| 10 | 1a | Stages: normalize + clean | 9 |
| 11 | 1a | Stage: repair | 10 |
| 12 | 1a | Stages: scale + orient | 11 |
| 13 | 1a | Stages: decimate + validate | 12, 8 |
| 14 | 1a | Stage: export 3MF + STL, Bambu Studio import checklist | 13 |
| 15 | 1a | CLI: end-to-end run | 14 |
| 16 | 1b | API service and OpenAPI contract | 7 |
| 32 | 1b | Auth: web sessions and device/worker API tokens | 16 |
| 33 | 1b | Resumable uploads, quotas and retention | 16, 32 |
| 17 | 1b | Worker and SQLite job queue on the VPS | 15, 16 |
| 18 | 1b | Web: scaffold, login, upload, job list and status | 6, 16, 32 |
| 19 | 1b | Web: 3D viewer with stage compare and issue overlays | 18 |
| 20 | 1b | Web: interactive fixes and re-run from stage | 19, 17 |
| 21 | 1b | Deploy to the Hetzner VPS (compose, TLS, backups, limits) | 17, 18 |
| 22 | 1c | Reconstructor interface + COLMAP/OpenMVS arm64 CPU fallback adapter (4 GB limits) | 17, 33, 23 |
| 24 | 1c | Capture guide documentation | 22 |
| 35 | 1c | Spike: metric scale for COLMAP from ARKit poses | 22 |
| 23 | 1c | Remote Mac worker (Apple Object Capture), primary full-detail photo path | 17, 32 |
| 25 | 1d | iOS capture app (on-device and raw-bundle upload) | 16, 32, 33 |
| 34 | 1d | iOS CI and TestFlight distribution | 25 |
| 26 | Phase 2 | Agent skill: scan-to-print | 15 |
| 27 | Phase 2 | Parametric remodel path for functional parts | 26 |
| 28 | Phase 2 | Spike: multi-color 3MF for Bambu Studio (AMS) | 14 |
| 29 | Phase 2 | Spike: Bambu Studio project 3MF (plates, settings) | 14 |
| 30 | Phase 2 | Split oversize models to fit the bed | 13, 14 |

Chains: 9 to 15 is sequential. 16, 32, 33 and 18 can run in parallel with it. 22 and 25 can run in parallel once 17 and 16/32/33 are merged.

## Risks to watch

| Risk | Why | Mitigation |
| --- | --- | --- |
| Photogrammetry on a 4 GB arm64 VPS runs out of memory or is very slow | No GPU, little RAM. COLMAP dense needs CUDA, OpenMVS CPU is slow and memory hungry, no official arm64 images | Mac worker is the primary photo path. VPS is a fallback with strict limits (about 20 to 40 images, downscaled), measured in #22. Also iOS on-device mesh. Bigger server only if needed |
| Mac worker offline | Personal machine can be asleep | Jobs wait with a visible reason, user can choose VPS fallback per job |
| arm64 library gaps | `lib3mf` has no aarch64 Linux wheel, COLMAP/OpenMVS have no arm64 images | Own 3MF writer (lib3mf only in tests), build COLMAP/OpenMVS from source for arm64 in CI. Check wheels again when building |
| No metric scale from photos | Photos alone have no scale | iOS bundle with ARKit poses (#35), reference dimension in UI (#20), printed scale card (#24) |
| iOS work cannot be verified by Claude | Needs Xcode, a device and an Apple Developer account | Keep the Swift code thin, unit-test client and manifest logic, manual device checklist per PR |
| Phase 1 is large | Four clients and a hosted platform | Milestones 1a to 1d, with a working demo after each |
| Internet-facing service handling untrusted files | Mesh, archive and image parsers | Auth, limits, non-root containers, timeouts (#21, #32, #33) |

## Working with Claude on issues

Each issue mentions `@claude`. To have Claude implement an issue via GitHub:

1. The workflow is in `.github/workflows/claude.yml`. Add the repository secret `ANTHROPIC_API_KEY` (or switch to `CLAUDE_CODE_OAUTH_TOKEN`, see the comments in the file) and make sure the Claude GitHub app is installed on the repo.
2. Comment `@claude implement this` on the issue **once its dependencies are merged**. Mentions in the original issue body only trigger if the workflow is installed when the issue is opened.
3. Review the PR like any other. `CLAUDE.md` holds the conventions Claude follows.

Work one dependency layer at a time to avoid merge conflicts between parallel PRs. iOS PRs and anything touching Bambu Studio need a manual test by you.
