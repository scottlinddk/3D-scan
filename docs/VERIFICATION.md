# Verification ledger

Planning baseline: 2026-10-31, upstream `17491ecd4729be807e4359a1a77e77c6c7c7822d`. Empty evidence is pending, never a pass. No MakerWorld drafts, uploads or publications were created in this planning task.

## Current evidence

| Check | Status | Evidence or limitation |
| --- | --- | --- |
| Repository/scaffold | Inspected | All tracked files, issue backlog and scope comments read via GitHub connector; current main matches supplied snapshot. |
| Upstream scaffold CI | Passed upstream | [CI run](https://github.com/scottlinddk/3D-scan/actions/runs/41107870439), same commit. This is not local test execution or pipeline acceptance. |
| Documentation-only revision | Locally checked | Relative links, issue-number references, source snapshot hashes, whitespace and prohibited punctuation checked before handoff. No feature code/dependency changes. |
| Scan ingest through validated 3MF | Pending | Identity stage only. M1 must supply real scan and fixture results. |
| Actual VPS peak-memory/restore | Pending | No access to target machine; #21 supplies measurements and recovery evidence. |
| Multiple physical measurement agreement | Pending | No measured real object supplied. Synthetic scaling tests alone cannot satisfy this. |
| Bambu Mac project generation/reopen | Pending | Official CLI guide read; executable and resolved configs not run. #29/B. |
| Pinned slicer success | Pending | No slicer executed. S. |
| P1S physical print with finished-print photo | Pending | Needs actual printer, project revision and user-confirmed result. T. |
| MakerWorld requirements/authenticated UI | Blocked for this review | Wiki returned 402, upload URL inaccessible, browser-control tools unavailable. MW spike remains open. |
| MakerWorld file acceptance/draft/publication/update | Not performed | Requires later authorized user/account verification. Third-party private tests do not count. |
| Mac real-photo reconstruction | Pending | M5/Q/#23; no reconstruction or accuracy measurement performed. |

## Manual product acceptance record

Use one record per attempt. Keep failed attempts and observations. Store private photo/scan assets outside the repository unless intentionally licensed for distribution.

```text
Date/operator:
Input scan source/app and file hashes:
Object reference photos and measured lengths/tolerances:
Model revision/recipe hash:
Scale source and per-measurement residuals:
Repair/protected-feature decisions and comparison evidence:
Geometry validation report/hash and unverified checks:
Bambu executable version/checksum, macOS:
P1S/nozzle/plate/material/process configuration hashes:
Project revision/file hash and geometry-retention/reopen evidence:
Slicer result/logs/estimates and exact project hash:
Physical print date/outcome and actual setup confirmation:
Finished-print photo hashes (distinct from reference-object photos):
Listing revision, license/attribution choices and cover crop references:
Kit hash and exact tested project selected:
MakerWorld current-requirements check date/source:
Manual transfer steps still required:
Remote model/profile IDs, published URL and status readback:
Update history and prior publication revision:
Pending checks, failures and deviations:
```

The principal acceptance test is complete only when that externally captured scan's tested project and prepared listing are actually published and read back, without rebuilding the project or rewriting the listing. A prepared kit is useful deliverable evidence, not proof of publication. If any geometry or effective print settings change, start a new project/print record and show the new revision as not test-printed.
