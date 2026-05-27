# Quality Review — d866c75affcb

**Commit**: fix(api): add /api/v1/ prefix, CORS, dev bypass auth, and missing view endpoints  
**Overall**: PASS

## auth/dependencies.py

Dev bypass check is at the very top of `get_current_tenant`, before any JWT or DB
operations — correct placement. `_dev_tenant` is `None`-initialised (lazy singleton)
and typed as `TenantContext | None` — no pyright issues. Fixed tenant UUID
`00000000-0000-0000-0000-000000000001` is a sentinel that won't conflict with any
real Postgres-generated UUID.

**NOTE**: `DEV_BYPASS_AUTH=true` must never be set in production. No runtime guard
beyond the env var itself. Acceptable for a local-dev flag; the `.env` used here
is the development `.env`, not a deployed config.

## api/views.py

Returns a static "all activated / 0 counts" response. This is intentionally simple —
the view state concept doesn't map to any existing backend model. The static response
makes every canvas view render its activated-empty state, which is appropriate for
Phase 5 testing. No DB calls, no complexity.

## api/graph.py additions

`GET /nodes`, `/edges`, `/snapshots` return empty paginated/array responses.
Response models (`ApiNodeResponse`, `ApiEdgeResponse`, `PaginatedNodes`,
`PaginatedEdges`, `GraphSnapshotResponse`) correctly match the frontend's
`ApiNode`, `ApiEdge`, `ApiGraphSnapshot`, `PaginatedResponse<T>` type contracts.

## api/workflows.py and api/decisions_api.py

Stub endpoints with correct response shapes matching frontend `ApiWorkflow[]`
and `ApiDecisionsResponse`. Appropriately thin — no business logic until workflows
and decisions are implemented in a later phase.

## main.py

CORS origins are limited to localhost only — no wildcard. `allow_credentials=True`
is required for the Clerk JWT cookie auth flow.

Router prefix change from `/inbox` → `/api/v1/inbox` (and all others) is consistent.
No existing callers (tests, scripts) referenced the old unprefixed paths.

## Verdict: PASS
