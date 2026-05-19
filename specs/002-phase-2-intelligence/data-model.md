# Data Model: Phase 2 — Intelligence

**Feature**: 002-phase-2-intelligence  
**Date**: 2026-05-18  
**Depends on**: Phase 1 Foundation schema (node_embeddings, sync_checkpoints, oauth_tokens, tenants)

---

## Overview

Phase 2 adds four new relational tables and extends the canonical memory graph with
two new node types and one new edge type. Pending agent outputs live exclusively in
the relational layer until operator approval; only approved outputs are promoted to
the canonical graph.

---

## New Relational Tables

### `approval_items`

Stores all pending, approved, and rejected agent-generated outputs. The single table
accommodates heterogeneous item types via the `item_type` discriminator and a JSONB
`content` column.

```sql
CREATE TABLE approval_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       TEXT NOT NULL,
    item_type       TEXT NOT NULL,   -- 'briefing_draft' | 'proposed_dependency' | 'proposed_risk'
    status          TEXT NOT NULL DEFAULT 'pending',  -- 'pending' | 'approved' | 'rejected'
    content         JSONB NOT NULL,  -- item-type-specific payload (see schemas below)
    failure_flags   JSONB,           -- list of {type, detail} detected failure modes
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    operator_id     TEXT,            -- Clerk user ID of the operator who acted
    acted_at        TIMESTAMPTZ,     -- timestamp of approve/reject action
    rejection_reason TEXT,           -- operator-supplied reason when rejecting
    edit_delta      JSONB,           -- {original_tokens, final_tokens, changed_sections[]}
    stale_notified_at TIMESTAMPTZ,   -- when stale notification was sent (if any)
    run_id          UUID,            -- FK to briefing_runs.id (for briefing_draft items)
    graph_node_id   UUID,            -- populated after approve → graph promotion
    workflow_thread_id TEXT          -- LangGraph thread ID for interrupt/resume
);

CREATE INDEX ix_approval_items_tenant_status ON approval_items (tenant_id, status);
CREATE INDEX ix_approval_items_tenant_created ON approval_items (tenant_id, created_at DESC);
CREATE INDEX ix_approval_items_run_id ON approval_items (run_id) WHERE run_id IS NOT NULL;
```

**State transitions**:
```
pending ──approve──▶ approved
pending ──reject───▶ rejected
```
Approved and rejected items are never deleted — they form a provenance log.  
Rejected items: `graph_node_id` remains NULL; `edit_delta` remains NULL.  
Approved items: `graph_node_id` is set to the created graph node UUID (for
BriefingDraft → Artifact promotion; NULL for edge-only items like ProposedDependency).

**JSONB content schemas by item_type**:

`briefing_draft`:
```json
{
  "window_days": 7,
  "window_start": "ISO-8601",
  "window_end": "ISO-8601",
  "sections": {
    "progress": [{"text": "...", "source_ids": ["uuid", ...]}],
    "risks": [{"text": "...", "severity": "high|medium|low", "source_ids": [...]}],
    "decisions": [{"text": "...", "source_ids": [...]}],
    "dependencies": [{"text": "...", "source_ids": [...]}],
    "escalations": [{"text": "...", "source_ids": [...]}]
  },
  "low_signal": false,
  "data_stale": false,
  "signal_counts": {"github": 12, "jira": 8, "slack": 5}
}
```

`proposed_dependency`:
```json
{
  "from_node_id": "uuid",
  "from_node_type": "Initiative",
  "to_node_id": "uuid",
  "to_node_type": "Initiative",
  "dependency_type": "DEPENDS_ON",
  "evidence": [{"source_id": "uuid", "source_type": "Signal", "excerpt": "..."}],
  "confidence": 0.82
}
```

`proposed_risk`:
```json
{
  "description": "...",
  "severity": "high|medium|low",
  "source_ids": ["uuid", ...],
  "rationale": "...",
  "related_node_id": "uuid"
}
```

---

### `briefing_runs`

Tracks each briefing generation attempt, including status, cost, and input signal counts.
One `briefing_run` produces one `approval_items` row of type `briefing_draft`.

