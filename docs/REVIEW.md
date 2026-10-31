# Current implementation assessment

Reviewed 2026-10-31. GitHub default branch `main` still points to `17491ecd4729be807e4359a1a77e77c6c7c7822d`, dated 2026-10-30. The earlier snapshot remains current. Inspected all 56 tracked files, repository guidance (`CLAUDE.md`, no AGENTS.md present), all 34 issues including closed issues, and the scope-changing issue comments. #6/#7 are closed; the remaining 32 issues are open. The [upstream CI run](https://github.com/scottlinddk/3D-scan/actions/runs/41107870439) succeeded for that commit. It verifies the scaffold, not scan-to-print functionality.

## What exists

- pnpm/uv workspaces, strict TypeScript/Python tooling, CI and one placeholder React page. TanStack Query, Router and React Three Fiber are planned; they are not installed in `apps/web/package.json` yet.
- Typed `Mesh`, `StageReport`, `StageResult` and `Stage` contracts in `services/pipeline/src/scan3d_pipeline/models.py`.
- Sequential identity-stage runner with copied inputs/parameters, supplied-parameter/duration reports, numbered PLY/GLB/JSON artifacts and resume from the previous PLY.
- Six deterministic mesh fixtures and six tests in total, including package smoke tests. No real scan acceptance evidence.
- API package version only, with no FastAPI dependency or endpoints. Printer profiles, Mac reconstruction, iOS capture, deployment and agent skill are README placeholders.

There is no ingest, cleanup, repair, scale/orient, validation, 3MF export, CLI, job queue, functional viewer or MakerWorld workflow. This pass changes planning documents only.

## Findings that affect implementation order

| Priority | Evidence | Consequence and refinement |
| --- | --- | --- |
| First | `runner.py:51-55` creates/reuses the final directory and writes PLY, GLB and report sequentially. `runner.py:37-38` resumes by file path only. | A failed write/rerun can leave new mesh data with an old preview/report. Add atomic immutable attempts and verified commit references before production use (draft A). Serialization before writing protects only one failure class. |
| First | Architecture's old stage order was clean, repair, then scale. #10 uses `planeDistanceMm`; #11 has hole-size thresholds. | Resolve real scale before all mm-based cleanup/repair. Split #12's early scale and late orientation work, removing its old dependency on #11 for scale. |
| Core path | #14 body uses `lib3mf`, its comment and ADR require a custom writer; #29 remains under advanced epic #5. | Evaluate separate third-party `py-lib3mf` ARM64 wheels before choosing. Move #29 to the main path and generate Bambu projects through a pinned CLI. |
| Core path | #12/#20 accept one reference; #11 fills holes/remeshes; #19 already compares stages. | Extend those tasks for multiple checks, protected features and quantified change review. Do not duplicate comparison or thin-wall work already in #13. |
| Reliability | `Mesh` holds only a Trimesh. Reports have no hashes/versions; PLY resumption uses float32 and is not full scene/texture preservation. Runner copies whole meshes; preview exports full geometry. | Add explicit unit/appearance provenance, recipes, immutable relationships and measured resource limits. Do not promise colour survival or fit from this skeleton. |
| Scope | Old #2 exit requires scan file, photos and native iOS; #3 still says VPS in its title; #24 waits for #22. | Deliver external scan first, then guided review, project/slice, print/publication preparation, then Mac photos with QC. Defer native capture and CPU fallback. |

## External verification limits

Official Bambu CLI project-export support and a Python 3.12 Linux ARM64 `py-lib3mf` wheel listing were read. Neither was executed on the target hardware. The MakerWorld guide returned 402 in the research tool, the upload page was inaccessible, and browser-control tools were unavailable. No authenticated submission UI, file acceptance, account connection, public API, physical print or publication was verified. These remain explicit spikes and manual gates, documented in [research](research/scan-to-publication.md) and [verification](VERIFICATION.md).

Direct git cloning also failed because the execution environment's proxy was unreachable. The review copy was assembled from pinned GitHub connector file reads. Local source hashes were checked against the Git tree. No runtime dependencies were changed or feature implementation attempted.

## Deliverables

- [Architecture](ARCHITECTURE.md): metric order, constrained workers, guided review, revision/evidence contracts and publication handoff.
- [Implementation plan](IMPLEMENTATION_PLAN.md): reused issue map, dependency corrections, delivery exits and next small milestone.
- [Backlog](BACKLOG.md): ready-to-copy amendments, missing issues and research spikes. These are drafts, not posted issues.
- [Research ledger](research/scan-to-publication.md) and [verification ledger](VERIFICATION.md): source strength, access failures, go/no-go questions and honest pending checks.
