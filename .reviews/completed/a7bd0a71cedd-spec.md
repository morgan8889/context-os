# Spec Review — a7bd0a71cedd

**Commit:** fix(graph): pass AGE params as asyncpg bind parameter, not SQL literal
**File:** `src/context_os/graph/client.py` — `run_cypher`
**Overall:** PASS

AGE 1.5 requires the third argument to `cypher()` to be a PostgreSQL bind parameter
(`$1::agtype`), not a string literal. The fix switches to `$1::agtype` and passes the
JSON-serialized params dict as an asyncpg positional argument. Satisfies AGE's parse-time
parameter check via the Extended Query Protocol. Matches research.md contract: user values
via AGE parameter map, never f-string-interpolated. No spec violations.