```sql
CREATE TABLE briefing_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       TEXT NOT NULL,
    trigger_type    TEXT NOT NULL,  -- 'manual' | 'scheduled'
    window_days     INTEGER NOT NULL DEFAULT 7,
    window_start    TIMESTAMPTZ NOT NULL,
    window_end      TIMESTAMPTZ NOT NULL,
    status          TEXT NOT NULL DEFAULT 'generating',
    -- 'generating' | 'complete' | 'failed' | 'partial'
    input_signal_counts JSONB,  -- {"github": N, "jira": N, "slack": N}
    retrieval_hit_rate  NUMERIC(4,3),  -- fraction of retrieval queries returning results
    cost_tokens     INTEGER,     -- total token count (prompt + completion)
    latency_ms      INTEGER,     -- ms from trigger to draft-ready
    error_detail    TEXT,        -- if status = failed
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at    TIMESTAMPTZ,
    approval_item_id UUID        -- FK to approval_items.id once draft is enqueued
);

CREATE INDEX ix_briefing_runs_tenant ON briefing_runs (tenant_id, created_at DESC);
```

**Status transitions**:
```
generating ──success──▶ complete
generating ──error─────▶ failed
generating ──budget hit─▶ partial (draft discarded; operator notified)
```

---

### `eval_runs`

Stores the result of each evaluation suite execution. Both agents share this table,
discriminated by `eval_type`.

```sql
CREATE TABLE eval_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       TEXT NOT NULL,
    eval_type       TEXT NOT NULL,  -- 'synthesizer' | 'mapper'
    dataset_id      UUID NOT NULL,  -- FK to golden_datasets.id
    dataset_version TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'running',  -- 'running' | 'passed' | 'failed' | 'error'
    scores          JSONB NOT NULL DEFAULT '{}',
    -- synthesizer: {accept_rate, median_edit_distance, false_positive_risk_rate,
    --               failure_mode_detection: {hallucinated_stakeholder, stale_dependency,
    --                                        missed_escalation, citation_error}}
    -- mapper: {precision, recall, false_positive_rate}
    gates_passed    BOOLEAN,        -- true if all CI gates cleared
    compared_to_run_id UUID,        -- FK to eval_runs.id for delta computation
    score_deltas    JSONB,          -- delta vs compared_to_run_id scores
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at    TIMESTAMPTZ,
    duration_ms     INTEGER,
    error_detail    TEXT
);

CREATE INDEX ix_eval_runs_tenant_type ON eval_runs (tenant_id, eval_type, created_at DESC);
```

**CI gate thresholds** (enforced in eval runner, readable from here for dashboards):
- synthesizer: `scores.accept_rate >= 0.40`
- mapper: `scores.recall >= 0.50`

---

### `golden_datasets`

Versioned reference datasets used as ground truth for eval suites.

```sql
CREATE TABLE golden_datasets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       TEXT NOT NULL,
    dataset_type    TEXT NOT NULL,  -- 'synthesizer' | 'mapper'
    version         TEXT NOT NULL,  -- semantic version string, e.g. "1.0.0"
    description     TEXT,
    record_count    INTEGER NOT NULL,
    content         JSONB NOT NULL,
    -- synthesizer: [{window_start, window_end, approved_content, accepted_as_is: bool,
    --                edit_delta, failure_mode_injections: [{type, injected_at, expected_flag}]}]
    -- mapper: [{from_node_id, to_node_id, ground_truth_exists: bool, evidence_signals: [...]}]
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    built_from_approval_items JSONB,  -- list of approval_item UUIDs used to build this dataset
    UNIQUE (tenant_id, dataset_type, version)
);
```

---

## Extended Memory Graph (Apache AGE)

Phase 2 adds two new node types and one new edge type to the canonical graph.
These are written only when an operator approves a corresponding `approval_items` row.

### New Node Type: `BriefingArtifact`

Maps to the existing `Artifact` node type (no new AGE node label; `Artifact.subtype =
'briefing'` distinguishes it). Properties:

