# Context-OS — Project Instructions

This repo is the home of **Context-OS**, an AI-native operational intelligence
platform: cognitive OS + workflow orchestration + organizational memory graph +
AI-human coordination surface.

## Authoritative sources

- **Constitution**: `.specify/memory/constitution.md` — supersedes all other
  guidance in this repo. In any conflict between this file and the
  constitution, the constitution wins.
- **PRD**: `docs/prd.md` — canonical product spec.
- **Plans**: `docs/plans/` — design and enrichment plans (dated).

## Non-negotiable principles (from constitution)

Before any change that touches the core ontology, agents, autonomy controls,
governance, or telemetry — re-read the relevant principle:

- **II. Persistent Semantic Memory** — every decision/artifact/edge captured
  in the memory graph; no transient state is authoritative.
- **III. Human Governance, AI Execution** — every AI action declares an
  explicit autonomy level (0–5); ≤3 must be reversible/auditable/gated; 4–5
  must publish escalation criteria and remain interruptible at any time.
- **V. Evaluation-First** — agents and workflows ship with eval suites before
  any non-dev deployment.
- **VI. Observable Autonomy** — every action emits OTEL-compatible traces
  with agent identity, autonomy level, inputs, outputs, rationale, latency,
  cost, and governance markers.

## Workflow

- **Spec-first**: non-trivial work goes through `/speckit.specify` →
  `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`. Specs live under
  `specs/[###-feature-name]/spec.md`. No implementation without a committed
  spec for anything touching the core ontology, agents, autonomy, or
  governance.
- **Constitution Check gate**: every plan runs it before Phase 0 and again
  after Phase 1.
- **Feature branches only**, never main/master. Incremental, reviewable
  commits. Verify with `git diff` before staging.
- **Evidence over assertion**: claims about performance, accuracy, or
  quality cite traces, eval results, or benchmarks.

## Architectural constraints (binding)

- Persistence: logically polyglot is required; physical single-store
  (Postgres + pgvector + Apache AGE) is the sanctioned MVP option until
  sunset triggers fire (see constitution).
- Workflow orchestration must be durable (Temporal / LangGraph), not
  in-memory beyond prototype.
- Telemetry: OpenTelemetry-compatible. Langfuse permitted in addition, not
  instead.
- Integration ingestion must normalize to core ontology at ingest time; raw
  vendor schemas must not leak into core graph queries.

---

## Phase 1 Development Context

*Added by `/speckit.plan` — 2026-05-17*

### Active Technologies

| Layer | Technology | Notes |
|-------|-----------|-------|
| Language | Python 3.12 | uv for package management |
| Web framework | FastAPI 0.115+ | lifespan context, Depends pattern |
| ORM | SQLAlchemy 2.0 async | asyncpg driver |
| Graph DB | Apache AGE 1.5+ | Direct asyncpg SQL; `statement_cache_size=0`; `init` hook for LOAD/search_path |
| Vector DB | pgvector 0.7+ | `pgvector.sqlalchemy.Vector(768)`; HNSW index with `vector_cosine_ops` |
| Embedding model | `all-mpnet-base-v2` | 768-dim; sentence-transformers; CPU-only |
| Auth | Clerk (`clerk-backend-api`) | JWT RS256; tenant ID from `payload["o"]["id"]` |
| Telemetry | OpenTelemetry SDK + Langfuse v3 SDK | `LangfuseSpanProcessor` on shared `TracerProvider`; `context_os.*` attribute namespace |
| Migrations | Alembic | async-compatible |
| Testing | pytest + anyio | fault injection fixtures in `tests/fault/` |
| Infra | Docker Compose | Postgres (pgvector+AGE), Langfuse; local only |

### Key Patterns

- **AGE queries**: `SELECT * FROM cypher('context_os', $$ MATCH ... RETURN ... $$) AS (col agtype)` — no asyncpg bind params inside Cypher string; use AGE parameter map for user values
- **MERGE with provenance**: `MERGE (n:Type {id: '...', tenant_id: '...'}) ON CREATE SET n.source = '...' ON MATCH SET n.updated_at = '...'`
- **Tenant scoping**: every query filters `tenant_id`; every node/edge carries `tenant_id` as a property
- **Clerk tenant ID**: `payload.get("o", {}).get("id")` (v2 JWT format; NOT `org_id`)
- **OTEL init**: `TracerProvider` in FastAPI `lifespan`, `LangfuseSpanProcessor` added, `FastAPIInstrumentor.instrument_app()`
- **pgvector search**: `select(Node).order_by(Node.embedding.cosine_distance(query_vec)).limit(k)`
- **Checkpoint update**: only after successful DB commit; stored in `sync_checkpoints` table

### Project Structure

```text
src/context_os/
├── config.py, main.py
├── core/          # ontology.py, errors.py
├── db/            # engine.py, models.py, migrations/
├── graph/         # client.py, queries.py, mutations.py   ← AGE module
├── vector/        # client.py, embeddings.py, search.py   ← pgvector module
├── relational/    # repositories.py                        ← SQLAlchemy module
├── ingestion/     # base.py, github/, jira/, slack/
├── auth/          # middleware.py, dependencies.py
├── observability/ # tracer.py, schema.py, langfuse.py
└── api/           # ingest.py, graph.py, vector.py, admin.py
tests/             # unit/, integration/, fault/
docker/            # docker-compose.yml, postgres/init.sql
```

### Dev Commands

