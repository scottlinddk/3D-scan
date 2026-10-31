# Issue amendments and missing work

Prepared 2026-10-31 after reading the existing issue bodies and scope-changing comments. These are issue-ready drafts, not live issue changes. IDs A/R/B/S/T/P/Q/MW are local aliases; replace them with actual issue numbers only when filed. Dependencies are implementation prerequisites unless explicitly described as research inputs. No issue text here should trigger implementation automation merely by being copied.

## Amend existing issues

Retain the existing issue numbers, preserve relevant tests and add the criteria below. [The implementation plan](IMPLEMENTATION_PLAN.md) is the complete dependency map.

### #2: Epic: External scan to tested P1S project and MakerWorld publication

Replace the broad scan/photos/iOS MVP exit with milestones M1 to M4. Add #29 and B/S/T/P/MW to the main path. Move photo and native capture to linked follow-on epics. Acceptance is the principal end-to-end test in the plan; partial exits stay explicitly named geometry, slice, print and publication evidence. Do not require every supported capture client before this can ship.

### #9: Ingest surface meshes and retain original evidence

Dependencies: #7, A. Start with GLB/PLY as a small increment, retain the remaining format scope for follow-up PRs.

- [ ] Surface faces are required for the mesh path. Gaussian-splat PLY and point-cloud-only inputs produce a specific unsupported-input explanation with surface-mesh re-export guidance.
- [ ] Declared units, axis conventions and scene transforms are retained as provenance. Unknown units are explicit, not assumed mm.
- [ ] Original files, UVs, textures, materials, vertex colours and OBJ sidecars remain immutable. Format fixtures describe what survives load, stage save/reload and preview. No general colour-export promise.
- [ ] Bounded archive expansion and limited-process decoding reject excessive files safely, including before face counting where required. Optional pre-simplification is recorded and never silently applied across protected features.

### #10 and #12: Resolve metric scale before cleanup and repair

Replace #12's blanket dependency on #11 with separately mergeable scale and orientation parts. `#10 normalize -> #12 scale -> #10 clean -> #11 repair -> #12 orient` is the corrected chain. #10 normalize still depends on #9.

- [ ] Unknown units stop before `planeDistanceMm`, repair size, base cuts or mm deviation limits. Explicit decorative target sizing is allowed and labelled as such.
- [ ] #12 records declared-unit conversion separately from any later correction, with one consistent transform chain.
- [ ] In M2, accept several positive real measurements with artifact-bound selections, calibration/check roles, tolerances and optional explicit weights. Fit uniform scale and report every signed/absolute mm and relative residual. Do not silently discard conflicting measurements.
- [ ] Test consistent references, conflicting references, invalid/zero distances, held-out checks and already-metric input. Synthetic tolerances are not marketed as scan accuracy.
- [ ] Critical disagreements block dimensional approval until resolved. A user may explicitly switch to decorative target sizing, which remains distinct from checked physical dimensions. No anisotropic correction disguised as uniform scaling.
- [ ] #10 lists/remembers removed components and geometry, including multi-part objects. #12 base cuts run the same feature/deviation review as repair, then validate again.

### #11: Preserve intended openings and explain repair

Dependencies: #10 clean after metric scale. Reuse #19 for display and #20 for review, with pipeline reports testable before the UI exists.

- [ ] User constraints identify openings, cavities and regions to preserve in an immutable source frame. Closed through-holes are not treated as defective boundary holes.
- [ ] Local repairs and remeshes report filled patches, removed components, method, parameters and bidirectional deviation in mm with sampling coverage/limitations. Volume change is unavailable when either mesh lacks a valid closed volume.
- [ ] Constraint remapping across topology changes is verified or marked unresolved. A global surface-distance pass cannot replace opening/clearance and cross-section checks.
- [ ] Regression fixtures include a damaged shell, mounting bore and open functional cavity. A candidate that fills the bore/cavity cannot be accepted just because it is watertight.
- [ ] Unsupported constraints or repairs beyond limits stop with an actionable review/rescan/CAD recommendation. Alternative repairs retain the same parent; user acceptance never suppresses a failed geometry gate.

M1 can ship conservative local repairs with explicit stop conditions. Aggressive automatic remeshing is not required before M2 constraints/review exist.

### #13: Keep validation and warning coverage explicit

