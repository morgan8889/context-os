# Telemetry Contract: Structured Log Schema v1

**Date**: 2026-05-17  
**Version**: 1.0.0 (Phase 1 — Foundation)  
**Status**: Committed — do not break without a MINOR version bump

---

## Purpose

This schema is committed at Phase 1 exit so Phase 2 agents can emit telemetry without breaking
existing consumers. All application logs MUST conform to this schema. OTEL span attributes follow
the same field naming.

---

## Extension Contract

- Phase 2+ MAY add new top-level keys or add keys inside `metadata`
- Phase 2+ MUST NOT rename or change the type of any field marked **required**
- Log consumers MUST ignore unknown keys (tolerant reader pattern)
- Breaking changes require a MINOR version bump of this document

---

## JSON Log Schema (v1.0.0)

```jsonc
{
  // ── Core identity ─────────────────────────────────────────────────────────
  "timestamp":       "2026-05-17T12:00:00.000Z",  // ISO 8601 UTC        REQUIRED
  "level":           "INFO",                        // ERROR|WARN|INFO|DEBUG REQUIRED
  "service":         "context-os",                  // always this value   REQUIRED
  "version":         "0.1.0",                       // semver              REQUIRED

  // ── Trace correlation ─────────────────────────────────────────────────────
  "trace_id":        "4bf92f3577b34da6a3ce929d0e0e4736", // OTEL hex; null if no span REQUIRED
  "span_id":         "00f067aa0ba902b7",                 // OTEL hex; null if no span REQUIRED

  // ── Event identity ────────────────────────────────────────────────────────
  "event":           "ingest.run.completed",         // dot-namespaced verb REQUIRED
  "message":         "Ingest run completed for github", // human-readable  REQUIRED

  // ── Governance fields (constitution Principle VI) ─────────────────────────
  "agent_identity":  "ingest-agent-v1",              // string             REQUIRED
  "autonomy_level":  2,                              // int 0-5            REQUIRED
  "tenant_id":       "org_abc123",                   // Clerk org ID       REQUIRED

  // ── Timing ────────────────────────────────────────────────────────────────
  "duration_ms":     142,                            // operation duration  REQUIRED

  // ── Extension namespace ────────────────────────────────────────────────────
  "metadata":        {}                              // open object         REQUIRED (may be empty)
}
```

---

## OTEL Span Attributes (context_os.* namespace)

All application spans MUST carry the following attributes in addition to standard OTEL HTTP/DB
instrumentation:

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `context_os.agent_identity` | string | ✅ | Component or future agent name |
| `context_os.autonomy_level` | int | ✅ | 0–5 per constitution |
| `context_os.tenant_id` | string | ✅ | Clerk org ID |
| `context_os.input_summary` | string | ✅ | ≤256 chars describing the operation input |
| `context_os.output_summary` | string | ✅ | ≤256 chars describing the result |
| `context_os.governance_markers` | string (JSON) | ✅ | `{}` minimum; extend in Phase 2 |
| `gen_ai.system` | string | ✅ | `"context-os"` |
| `gen_ai.operation.name` | string | ✅ | `"ingest"` \| `"graph_traverse"` \| `"vector_search"` |

---

## Event Vocabulary (Phase 1)

| Event | Level | Description |
|-------|-------|-------------|
| `ingest.run.started` | INFO | Ingest job kicked off |
| `ingest.run.completed` | INFO | All pages fetched and committed |
| `ingest.run.checkpoint_saved` | INFO | Mid-run checkpoint persisted |
| `ingest.run.failed` | ERROR | Terminal failure; checkpoint may be saved |
| `ingest.source.rate_limited` | WARN | 429 received; backing off |
| `ingest.source.token_expired` | ERROR | OAuth token expired; halting |
| `graph.traverse.executed` | INFO | Graph traversal completed |
| `graph.traverse.error` | ERROR | AGE query failed |
| `vector.search.executed` | INFO | Top-k retrieval completed |
| `vector.search.error` | ERROR | pgvector query failed |
| `auth.request.rejected` | WARN | Unauthenticated or wrong tenant |

---

## `metadata` Field Examples (Phase 1)

```jsonc
// ingest.run.completed
"metadata": {
  "integration": "github",
  "records_fetched": 143,
  "nodes_created": 87,
  "nodes_updated": 56,
  "edges_created": 201,
  "checkpoint_cursor": "2026-05-17T11:45:00Z"
}

// graph.traverse.executed
"metadata": {
  "from_node_id": "a3f2...",
  "max_hops": 2,
  "edge_types": ["AUTHORED_BY", "PRODUCES"],
  "nodes_returned": 12,
  "edges_returned": 15
}

// vector.search.executed
"metadata": {
  "query_length": 42,
  "k": 5,
  "node_types": ["Artifact", "Memory"],
  "top_distance": 0.12,
  "results_returned": 5
}
```