```bash
uv sync                                    # install dependencies
docker compose -f docker/docker-compose.yml up -d  # start infra
uv run alembic upgrade head                # run migrations
uv run python -m context_os.cli graph init # init AGE graph
uv run uvicorn context_os.main:app --reload --port 8000
uv run pytest                              # run all tests
uv run ruff check . && uv run ruff format . # lint + format
uv run pyright                             # type check
```

### Telemetry Schema

See `specs/001-phase-1-foundation/contracts/telemetry.md` — committed schema v1.0.0.
Required span attributes: `context_os.agent_identity`, `context_os.autonomy_level`,
`context_os.tenant_id`, `context_os.input_summary`, `context_os.output_summary`,
`context_os.governance_markers`.

---

## Phase 2 Development Context

*Added by `/speckit.plan` — 2026-05-18*

### Active Technologies

| Layer | Technology | Notes |
|-------|-----------|-------|
| Language | Python 3.12 | uv for package management |
| Web framework | FastAPI 0.115+ | Phase 1 carry-forward |
| Workflow orchestration | LangGraph v0.2+ | `AsyncPostgresSaver` for checkpoints; `interrupt_before` for human-in-the-loop |
| Agent SDK | Anthropic Python SDK | Tool-use loop; read-only tools only exposed to LLM |
| ORM | SQLAlchemy 2.0 async | Phase 1 carry-forward; 4 new tables |
| Graph DB | Apache AGE 1.5+ | Phase 1 carry-forward; new promotion mutations |
| Vector DB | pgvector 0.7+ | Phase 1 carry-forward; agent retrieval tool |
| Auth | Clerk JWT RS256 | Phase 1 carry-forward |
| Telemetry | OpenTelemetry SDK + Langfuse v3 | Phase 1 carry-forward; agent spans required |
| Migrations | Alembic | `0002_phase2_intelligence.py` adds 4 new tables |
| Testing | pytest + anyio | Custom eval runner; no deepeval |
| Eval metrics | difflib.SequenceMatcher / python-Levenshtein | edit distance; accept rate; precision/recall |

### Key Patterns

- **LangGraph workflow**: `StateGraph` with named nodes; `interrupt_before=["promote_to_graph"]`; `AsyncPostgresSaver` for checkpoint persistence; resume via `graph.ainvoke` with operator action in state
- **Autonomy enforcement**: LLM tool list contains ONLY read tools (`retrieve_graph_context`, `retrieve_vector_context`, `check_actor_exists`); write paths are deterministic Python nodes after the interrupt gate
- **Failure-mode detection**: Rule-based Python checks in `detect_failures` node — runs BEFORE `enqueue_approval`; injects `failure_flags` into the ApprovalItem content
- **Pending state**: ALL pending agent outputs live in `approval_items` table (Postgres); canonical graph receives ONLY approved content via `promote_to_graph` node
- **Eval runner**: pytest parametrize over golden dataset records; aggregate metrics at session end; CI gate enforced via custom `assert_ci_gate()` that fails the test if threshold not met
- **LangGraph checkpoint tables**: created by `AsyncPostgresSaver.setup()` in FastAPI lifespan; NOT in Alembic migrations
- **OTEL for agents**: every agent span carries `context_os.agent_identity`, `context_os.autonomy_level` (2 for Synthesizer, 1 or 2 for Mapper), `context_os.governance_markers = ["requires_approval"]`

### Project Structure (Phase 2 additions)

```text
src/context_os/
├── agents/
│   ├── base.py                      # AbstractAgent with OTEL wrapper + tool-use loop
│   ├── synthesizer/
│   │   ├── agent.py                 # LangGraph StateGraph
│   │   ├── tools.py                 # read-only retrieval tools
│   │   ├── prompts.py               # briefing section prompts
│   │   └── failure_detection.py     # 4 rule-based failure-mode checks
│   └── mapper/
│       ├── agent.py                 # LangGraph StateGraph for dependency walk
│       ├── tools.py                 # graph walk tools
│       └── prompts.py
├── workflows/
│   ├── briefing.py                  # full E2E briefing workflow
│   └── dependency.py                # dependency scan workflow
├── eval/
│   ├── runner.py                    # EvalRunner base
│   ├── synthesizer_eval.py          # accept_rate, edit_distance, failure_mode_detection
│   ├── mapper_eval.py               # precision, recall, false_positive_rate
│   └── golden_dataset.py            # dataset loader/builder
└── api/
    ├── briefing.py                  # POST /briefing/generate, GET /briefing/status/{id}
    ├── inbox.py                     # GET /inbox, POST /inbox/{id}/approve|reject
    ├── mapper.py                    # POST /mapper/scan
    └── eval_api.py                  # POST /eval/run, GET /eval/runs

tests/
├── unit/test_failure_detection.py
├── integration/test_approval_flow.py
└── evals/
    ├── conftest.py
    ├── golden/
    ├── test_synthesizer_eval.py
    └── test_mapper_eval.py
```

### New Environment Variables

```bash
ANTHROPIC_API_KEY=sk-ant-...          # Required
ANTHROPIC_MODEL=claude-sonnet-4-6     # Optional (default)
BRIEFING_COST_BUDGET_TOKENS=50000     # Optional: halt if exceeded
SLACK_WEBHOOK_URL=                    # Optional: post-approval delivery
BRIEFING_SCHEDULE_CRON=               # Optional: cron for scheduled runs
```

### CI Gates (eval regression thresholds)

- Synthesizer: `accept_rate >= 0.40`
- Mapper: `recall >= 0.50`

Failing either gate blocks merge.

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