| Property | Type | Description |
|---|---|---|
| `id` | UUID | Canonical node ID |
| `tenant_id` | TEXT | Tenant scope |
| `subtype` | TEXT | Always `'briefing'` |
| `title` | TEXT | e.g., "Weekly Briefing 2026-05-11–2026-05-18" |
| `content` | TEXT | Final approved Markdown (post operator edits) |
| `window_start` | TIMESTAMPTZ | Briefing data window start |
| `window_end` | TIMESTAMPTZ | Briefing data window end |
| `approval_item_id` | UUID | FK back to `approval_items.id` |
| `operator_id` | TEXT | Clerk ID of approving operator |
| `approved_at` | TIMESTAMPTZ | Approval timestamp |
| `source` | TEXT | Always `'internal'` |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### New Node Type: `Risk`

A confirmed Risk entry proposed by the Synthesizer and approved by the operator.

| Property | Type | Description |
|---|---|---|
| `id` | UUID | Canonical node ID |
| `tenant_id` | TEXT | Tenant scope |
| `description` | TEXT | Risk description |
| `severity` | TEXT | `'high'` \| `'medium'` \| `'low'` |
| `status` | TEXT | `'open'` \| `'mitigated'` \| `'dismissed'` |
| `source` | TEXT | Always `'internal'` |
| `approval_item_id` | UUID | FK to `approval_items.id` |
| `operator_id` | TEXT | Clerk ID of approving operator |
| `approved_at` | TIMESTAMPTZ | |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### New Edge Type: `DEPENDS_ON` (promoted from proposed)

The `DEPENDS_ON` edge type may already exist in Phase 1 for manually asserted
dependencies. Phase 2 adds agent-proposed `DEPENDS_ON` edges promoted via the approval
inbox. Promoted edges carry additional provenance properties:

| Property | Type | Description |
|---|---|---|
| `mapper_confidence` | NUMERIC | Dependency Mapper's confidence score |
| `evidence_item_ids` | TEXT[] | Source node IDs cited as evidence |
| `approval_item_id` | UUID | FK to `approval_items.id` |
| `operator_id` | TEXT | Approving operator |
| `approved_at` | TIMESTAMPTZ | |

The Dependency Mapper NEVER creates `DEPENDS_ON` edges directly. The write happens in
the deterministic graph promotion step after operator approval.

---

## LangGraph Checkpoint Tables

Managed by the `langgraph-checkpoint-postgres` library via `AsyncPostgresSaver.setup()`
called in the FastAPI lifespan. The library creates:
- `checkpoints` — workflow state snapshots
- `checkpoint_blobs` — binary state blobs
- `checkpoint_writes` — pending write records

These tables are NOT in Alembic migrations. They are implementation details of the
orchestrator. Application code references them only indirectly via the LangGraph SDK.

---

## Schema Relationships

```
tenants
  ├── oauth_tokens (phase 1)
  ├── sync_checkpoints (phase 1)
  ├── node_embeddings (phase 1)
  ├── approval_items ──run_id──▶ briefing_runs
  │       │
  │       └──graph_node_id──▶ [AGE graph: Artifact(briefing) | Risk node]
  ├── briefing_runs ──approval_item_id──▶ approval_items
  ├── eval_runs ──dataset_id──▶ golden_datasets
  └── golden_datasets

AGE graph (canonical, approved state only)
  ├── Goal / Initiative / Signal / Artifact / Actor / Memory (phase 1)
  ├── Artifact {subtype: 'briefing'} (phase 2, approved briefings)
  ├── Risk (phase 2, approved risks)
  └── DEPENDS_ON edges (phase 2, mapper-proposed + operator-approved)
```

---

## Migration Notes

- All four new tables are created in a single Alembic migration: `0002_phase2_intelligence.py`
- The migration runs after `0001_initial_schema.py` (Phase 1 migration)
- No existing Phase 1 tables are modified
- AGE graph schema is schema-flexible (no migration required for new node types or
  edge properties; AGE is property-graph, not fixed-schema)
