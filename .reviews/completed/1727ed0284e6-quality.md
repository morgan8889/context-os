# Code Quality Review — 1727ed0284e6

**Commit**: feat(phase6): seed endpoints, real AGE counts, /onboarding route
**Scope**: graph.py (seed + list endpoints), views.py (_count_age_nodes), router.tsx, OnboardingView.tsx

---

## [CRITICAL]

### C-1: Cypher label injection in _count_age_nodes (views.py:22)
`_count_age_nodes(tenant_id, node_type)` interpolates `node_type` directly into the
Cypher f-string: `f"MATCH (n:{node_type} {{tenant_id: $tenant_id}}) RETURN count(n) AS cnt"`
The function is currently called only with the literal string `"Initiative"`, so the
immediate risk is low — but the function signature accepts any caller-supplied string.
If a future caller passes a node_type derived from request input, this is a Cypher
injection vector. Every other mutation/query in this codebase uses the AGE param map
for user values or validates labels against an enum. This should do the same.

Fix: validate node_type against an allowlist (`ALLOWED_NODE_TYPES = {"Initiative",
"Goal", "Signal", "Artifact", ...}`) before interpolation, and raise ValueError if
not in the set.

### C-2: seed_nodes/seed_edges raise unhandled RuntimeError when AGE pool is absent (graph.py:481, 531)
`list_nodes` and `list_edges` catch `RuntimeError` from `get_age_pool()` and return
empty results gracefully. `seed_nodes` (line 481) and `seed_edges` (line 531) call
`get_age_pool()` with no try/except around it. If the pool is not initialised, FastAPI
propagates a 500 RuntimeError to the client rather than a 503/400 with a useful message.

Fix: wrap `get_age_pool()` in both seed handlers with `except RuntimeError` → raise
`HTTPException(status_code=503, detail="Graph store unavailable")`.

---

## [WARN]

### W-1: get_nodes_for_tenant called with node_type="Initiative" but returns node props keyed by AGE vertex structure (graph.py:373–395)
`get_nodes_for_tenant` returns `props = node_data.get("properties", node_data)` (mutations.py:615).
The AGE vertex dict structure after `_parse_agtype` is `{"id": ..., "label": ..., "properties": {...}}`.
`_props_to_api_node` then calls `props.get("id")` etc., which works correctly only if
the properties sub-dict contains a flat `id` field — which `upsert_node` does set. This
is correct, but fragile: if the AGE vertex is returned without a nested `properties` key
(possible in some AGE versions), `props` falls back to the raw vertex dict that has `id`
as the vertex internal ID (int64), not the app-level UUID string. The code would silently
produce wrong `id` values. Add an explicit assertion or log a warning when
`props.get("id")` is not a string.

### W-2: list_edges query only matches Initiative→Initiative edges (graph.py:484–495)
The Cypher query hard-codes `(s:Initiative {tenant_id:…})-[r]->(t:Initiative {tenant_id:…})`.
Demo data seeds edges from Signal, Artifact, and Goal nodes to Initiative nodes (e.g.
`demo-sig-1 → demo-proj-5`). Those edges will not appear in the GET /edges response
immediately after seeding because the source nodes have labels other than Initiative.
The frontend will see missing edges in the galaxy. The fix is to match unlabelled or
broader label patterns, consistent with the node model.

### W-3: edge_type label injection (graph.py:553)
`age_label = edge.edge_type.upper().replace("-", "_")` is interpolated into the Cypher
string `MERGE (a)-[r:{edge_type}]->(b)` inside `upsert_edge`. The `edge_type` field
comes from `SeedEdgeItem` (a Pydantic model), so it is a validated string, but there is
no allowlist check. A value like `DEPENDS_ON] RETURN 1; //` could break the Cypher
syntax. Add an allowlist for the seed endpoint edge types.

### W-4: Sequential node + edge seed with no transaction (graph.py:98–113 OnboardingView.tsx)
`handleLoadSampleData` fires `POST /nodes/seed` then `POST /edges/seed` sequentially.
If the edges request fails, nodes are partially seeded with no edges, and the galaxy
shows nodes without connections. The backend has no rollback. Consider returning a count
of partial success to the frontend, or documenting that partial seed is acceptable and
re-running seed is idempotent (which it is, given MERGE).

---

## [INFO]

### I-1: Cursor-based pagination uses integer offset strings (graph.py:360–368)
The cursor is `str(offset + limit)` (line 400). This is offset pagination renamed, not
a stable cursor. Concurrent writes between pages will cause rows to be skipped or
repeated. For the current demo use case (single user, small dataset) this is acceptable.
Worth a comment noting the limitation.

### I-2: setTimeout in React component (OnboardingView.tsx:98)
`setTimeout(() => navigate('/galaxy'), 600)` is not cancelled on unmount. If the user
navigates away in that 600ms window, `navigate` fires on an unmounted context (harmless
with React Router v6 but emits a console warning). Use `useEffect` cleanup or
`clearTimeout`.

### I-3: No rate-limiting on seed endpoints
`POST /nodes/seed` and `/edges/seed` are authenticated but have no rate limit or
idempotency key. A user could call them repeatedly, inflating the graph. Acceptable for
beta, but should be noted for GA.