Dependencies: #12 orient, #8.

- [ ] Preserve existing topology, winding, positive-volume, bed-fit, base and simplification gates. Add a reliable intersection check or explicitly report that check as unverified, with no claim that it passed. Unrun required checks block validated export; optional warnings cannot stand in for required gates.
- [ ] Extend the already-planned thin-wall warnings with locations, nozzle/process context, sample coverage and limitations. Absence of sampled warnings is not a minimum-wall guarantee.
- [ ] Reports distinguish geometry validity, checked dimensions and unresolved repair reviews. Export/project/publication readiness consumes the exact revision's results.

### #14: Geometry 3MF export and ARM64 library decision

Dependency: #13. Replace both the original unconditional `lib3mf` choice and the later unconditional custom-writer instruction with the bounded spike below. Reconcile the issue, architecture and ADR in the decision PR.

- [ ] Selected exporter writes mm units, a mesh/build item and expected metadata; reimport checks geometry, transforms, units, bounds and topology within recorded numeric tolerances.
- [ ] Independent structural validation cannot be silently skipped in the sole export-acceptance job. ARM64 runtime and developer/CI platforms have explicit support results.
- [ ] A real scan and fixture import into pinned Bambu Studio targeting P1S, without repair prompt, at checked size and flat on the bed. Record version/OS and screenshots; until run, mark manual acceptance pending.
- [ ] Validated exports reject current validation errors and stale validation hashes. Any diagnostic force path produces separately labelled unvalidated artifacts, excluded from B/S/T/P.
- [ ] Core geometry 3MF is labelled separately from the Bambu project delivered by B.

**Spike: py-lib3mf compatibility and provenance.** Compare the separate third-party `py-lib3mf` package to official bindings and a minimal writer, using the Python 3.12 production image on Linux ARM64. Check package publisher/source, release attestation/checksum, bundled native library version/license, ABI/glibc, import name/conflicts, API usage, fixture round trip, peak memory and Bambu import. Verify supported development-platform installation too. Deliver a short ADR decision, exact candidate version/hash and reproducible commands/results. PyPI's wheel listing is evidence to investigate, not a completed runtime check. Choose a custom writer only if measured compatibility/maintenance evidence justifies it.

### #15, #17 and #33: Safe replay and lifecycle

- #15 depends on #14 and A. Expose scale decisions, stable report codes and revision IDs; a rerun invalidates affected downstream artifacts before showing new readiness.
- #17 depends on #15/#16/#32 and A. Fence stale worker results by lease; reconcile filesystem publication with SQLite status after crashes. Claim capabilities generically for B and later #23.
- #33 depends on #16/#32. Retention must not remove tested/published artifacts, photographs or required parents. Report which optional intermediates are no longer available for replay.

Acceptance additions: failure-injection tests for stale completion/recovery; rerun leaves upstream hashes unchanged; tested and published revisions survive retention cleanup; diagnostic artifacts cannot become project inputs.

### #19 and #20: Extend stage comparison and guide the next decision

Dependencies: #19 on #18 and report contracts; #20 on #19/#17, R and #11/#12 changes.

- [ ] Reuse the stage compare view for input versus candidate, adjacent stages and repair alternatives, with identical cameras/metric frame and clear distinction between edits and placement transforms.
- [ ] Display mm deviation legend/method, removed components, filled regions, qualified volume change and relevant sections. Unavailable checks are visible.
- [ ] Lightweight-preview selections map to the authoritative artifact; stale picks/reviews are rejected after a revision change.
- [ ] Guided mode presents the next unresolved item among size, repair review, orientation/base, warnings, print settings and publication. Advanced controls remain available. Do not invent a single readiness score that conceals failed evidence gates.
- [ ] Before a rerun, identify downstream invalidations, including slice and test-print status. Mouse, keyboard and touch users can review and confirm decisions.
- [ ] API-backed tests cover conflicting measurements, protected-feature failure, stale review and changed-project print status, in addition to existing request/query tests.

### #21: Measure the actual VPS envelope

Dependencies: #17/#18/#33. Retain deploy/security/restore scope, remove #22 as a gate for initial deployment.

