# shared/api

Generated OpenAPI types and the typed fetch client live here. Never hand-write API types.
They are generated from the FastAPI OpenAPI schema (see the API issue, #16).

Regenerate with `pnpm gen:api` (writes `apps/web/openapi.json` and `schema.d.ts`). A Python test fails
if the committed `openapi.json` is stale.
