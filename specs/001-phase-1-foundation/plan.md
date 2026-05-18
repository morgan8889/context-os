# Implementation Plan: Phase 1 — Foundation

**Branch**: `1-phase-1-foundation` | **Date**: 2026-05-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-phase-1-foundation/spec.md`

**Note**: This plan is produced by `/speckit.plan`. Tasks are generated separately by `/speckit.tasks`.

---

## Summary

Build the memory graph, ingestion pipeline (Jira + GitHub + Slack), multi-tenant auth, and
observability scaffold for Context-OS Phase 1. All components run locally via Docker Compose.
The exit criterion is a full three-source ingest visible in the admin UI with observable traces
in Langfuse — proving the persistence interfaces, normalization layer, tenant isolation, and
telemetry substrate before Phase 2 agents depend on them.

---

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI 0.115+, SQLAlchemy 2.0 (async), asyncpg, apache-age (Python
client), pgvector, Clerk SDK, Langfuse Python SDK, opentelemetry-sdk, opentelemetry-exporter-otlp,
httpx (OAuth flows), Pydantic v2, Alembic (migrations), uv (package management)  
**Storage**: PostgreSQL 16 + pgvector 0.7+ + Apache AGE 1.5+ (single Docker image); three
logically separate access modules: `relational`, `graph`, `vector`  
**Testing**: pytest + anyio (async), pytest-httpx (mock external APIs), fault injection fixtures  
**Target Platform**: Linux (Docker Compose local); macOS dev host  
**Project Type**: Web service (FastAPI JSON API) + CLI ingest commands  
**Performance Goals**: Graph query p95 ≤ 500ms on representative local dataset (AGE sunset trigger
threshold); vector retrieval top-5 within 200ms; ingest full run < 15 min from OAuth token  
**Constraints**: Local deploy only; no cloud infra in Phase 1; Clerk in dev/test key mode; Langfuse
local Docker Compose only  
**Scale/Scope**: 2 stub tenants; single author org data; ≤ 3 ingestion sources; Phase 1 only

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

### Pre-design check (2026-05-17)

| Principle | Area Touched | Status | Notes |
|-----------|-------------|--------|-------|
| I. Intent Over Tasks | Core ontology primitives (Goal, Initiative, Signal, Artifact, Actor, Memory, Dependency) are Phase 1's data model | ✅ PASS | All ingested data normalizes to intent-graph types; no raw task records leak to queries |
| II. Persistent Semantic Memory | Every ingest node/edge persisted in graph with provenance; no transient state is authoritative | ✅ PASS | FR-002, FR-008 — source, source_id, fetch_ts, tenant_id on every node |
| III. Human Governance, AI Execution | No AI agents in Phase 1; Clerk auth gates all data access | ✅ PASS | Autonomy model declared N/A for Phase 1 (no agent actions) |
| IV. Visualization as Cognition | Admin UI is a read-only list view, not topology-first | ⚠️ EXCEPTION | A-006: explicitly minimal, no design polish; topology surface deferred to Phase 3 (Galaxy layer). Admin view is a secondary detail pane — acceptable per Spec out-of-scope |
| V. Evaluation-First | No AI agents shipped; ingest and query are deterministic pipelines | ✅ PASS | Fault-injection test suite for OAuth expiry + rate-limit satisfies SC-007; standard pytest coverage sufficient |
| VI. Observable Autonomy | Every ingest run, graph query, vector retrieval emits OTEL trace with governance markers | ✅ PASS | FR-014, FR-015, FR-016 — structured log schema committed at Phase 1 exit |
| VII. Domain-Adapter Extensibility | Core ontology remains domain-agnostic; Jira/GitHub/Slack normalization in adapter layer | ✅ PASS | FR-006: raw vendor schemas must not leak into core graph queries |

### Architectural Constraints Check

| Constraint | Status | Notes |
|------------|--------|-------|
| Logically polyglot persistence | ✅ PASS | FR-001: three separate module interfaces; physical single-store (Postgres + pgvector + AGE) is sanctioned MVP option |
| Workflow orchestration durable | ✅ PASS | Phase 1 ingest is CLI-invoked batch (not a long-running agent workflow); checkpoint-based incremental sync satisfies durability for this phase; Temporal/LangGraph wired in Phase 2 |
| Autonomy levels 0–5 only | ✅ PASS | No agents in Phase 1 |
| OTEL-compatible telemetry | ✅ PASS | FR-014: OTEL traces; Langfuse additional layer |
| Integration normalization at ingest | ✅ PASS | FR-006: normalization to core ontology before persistence |

**Gate result**: ✅ PASS — One justified exception (Principle IV) documented. Plan may proceed to Phase 0.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-phase-1-foundation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── api.yaml         # OpenAPI 3.1 spec
│   └── telemetry.md     # Structured log schema
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/context_os/
├── __init__.py
├── config.py                    # Settings (Pydantic BaseSettings, env vars)
├── main.py                      # FastAPI app factory
│
├── core/                        # Domain models + shared types
│   ├── ontology.py              # NodeType, EdgeType enums; Pydantic node schemas
│   └── errors.py                # Structured error types
│
├── db/                          # Database lifecycle
│   ├── engine.py                # SQLAlchemy async engine + session factory
│   ├── migrations/              # Alembic migration scripts
│   └── models.py                # SQLAlchemy ORM (tenant table, ingest_checkpoints)
│
├── graph/                       # Graph module interface (AGE / Cypher)
│   ├── __init__.py
│   ├── client.py                # AGE connection wrapper
│   ├── queries.py               # 1-hop, k-hop, edge-filtered traversal
│   └── mutations.py             # Node / edge upsert with provenance
│
├── vector/                      # Vector module interface (pgvector)
│   ├── __init__.py
│   ├── client.py                # pgvector-aware session helper
│   ├── embeddings.py            # Embedding model wrapper (sentence-transformers)
│   └── search.py                # Top-k semantic retrieval
│
├── relational/                  # Relational module interface (SQLAlchemy)
│   ├── __init__.py
│   └── repositories.py          # Tenant CRUD, ingest checkpoint CRUD
│
├── ingestion/                   # Source adapters
│   ├── base.py                  # Abstract IngestAdapter (OAuth, checkpoint, normalize)
│   ├── github/
│   │   ├── client.py            # GitHub REST/GraphQL OAuth client
│   │   └── normalizer.py        # → Goal/Initiative/Signal/Artifact/Actor
│   ├── jira/
│   │   ├── client.py
│   │   └── normalizer.py        # → Goal/Initiative/Signal/Artifact/Actor
│   └── slack/
│       ├── client.py
│       └── normalizer.py        # → Signal/Actor + pending cross-source edges
│
├── auth/                        # Clerk integration
│   ├── middleware.py            # JWT verification; tenant scoping
│   └── dependencies.py          # FastAPI dependency: current_tenant
│
├── observability/               # OTEL + Langfuse wiring
│   ├── __init__.py
│   ├── tracer.py                # TracerProvider setup; span helpers
│   ├── schema.py                # Committed structured-log schema (v1)
│   └── langfuse.py              # Langfuse callback integration
│
└── api/                         # FastAPI routers
    ├── ingest.py                # POST /ingest/{source}
    ├── graph.py                 # GET /graph/traverse, /graph/query
    ├── vector.py                # GET /vector/search
    └── admin.py                 # GET /admin/entities (list view)

tests/
├── conftest.py                  # DB fixtures, tenant fixtures, mock OAuth
├── unit/
│   ├── test_normalizers.py      # Per-source normalization unit tests
│   ├── test_graph_queries.py    # AGE query correctness
│   └── test_vector_search.py   # pgvector retrieval correctness
├── integration/
│   ├── test_ingest_github.py    # End-to-end GitHub ingest (real or cassette)
│   ├── test_ingest_jira.py
│   ├── test_ingest_slack.py
│   ├── test_tenant_isolation.py # Cross-tenant zero-visibility check
│   └── test_observability.py   # Trace emission verification
└── fault/
    ├── test_oauth_expiry.py     # Inject 401 mid-ingest; verify checkpoint + error
    └── test_rate_limit.py       # Inject 429; verify backoff + resume

docker/
├── docker-compose.yml           # postgres (pgvector + AGE), langfuse, app
└── postgres/
    └── init.sql                 # Enable extensions: pgvector, age

scripts/
└── ingest.py                    # CLI entry point: python -m context_os.cli ingest [source]
```