- [ ] Benchmark representative increasing scan sizes through loading, copies, cleanup, repair, comparison, preview and export on the actual ARM64 VPS. Record OS/image/versions, mesh counts/bytes, peak RSS/container memory, swap, time and temporary disk per stage.
- [ ] Derive supported limits/headroom from measurements; test controlled over-limit, timeout, disk-full and OOM recovery. No invented 500k-face safe limit.
- [ ] Restore a backup containing a tested project and verify all required hashes/relationships. Referenced evidence is retained.

### #29: Spike: Generate an editable Bambu project through the pinned Mac CLI

Move from advanced epic #5 into main epic #2, ahead of B. Prototype with a fixture now; final acceptance depends on #14 output.

**Question:** Can one pinned Mac build generate a geometry-retaining P1S project from the validated model and resolved settings without manual rebuilding?

**Method:** Read the official CLI guide, run the chosen executable's help, pin binary/build checksum and resolve full machine/nozzle/plate/material/process configs. Exercise load, arrange, export and slice. Reopen the exported project and compare geometry, units, object transforms, plate, printer, nozzle and relevant process settings. Test a sliced export as well to ensure the retained project is not a geometry-less G-code package. Do not synthesize Bambu metadata. Check licensing/distribution implications before bundling an executable.

**Acceptance:**

- [ ] `docs/research/bambu-project-3mf.md` records exact version, OS, arguments/config hashes, fixture project and reopen screenshots/results.
- [ ] Geometry counts/bounds/placement survive and project settings are editable. No hidden rescale, auto-update or unsupported-preset substitution.
- [ ] Once a suitable account is available, validate project acceptance in the current MakerWorld upload flow without submitting. Record that result separately from Bambu reopen. No account-backed action is performed in this planning pass.
- [ ] A bounded go/no-go decision names any remaining manual steps. Go feeds B; no-go retains validated geometry plus a documented Bambu-assisted handoff and marks the project milestone incomplete.

### Photo and advanced issue corrections

- #3: rename to Mac-first photo reconstruction; remove mandatory CPU fallback from exit.
- #23: extract the common reconstructor interface currently assigned to #22; depend on #17/#32/#33/Q, reuse B transport. Verify Apple OS/hardware/API requirements and sensor-scale claims against real captures. Acceptance includes an ordinary real photo set and a measured object, not just synthetic images.
- #24: remove #22 as a prerequisite. Draft external-scan export/measurement guidance with #9/#12; add QC retakes, coverage and real Mac capture lessons in M5. No numerical accuracy guarantee.
- #22: defer the constrained CPU fallback. Keep a separate actual-VPS benchmark and explicit no-go path when quality/memory/time are unsuitable.
- #25/#34: later native capture. Raw capture uses #23 first; verify devices/OS and retain manual hardware checks.
- #5: remove #29; #26/#27/#28/#30 remain later. #27 adds STEP plus editable CAD recipe, opening/cavity/section and dimensional gates, benchmarked separately from decorative scans. Remove its unsupported consumer-scan accuracy range. #28 first tests appearance survival and a minimal representation; no assumed AMS support.

## Missing implementation issues

### A: Publish pipeline stage attempts atomically

**Milestone:** M0, next smallest implementation. **Depends on:** closed #7.

**Problem:** The runner overwrites final PLY/GLB/report paths sequentially. A failing rerun can mix new geometry with an old report. Directory/file existence currently substitutes for a completed stage.

**Scope:** Write unique attempt directories, verify a hash manifest, atomically publish a reference after all files complete, preserve previous successful attempts, and require the commit manifest for resume. Define same-filesystem rename/durability behavior and explicit handling of old directories. Keep the pure Stage API; update reader/writer tests and architecture together. No database, API or full recipe engine in this issue.

**Acceptance:**

- [ ] Fail PLY export, GLB export, report/manifest write and pointer publication independently, on first run and rerun. No partial attempt becomes current and the prior committed attempt is still readable.
- [ ] Inject process termination between artifact writes and around commit; restart sees only a complete generation. Document process-crash versus power-loss guarantees and filesystem assumptions.
- [ ] Resume rejects missing/tampered outputs. Earlier stage files/hashes remain unchanged. The success path still returns reports in stage order.
- [ ] Legacy layouts have a documented explicit import/recompute path; orphan temporary attempts are safely ignored/cleaned.

### R: Versioned recipes, artifact lineage and reusable alternatives

