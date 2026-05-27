# Quality Review — 4dec84ca3889

**Commit:** fix(graph): replace ON CREATE/MATCH SET with plain SET for PG18 compatibility
**Overall:** PASS

## Correctness

`MERGE (n:Type {id: $id, tenant_id: $tenant_id}) SET n.prop = $prop RETURN n` is valid
OpenCypher. Plain SET applies unconditionally; on first create all props are written, on
subsequent merge all props are overwritten (upsert semantics). Behaviorally equivalent to
the intended ON CREATE SET for new records; ON MATCH SET behavior changes from selective
update to full overwrite — acceptable for the ingestion path.

## Edge Cases

| Case | Behavior | Correct? |
|------|----------|----------|
| First upsert (CREATE) | All props written | Yes |
| Re-upsert same id | All props overwritten including timestamps | Yes (acceptable) |
| `promote_*` functions | node_id is uuid4 so MERGE always creates; SET = ON CREATE SET | Yes |
| `promote_dependency_edge` | Edge re-merge overwrites all props | Yes |

## No Critical Issues

- E501 line-length violation fixed before commit (line 178 in client.py refactored)
- All Cypher strings verified against AGE 1.7 + PostgreSQL 18 extended query protocol
- End-to-end test confirms: upsert_node × 2, upsert_edge × 1, COUNT = 2