**Structure Decision**: Single Python project layout under `src/context_os/`. Module boundaries
mirror the three logical persistence roles (graph, vector, relational) and the ingestion adapter
pattern. No monorepo split needed at Phase 1 scale.

---

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Admin UI as list view (Principle IV exception) | Phase 1 exit criterion requires author to verify normalization without DB access; no topology data to visualize yet | Topology surface requires Phase 2 agent data to be meaningful; building it now would be speculative and violate YAGNI |

---

## Phase 0: Research Findings

*Populated from research agents — see [research.md](research.md)*

---

## Phase 1: Design Artifacts

*Populated after Phase 0 — see [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)*

---

## Post-design Constitution Check

*Re-run after Phase 1 artifacts complete — 2026-05-17*

| Principle | Design Decision | Status |
|-----------|----------------|--------|
| I. Intent Over Tasks | Core ontology (Goal/Initiative/Signal/Artifact/Actor/Memory) is the primary schema; source data normalized to these types at ingest | ✅ PASS |
| II. Persistent Semantic Memory | Every node/edge written to AGE graph with provenance (source, source_id, fetch_ts, tenant_id); checkpoint-based recovery; no transient-only state | ✅ PASS |
| III. Human Governance, AI Execution | No AI agents in Phase 1; autonomy_level=2 (supervised automation) declared for ingest operations; all actions reversible | ✅ PASS |
| IV. Visualization as Cognition | Admin UI is a list view (exception justified); topology surface deferred to Phase 3 | ✅ JUSTIFIED EXCEPTION |
| V. Evaluation-First | No agents to evaluate; fault-injection test suite (tests/fault/) covers OAuth expiry + rate-limit per SC-007 | ✅ PASS |
| VI. Observable Autonomy | OTEL `TracerProvider` + `LangfuseSpanProcessor`; `context_os.*` attribute namespace; telemetry schema committed (contracts/telemetry.md) | ✅ PASS |
| VII. Domain-Adapter Extensibility | Source normalizers in `ingestion/{github,jira,slack}/normalizer.py` — adapter layer; core ontology remains domain-agnostic | ✅ PASS |

**Post-design gate result**: ✅ PASS — No new violations introduced by design decisions. Plan is complete and ready for `/speckit.tasks`.
