# Scan-to-publication research ledger

Reviewed 2026-10-31. Documentation establishes intended or reported functionality, not independent performance. No external tool, scanner, printer or publishing integration was run in this planning pass. Follow-up spike bodies and acceptance criteria are in [BACKLOG.md](../BACKLOG.md).

## Integration decisions and remaining evidence

| Integration | Evidence inspected | What can be concluded | Unresolved gate |
| --- | --- | --- | --- |
| Bambu Studio | [Official CLI guide](https://github.com/bambulab/BambuStudio/wiki/Command-Line-Usage), edited 2026-03-31 | Documents configuration loading, arranging, slicing and project 3MF export. Prefer its project writer over invented metadata. | #29 must verify a pinned Mac executable, resolved configs, geometry/settings survival and MakerWorld acceptance. No candidate build has yet been selected or run. |
| Print-profile meaning | [Bambu explanation](https://blog.bambulab.com/makerworld-one-step-printing/) | Explains why a profile carries geometry preparation and printing information. A core geometry 3MF alone does not deliver that experience. | Actual current compatibility and acceptance must be tested. The older article is not a current submission specification. |
| MakerWorld official requirements | [Model upload guide](https://wiki.bambulab.com/en/makerworld/tutorials/how-to-upload-models), [profile upload guide](https://wiki.bambulab.com/en/makerworld/tutorials/print-profile-upload), [community guidelines](https://makerworld.com/en/community-guidelines) | All three fetches returned 402 in the research tool. The [upload route](https://makerworld.com/en/my/models/upload) was inaccessible. | Authenticated UI not inspected; browser-control tools were unavailable. No field names, dimensions, limits or compatibility codes are certified here. MW spike must verify them. |
| Genuine print photographs | User requirement; official guide inaccessible as above | 3D-scan will require genuine finished-print evidence for its tested-profile workflow regardless of unknown UI wording. Object-reference photos and renders cannot satisfy this product gate. | Verify the exact current MakerWorld photo rule, accepted image formats/crops and model/profile distinctions. Do not infer a live requirement from old forum discussions. |
| Supported publishing API | Official-page attempts and targeted search for MakerWorld developer/publishing documentation | No officially documented public publishing API was established. This is a research limit, not proof that none exists. | MW must verify supported connection/handoff options and platform permission before an integration commitment. |
| ModelPrep | [Reverse-engineered flow](https://github.com/iamdjem/modelprep/blob/main/backend/docs/makerworld-web-flow.md), file blob `1e2c94e4f9cdb8b76611d0429b4e55d8d2ac5436` | Author reports private submission tests and later read-only UI audits. Public/remix/other branches remain separately qualified. Useful hypotheses for session, asset and draft lifecycle. | Third-party reports are not 3D-scan tests or a supported contract. Do not copy endpoint constants, taxonomy, auth claims or file limits as verified requirements. |
| Core 3MF exporter | [py-lib3mf 2.5.0 files](https://pypi.org/project/py-lib3mf/2.5.0/), linked [packaging repository](https://github.com/jdegenstein/py-lib3mf), [upstream lib3mf](https://github.com/3MFConsortium/lib3mf) | Separate third-party packaging lists a CPython 3.12 manylinux ARM64 wheel, Apache-2.0 metadata and PyPI provenance details. The old blanket no-wheel rationale is insufficient. | #14 spike checks the actual wheel/checksum/attestation, bundled library, glibc/ABI/API, platform support, round trips and memory. Not installed or validated here. |

The official CLI options include `--load-settings`, `--load-filaments`, `--arrange`, `--slice`, and `--export-3mf`. The guide calls for full configurations rather than unresolved resource-profile fragments. Resolve presets through the pinned toolchain, record all effective settings, and confirm exact syntax from that executable. Do not present an untested command template as a working Mac recipe. Exporting slice data must not replace the required geometry-containing project.

## MakerWorld integration recommendation

| Route | Present feasibility assessment | Delivery decision |
| --- | --- | --- |
| Supported API or documented application handoff | Not established by accessible official evidence. | Investigate first in MW; do not promise. |
| Prepared publication kit with guided website transfer | Independent of an undocumented API. Still needs current UI checks to make the checklist precise. | Initial P deliverable: one kit, remembered facts, editable listing, grouped copy actions, phone photos and recorded publication URL/revisions. Manual transfer stays visible. |
| Local/browser companion using the user's session | Candidate for reducing file picking and copying. No current session or authenticated UI available for testing here. | Evaluate in MW, including platform permission, session storage, user review, supported browsers and maintenance cost. Not implemented or advertised. |
| Reverse-engineered hosted upload | ModelPrep reports a broader lifecycle, with qualified certification. Supported auth/API and public publishing remain unestablished for this project. | No production commitment. Prefer keeping account secrets out of the VPS; require a scoped follow-up and separate live verification if pursued. |

The transfer design needs explicit states for disconnected/expired session, assets uploading/failed, draft prepared, verification pending/failed, submission outcome unknown, published and update pending. Retain upload intents, asset hashes and remote IDs. Reconcile status after uncertainty before resubmitting, and select an existing publication ID for updates. Keep an offline prepared kit usable during integration failures. No automatic retries that can create duplicate listings, and no one-click publishing claim before the full public create/update path has evidence.

## Capability references

| Reference | Useful lesson for 3D-scan | Evidence boundary |
| --- | --- | --- |
| [MeshRight](https://github.com/Huzy85/MeshRight) | Plain-language problem explanations, next-decision guidance, reviewable cleanup, orientation choices and deviation display. Extend #19/#20 rather than recreating its whole editor. | README identifies an early alpha and reports local processing, repair, comparison, export and MCP capabilities. No performance or feature tests run here. |
| [phone-to-print-3d](https://github.com/yuanluxu/phone-to-print-3d) | Per-photo QC and explicit validation/slicer gates. Extract the general pattern, not accuracy claims. | README labels synthetic capture and a dense-depth stand-in in its published verification. Reported surface error is not demonstrated real-photo reconstruction accuracy. |
| [stl2step](https://github.com/nickpagz/stl2step) | Later functional CAD should check dimensions, openings, cavities and sections, with editable recipes/STEP. Surface deviation alone is insufficient. | Tool/benchmark descriptions are author reports. Do not inherit their tolerances or results as scan guarantees. |
| [3d-model-anything](https://github.com/wesbos/3d-model-anything) | Preserve original evidence and measurement/reconstruction/matched-camera comparisons. | Its room-to-Three.js workflow differs from object print preparation. |
| [Scaniverse support](https://scaniverse.com/support) | Content-based import must distinguish actual mesh faces from splats. | On review the supplied URL redirected to [Niantic Spatial Capture](https://www.nianticspatial.com/products/capture). Current mobile export details are not established by that redirect; verify with real files in #9/#24. |
| [KIRI features](https://www.kiriengine.app/features) | Optional future comparison for difficult objects and mesh-inclusive 3DGS exports. | Product page reports those capabilities; real metric accuracy and export topology require benchmarks. No cloud adapter in the main plan. |
| [Qlone FAQ](https://www.qlone.pro/faq) | Guided coverage, printed mats and multiple-angle/underside capture inform later capture guidance. | FAQ describes both mat and matless modes. No device or measurement test here. |
| [Sculpt](https://sculptor.uptrail.ai/) | Approachable scan-to-print review with size, repairs and warnings. | Product descriptions, not verified repair/accuracy evidence. |
| [Meshroom](https://meshroom.org/) | Cached intermediates and invalidating only affected downstream nodes inform R. | Its documented dependency behavior is an architectural reference, not a requirement to adopt Meshroom. |

## Bounded spikes and go/no-go outputs

1. **#14 exporter:** one compatibility/round-trip/provenance prototype on target ARM64 plus supported development platforms; choose and document an exporter. Failed compatibility can justify a small core writer, with mandatory independent validation.
2. **#29 Bambu project:** one pinned Mac CLI project and reopen/slice experiment with exact settings; verify geometry retention and current MakerWorld file acceptance separately. Unsupported unattended behavior leaves a clearly manual handoff, not a fabricated project format.
3. **MW platform:** read current official guides and authenticated UI, establish supported transfer/auth options, then recommend kit/companion/API or no-go. Future draft/public/update tests require explicit authorization and are distinct certification steps. No MakerWorld writes in this task.
4. **#23 Apple reconstruction:** verify current requirements/APIs and scale evidence, then compare real measured objects with retained photos. Synthetic results stay labelled. Mac path ships without CPU fallback.
5. **#21 and #22 capacity:** measure the mesh path first on the actual VPS; later make an independent CPU-photo go/no-go decision. Limit guesses in old issues are hypotheses.
6. **#28 and #27 later:** appearance/AMS interoperability and functional STEP/CAD gates each require a small demonstrated example before broader UI work.