**Milestone:** M1 minimal provenance, M2 branches/cache. **Depends on:** A, #15.

**Scope:** Versioned manifest of input/artifact hashes, resolved parameters/defaults, source/stage/dependency/runtime versions, transforms, seeds, measurements/constraints and printer/configuration identity. Keep alternative attempts with parent relationships. Reuse only verified artifacts with matching effective inputs; invalidate affected descendants. API/UI exposure extends #16/#19/#20.

**Acceptance:**

- [ ] Export includes sufficient recipe and version data to explain its inputs and decisions. Replay documents platform/numeric tolerances and nondeterminism.
- [ ] Identical recipe inputs reuse verified work; changing a measurement, dependency or stage implementation invalidates the appropriate descendants. A changed presentation-only listing field does not rerun mesh repair.
- [ ] Two repair alternatives share immutable upstream artifacts and remain independently comparable/exportable. Corrupted cached output is rejected, never reused.

### B: Generate Bambu Studio projects on a Mac capability worker

**Milestone:** M3. **Depends on:** #29 go decision, #14/#17/#32, R.

**Scope:** Generate projects using the pinned executable/configuration path proven in #29. Reuse capability claims/leases from #17, remembered user preferences and immutable settings snapshots. Return an editable project with geometry plus artifact manifest and logs. Keep the adapter independent of later Object Capture code.

**Acceptance:**

- [ ] A validated real scan becomes a project with selected P1S, nozzle, plate, material and process without manually rebuilding the project. Reopen checks geometry/scale/placement/settings; version and configuration hashes are recorded.
- [ ] Unknown or unavailable presets stop with a precise correction, without substitution. Invalid/stale/diagnostic geometry cannot enter project generation.
- [ ] Offline Mac waits visibly. Timeout, cancellation, expired lease and duplicate result handling leave the previous project intact and do not advance readiness.
- [ ] Changing model or effective settings produces a new project revision with no inherited slicing or print evidence. Actual Mac execution/reopen remains a named manual acceptance check until automated there.

### S: Verify projects with a pinned slicer and known settings

**Milestone:** M3. **Depends on:** B.

**Scope:** Adapter invocation on the exact project, initially Bambu Studio on the Mac. Store executable/version/configuration hashes, final placement, command arguments, exit status, logs and any estimates the selected version can reliably expose. Keep geometry-containing project and generated slice data distinct.

**Acceptance:**

- [ ] One good and one deliberately unsliceable fixture exercise success/failure. Missing executable, timeout and malformed output are distinct outcomes.
- [ ] Slicing cannot silently update settings, rescale or reorient a project. If settings change, create a new project and rerun its gates.
- [ ] Supported time/filament/support estimates include units and provenance; unavailable values are null with reasons, not guesses.
- [ ] Report/UI say slicing verified for this hash and explicitly leave physical-print status unverified. A library or configuration change invalidates previous slice verification.

### T: Freeze tested projects and attach finished-print evidence

**Milestone:** M4. **Depends on:** B, S, #16/#18/#33.

**Scope:** Immutable print attempt records tied to project file/settings hashes. User records actual P1S setup, outcome, deviations and original phone photographs. Keep reference-object and finished-print photos distinct; preserve originals and create reversible cover crops. Import an externally edited Bambu project as a new revision before it can be marked tested.

**Acceptance:**

- [ ] A successful user-confirmed print has date, project revision, actual settings confirmation and at least one genuine finished-print photograph. Original-object photos/screenshots cannot fulfil this product evidence gate.
- [ ] Failed prints remain useful records but cannot establish success. Photo upload alone cannot establish success either.
- [ ] Geometry, arrangement, nozzle, material or process edits create a clearly untested revision. Previous tested project and its photos remain available; listing-only edits can retain that project's evidence.
- [ ] A manual P1S test confirms the saved project matches the printed revision. This cannot be completed by an automated slicer test.

### P: Editable MakerWorld listing, publication kit and guided updates

**Milestone:** M4. **Depends on:** T, #20, MW findings or explicitly pending platform checks.

**Scope:** Prefill editable title/description, proposed category/tags, dimensions, material/nozzle/layer/support settings, assembly notes, explicit license and attribution. Reuse stored facts; ask only for unresolved decisions. Package project 3MF, optional STL, finished-print photos/crops, listing text/data, evidence summaries and hash manifest in one revisioned kit. Guide transfer and retain published URL/model/profile IDs and revision history for updates.

