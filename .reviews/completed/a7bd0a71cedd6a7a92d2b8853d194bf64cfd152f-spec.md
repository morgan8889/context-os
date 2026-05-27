# Spec Review — a7bd0a71cedd6a7a92d2b8853d194bf64cfd152f

**Commit:** fix(graph): pass AGE params as asyncpg bind parameter, not SQL literal
**File:** `src/context_os/graph/client.py` — `run_cypher`
**Overall:** PASS

## Root Cause Addressed

The prior code embedded the serialized JSON directly into the SQL text as a string literal:
`f"... $$ {cypher} $$, '{params_json}'::agtype ..."`. AGE 1.5 validates at parse time
that the third argument to `cypher()` is a SQL parameter placeholder, not a literal
expression — error: `"third argument of cypher function must be a parameter"`.
This caused `seeded=0` on all seed endpoints and `_count_age_nodes` always returning 0.

## Fix Correctness — AGE 1.5

AGE documentation: "place a Postgres parameter as the third argument in the Cypher function
call." The fix uses `$1::agtype`. When `conn.fetch(query, params_json)` is called, asyncpg
uses the PostgreSQL Extended Query Protocol (Parse → Bind → Execute). AGE's check is satisfied
by `$1` at parse time; the JSON is transmitted at bind time. `statement_cache_size=0` (already
present) prevents asyncpg named-statement reuse but does not disable the extended protocol.

## Conformance to Research.md

| Contract | Status |
|---|---|
| `asyncpg.create_pool(statement_cache_size=0, init=_age_setup)` | Unchanged, correct |
| User values via AGE parameter map, never f-string-interpolated | NOW CORRECT — was broken before this commit |
| `SELECT * FROM cypher(graph_name, $$ ... $$[, $1::agtype]) AS (col agtype)` | Correct |

## Verdict: PASS
