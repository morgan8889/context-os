# Spec Review — 4dec84ca3889

**Commit:** fix(graph): replace ON CREATE/MATCH SET with plain SET for PG18 compatibility
**Files:** `src/context_os/graph/client.py`, `src/context_os/graph/mutations.py`
**Overall:** PASS

## PostgreSQL 18 / AGE 1.7 Compatibility

PostgreSQL 18.4 parses `MERGE...ON` as native MERGE DML even inside dollar-quoted string
literals. AGE's Cypher `MERGE...ON CREATE SET` / `ON MATCH SET` syntax triggers this parser
conflict. Plain `SET` (unconditional, applies on both create and match) is valid OpenCypher
and avoids the conflict.

All Cypher mutation strings in `mutations.py` now use `MERGE (...) SET props RETURN`.
The `client.py` comment documents the constraint. No spec violation: the graph write path
still guarantees upsert semantics (MERGE identity keys remain `{id, tenant_id}`).