**Acceptance:**

- [ ] User can review one listing and obtain all selected assets together without rebuilding a Bambu project or composing a listing from scratch. License/attribution require explicit choices; unknown facts stay marked unresolved.
- [ ] Cover assistance retains original phone photos and previews crops using verified platform rules when available. Do not hard-code unverified dimensions, limits or compatibility codes.
- [ ] Readiness requires matching geometry, measurement/review, slice and physical-print evidence. Bundle manifest always names the tested project selected for publication.
- [ ] Fallback offers one kit, grouped field-copy actions and a precise guided checklist, recording which transfers still require user action. No one-click claim.
- [ ] User can attach the published URL/IDs and exact listing/project revision, then prepare an update to that publication without losing history. New model revisions are untested until separately printed.
- [ ] If a companion/adapter is later approved, session expiry preserves the local draft; partial uploads resume known assets; uncertain submit results reconcile before retry; updates require existing IDs to prevent duplicates. Live write integration is a separately scoped implementation after MW, not hidden inside the fallback.

### Q: Photo-quality preflight shared by web upload and Mac reconstruction

**Milestone:** M5. **Depends on:** #33/#18 for integration; local QC prototype needs only image fixtures.

**Scope:** Bounded image decode, EXIF orientation handling and versioned per-image checks for blur, under/overexposure, exact/near duplicates, undersized and corrupt files. Show affected images/contact sheet, reasons and actionable retake guidance. Preserve originals; let users exclude/replace with recorded decisions before expensive reconstruction. Extract overlap with #22's planned blur/resolution checks into this shared issue.

**Acceptance:**

- [ ] Reproducible fixture images exercise every finding and exact duplicates/near-duplicate groups. Check thresholds and analysis versions are in the QC report/recipe.
- [ ] Users can identify and replace affected photos from a phone. Guidance addresses focus/motion, lighting or pixel size for the actual finding.
- [ ] Reconstruction waits for unresolved blocking input errors and records any accepted quality warnings; adding/replacing a photo invalidates QC/reconstruction, not unrelated projects.
- [ ] A real capture session records useful/false-positive findings and retakes. Synthetic fixtures are labelled and no scan-accuracy/coverage guarantee is inferred from QC.

## Missing research issue

### MW: Spike: Current MakerWorld submission and supported handoff feasibility

**Milestone:** start read-only research early, gate live integration in M4. **Depends on:** no implementation for documentation research; B/T required for later real-project acceptance tests.

**Question:** What is the least manual reliable route from a tested project/listing to a MakerWorld model and print profile, including updates?

**Scope:** Verify the current upload guide, profile/photo rules and authenticated submission UI before encoding platform requirements. Evaluate supported APIs/deep links/import/handoff first, then a user-session local/browser companion. Use ModelPrep for hypotheses only. Separate model and profile creation, account permissions/eligibility, draft save, asset uploads, verification/moderation state, public publication, readback and updates.

**Acceptance:**

- [ ] Dated requirement matrix links official sources and authenticated observations for field names, image/file rules, licences, attribution, genuine finished-print evidence and printer compatibility. Unknowns remain unknown; do not copy third-party constants into production.
- [ ] Establish whether any supported publishing API/account connection exists and document evidence or inability to establish it. Compare maintenance/session/permission costs of supported handoff, local companion and reverse-engineered calls. Recommend one route or no-go.
- [ ] State how session expiry, disconnect/revocation, failed/partial uploads, uncertain submit responses, duplicate submissions and updates to existing IDs are handled. Keep credentials out of VPS logs/bundles where possible.
- [ ] Document a staged verification plan: read-only UI first, later specifically authorized draft/upload tests, then separately authorized public creation and update with post-submit readback. A private draft is not proof of public publishing.
- [ ] Deliver `docs/research/makerworld-integration.md`, evidence matrix and a bounded follow-up implementation task only after a go decision. On no-go or blocked access, P's prepared kit/guided handoff stays usable and limitations remain visible.

**Current status:** official wiki retrieval returned 402 and the upload URL was inaccessible. No browser-control connection was available. No authenticated flow, upload or publication was tested. This planning task must not create MakerWorld drafts or publish content.
