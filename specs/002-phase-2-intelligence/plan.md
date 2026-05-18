# Implementation Plan: Phase 2 — Intelligence

**Branch**: `2-phase-2-intelligence` | **Date**: 2026-05-18 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/002-phase-2-intelligence/spec.md`

---

## Summary

Phase 2 adds two AI agents (Operational Synthesizer at autonomy level 2, Dependency
Mapper at levels 1/2), a durable Executive Briefing workflow, a REST-based approval
inbox (human-in-the-loop governance gate), and eval suites for both agents — all built
on top of the Phase 1 Foundation graph, vector, and relational stores.

The Synthesizer reads from the memory graph and produces structured briefing drafts
pending operator approval. The Dependency Mapper walks the graph and proposes
`DEPENDS_ON` edges pending operator approval. No canonical graph mutations occur
without an explicit operator action on the approval inbox. Both agents ship with
evaluation suites that enforce CI regression gates before Phase 3 promotion.

---

## Technical Context

| Dimension | Value |
|---|---|
| Language / Version | Python 3.12 (same as Phase 1) |
| Package manager | uv |
| Web framework | FastAPI 0.115+ (Phase 1 carry-forward) |
| Workflow orchestration | LangGraph v0.2+ with `langgraph-checkpoint-postgres` |
| Agent SDK | Anthropic Python SDK (`anthropic`) — tool-use loop |
| ORM | SQLAlchemy 2.0 async (Phase 1 carry-forward) |
| Graph DB | Apache AGE 1.5+ via asyncpg (Phase 1 carry-forward) |
| Vector DB | pgvector 0.7+ (Phase 1 carry-forward) |
| Auth | Clerk JWT RS256 (Phase 1 carry-forward) |
| Telemetry | OpenTelemetry SDK + Langfuse v3 SDK (Phase 1 carry-forward) |
| Migrations | Alembic — new migration `0002_phase2_intelligence.py` |
| Testing | pytest + anyio; custom eval runner (no deepeval) |
| Target platform | localhost (Phase 2 only; cloud deployment Phase 3+) |
| Performance target | Briefing draft ready in < 5 minutes; inbox clearable in < 3 minutes |
| Constraints | Autonomy ≤ 3 → reversible/auditable/gated; all agent actions emit OTEL traces |

---

## Constitution Check

*GATE: evaluated before Phase 0 research, re-evaluated after Phase 1 design.*

| Principle | Status | Evidence |
|---|---|---|
| I. Intent Over Tasks | ✅ PASS | Briefing is generated from Goal/Initiative/Signal graph nodes. All briefing content traces to canonical intent primitives. No orphan task records. |
| II. Persistent Semantic Memory | ✅ PASS | All pending outputs stored in `approval_items` (Postgres). Approved items promoted to canonical AGE graph with provenance. Rejected items retained as provenance log. No transient state is authoritative. |
| III. Human Governance, AI Execution | ✅ PASS | Synthesizer at autonomy level 2: drafts, operator approves before any canonical graph write. Mapper at level 1 (briefing) / level 2 (portfolio scan): never writes canonical edges without approval gate. All autonomy levels declared explicitly in agent definitions. |
| IV. Visualization as Cognition | ⚠️ EXCEPTION | Approval inbox is a CRUD list+action surface (not topology-first). See Complexity Tracking justification below. |
| V. Evaluation-First | ✅ PASS | Eval suites (FR-021–FR-025) required for both agents. CI gates enforced. US4 is the eval story; agents cannot be promoted past development without evals passing. |
| VI. Observable Autonomy | ✅ PASS | FR-026–FR-028: every agent action emits OTEL-compatible traces with agent identity, autonomy level, inputs, outputs, latency, cost, governance markers. Operators can reconstruct any AI outcome from telemetry alone. |
| VII. Domain-Adapter Extensibility | ✅ PASS | BriefingDraft → `Artifact {subtype: 'briefing'}`, ProposedRisk → `Risk` node, ProposedDependency → `DEPENDS_ON` edge. All mapped to core ontology primitives. No core schema forks or hardcoded extensions. |
| Durable workflow | ✅ PASS | LangGraph v0.2+ with `AsyncPostgresSaver` (PostgreSQL checkpoints). Briefing workflow survives process restarts. Human-in-the-loop via `interrupt_before` mechanism. |
| Telemetry stack | ✅ PASS | OTEL primary (Phase 1 `TracerProvider` carry-forward). Langfuse permitted as supplementary (Phase 1 `LangfuseSpanProcessor` carry-forward). |
| Integration normalization | ✅ N/A | Phase 2 reads from the normalized graph; no new external integrations are added. |

**Post-Phase 1 design re-check**: All gates remain PASS. The data model (research.md,
data-model.md) confirms: pending state is relational-only; canonical graph only receives
approved outputs; LangGraph checkpoints are library-managed (not application state).

---

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Principle IV exception: approval inbox is a CRUD list, not topology-first | The inbox is a governance surface — it enables every canonical graph write for Phase 2. Without it, no approved state can enter the graph, making the topology surface (Phase 3 Galaxy) impossible to populate. The operator needs to act on items; a topology view of pending items would obscure actionability. | A topology-first pending-items surface would be unintuitive (you'd be visualizing provisional state that may be rejected). The inbox is explicitly scoped to Phase 2 localhost; Phase 3 integrates approved outputs into the topology surface. |

---

## Project Structure

### Documentation (this feature)

```text
specs/002-phase-2-intelligence/
├── plan.md          ← this file
├── spec.md
├── research.md      ← Phase 0 complete
├── data-model.md    ← Phase 1 complete
├── quickstart.md    ← Phase 1 complete
├── contracts/
│   └── api.yaml     ← Phase 1 complete
├── checklists/
│   └── requirements.md
└── tasks.md         ← generated by /speckit.tasks (not yet)
```

### Source Code (repository root)

Phase 2 extends Phase 1's `src/context_os/` layout. No existing modules are removed;
new modules are added alongside existing ones.

```text
src/context_os/
├── config.py             (Phase 1 — extended with new env vars)
├── main.py               (Phase 1 — new routers registered)
├── cli.py                (Phase 1 — new eval subcommands added)
├── core/
│   ├── ontology.py       (Phase 1 — no changes needed)
│   └── errors.py         (Phase 1 — new error types added)
│
├── agents/               ← NEW: AI agent module
│   ├── __init__.py
│   ├── base.py           ← AbstractAgent: autonomy level, OTEL wrapper, tool-use loop
│   ├── synthesizer/
│   │   ├── __init__.py
│   │   ├── agent.py      ← LangGraph StateGraph + interrupt_before(approve)
│   │   ├── tools.py      ← read-only tools: retrieve_graph_context, retrieve_vector_context,
│   │   │                    check_actor_exists
│   │   ├── prompts.py    ← system prompt templates (briefing sections)
│   │   └── failure_detection.py  ← rule-based checks: hallucinated_stakeholder,
│   │                                stale_dependency, missed_escalation, citation_error
│   └── mapper/
│       ├── __init__.py
│       ├── agent.py      ← LangGraph StateGraph for dependency walk
│       ├── tools.py      ← graph walk tools: walk_graph, find_cross_initiative_signals
│       └── prompts.py    ← dependency candidate classification prompt
│
├── workflows/            ← NEW: durable workflow definitions
│   ├── __init__.py
│   ├── briefing.py       ← end-to-end: trigger → retrieve → synthesize →
│   │                        detect_failures → enqueue_approval → interrupt →
│   │                        (resume on approve) → promote_to_graph
│   └── dependency.py     ← dependency scan: walk_graph → classify_candidates →
│                             enqueue_proposals
│
├── eval/                 ← NEW: evaluation framework
│   ├── __init__.py
│   ├── runner.py         ← EvalRunner base: load dataset, run metrics, write EvalRun
│   ├── synthesizer_eval.py  ← metrics: accept_rate, edit_distance, false_positive_risk_rate,
│   │                            failure_mode_detection (4 injected failure modes)
│   ├── mapper_eval.py       ← metrics: precision, recall, false_positive_rate
│   └── golden_dataset.py    ← GoldenDataset loader/builder from approved approval_items
│
├── db/
│   ├── engine.py         (Phase 1 — no changes)
│   ├── models.py         (Phase 1 + new tables: ApprovalItem, BriefingRun,
│   │                       EvalRun, GoldenDataset)
│   └── migrations/
│       ├── 0001_initial_schema.py   (Phase 1)
│       └── 0002_phase2_intelligence.py  ← NEW: 4 new tables + indexes
│
├── relational/
│   └── repositories.py   (Phase 1 + ApprovalItemRepository, BriefingRunRepository,
│                            EvalRunRepository, GoldenDatasetRepository)
│
├── graph/                (Phase 1 — extended)
│   ├── client.py         (no changes)
│   ├── queries.py        (Phase 1 + agent read queries: find_cross_initiative_signals,
│   │                       check_actor_exists, find_stale_dependencies)
│   └── mutations.py      (Phase 1 + promote_briefing_to_artifact, promote_risk_node,
│                            promote_dependency_edge)
│
├── vector/               (Phase 1 — no changes needed)
│
├── auth/                 (Phase 1 — no changes)
├── observability/        (Phase 1 — no changes)
│
└── api/
    ├── ingest.py         (Phase 1 — no changes)
    ├── graph.py          (Phase 1 — no changes)
    ├── vector.py         (Phase 1 — no changes)
    ├── admin.py          (Phase 1 — no changes)
    ├── briefing.py       ← NEW: POST /briefing/generate, GET /briefing/status/{run_id}
    ├── inbox.py          ← NEW: GET /inbox, GET/POST /inbox/{id}/approve|reject
    ├── mapper.py         ← NEW: POST /mapper/scan
    └── eval_api.py       ← NEW: POST /eval/run, GET /eval/runs, GET /eval/runs/{id}

tests/
├── unit/
│   ├── test_normalizers.py      (Phase 1)
│   └── test_failure_detection.py  ← NEW: unit tests for 4 failure-mode detectors
├── integration/
│   ├── test_tenant_isolation.py   (Phase 1)
│   └── test_approval_flow.py      ← NEW: full approve/reject lifecycle
├── evals/               ← NEW: evaluation suite tests (run with pytest)
│   ├── conftest.py      ← fixtures: golden dataset loader, agent mock/real toggle
│   ├── golden/          ← versioned golden dataset JSON files (gitignored if large)
│   ├── test_synthesizer_eval.py  ← pytest parametrize over golden dataset records
│   └── test_mapper_eval.py
└── fault/
    ├── test_oauth_expiry.py     (Phase 1)
    └── test_rate_limit.py       (Phase 1)
```

---

## Key Patterns

### LangGraph briefing workflow with human-in-the-loop

```python
# workflows/briefing.py (sketch — not implementation)
from langgraph.graph import StateGraph
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

builder = StateGraph(BriefingState)
builder.add_node("retrieve_signals", retrieve_signals_node)
builder.add_node("synthesize_draft", synthesize_draft_node)   # calls Anthropic API
builder.add_node("detect_failures", detect_failures_node)      # rule-based checks
builder.add_node("enqueue_approval", enqueue_approval_node)    # writes approval_items row
builder.add_node("promote_to_graph", promote_to_graph_node)    # writes to AGE graph
builder.add_edge("retrieve_signals", "synthesize_draft")
builder.add_edge("synthesize_draft", "detect_failures")
builder.add_edge("detect_failures", "enqueue_approval")
# Workflow suspends here; inbox /approve endpoint resumes the thread
builder.add_edge("enqueue_approval", END)

# On operator approval:
# await graph.ainvoke({"operator_action": "approve", "edited_content": ...},
#                     config={"configurable": {"thread_id": thread_id}})
```

### Agent tool-use (read-only tools exposed to LLM)

```python
# agents/synthesizer/tools.py (sketch)
SYNTHESIZER_TOOLS = [
    {
        "name": "retrieve_graph_context",
        "description": "Retrieve goal/initiative/signal nodes from the memory graph",
        "input_schema": {"type": "object", "properties": {
            "query": {"type": "string"},
            "node_types": {"type": "array", "items": {"type": "string"}},
            "max_hops": {"type": "integer"}
        }, "required": ["query"]}
    },
    {
        "name": "retrieve_vector_context",
        "description": "Semantic similarity search over memory and artifact nodes",
        "input_schema": {"type": "object", "properties": {
            "query": {"type": "string"}, "k": {"type": "integer"}
        }, "required": ["query"]}
    },
    {
        "name": "check_actor_exists",
        "description": "Verify a stakeholder name exists in the Actor graph",
        "input_schema": {"type": "object", "properties": {
            "name": {"type": "string"}
        }, "required": ["name"]}
    }
]
# Write tools are NEVER in this list — autonomy level enforced at platform layer
```

### Failure-mode detection (rule-based, runs before approval enqueue)

```python
# agents/synthesizer/failure_detection.py (sketch)
async def detect_hallucinated_stakeholder(name: str, tenant_id: str, graph: AGEClient) -> bool:
    # Query: MATCH (a:Actor {tenant_id: $tid}) WHERE a.name CONTAINS $name RETURN a LIMIT 1
    return not await graph.actor_exists(name, tenant_id)

async def detect_stale_dependency(edge_id: str, tenant_id: str, repo: Repository) -> bool:
    edge = await repo.get_edge(edge_id, tenant_id)
    return edge.updated_at < (now() - timedelta(days=90))

async def detect_missed_escalation(draft: BriefingDraft, tenant_id: str, graph: AGEClient) -> bool:
    # Query for high-severity Risk nodes not referenced in draft.sections.escalations
    ...

async def detect_citation_error(source_id: str, tenant_id: str, repo: Repository) -> bool:
    return not await repo.node_embedding_exists(source_id, tenant_id)
```

### Eval runner pattern

```python
# eval/synthesizer_eval.py (sketch)
@pytest.mark.eval
@pytest.mark.parametrize("record", load_golden_dataset("synthesizer", "latest"))
async def test_synthesizer_accept_rate(record, synthesizer_agent):
    draft = await synthesizer_agent.generate(record["window_start"], record["window_end"])
    edit_dist = normalized_edit_distance(draft.content, record["approved_content"])
    accepted_as_is = edit_dist < ACCEPT_AS_IS_THRESHOLD

    # CI gate: aggregate across all records at the end of the session
    assert_ci_gate("synthesizer.accept_rate", accepted_as_is)
```

---

## New Environment Variables

Add to `.env.example` (Phase 1 base + Phase 2 additions):

```bash
# Phase 2 — Intelligence
ANTHROPIC_API_KEY=sk-ant-...        # Required: Anthropic Claude API key
ANTHROPIC_MODEL=claude-sonnet-4-6   # Optional: defaults to claude-sonnet-4-6
ANTHROPIC_MAX_TOKENS=4096           # Optional: max tokens per synthesis call
BRIEFING_COST_BUDGET_TOKENS=50000   # Optional: per-run budget (halts generation if exceeded)
SLACK_WEBHOOK_URL=                  # Optional: Slack delivery channel for approved briefings
BRIEFING_SCHEDULE_CRON=             # Optional: cron expression for scheduled briefings
```

---

## Dev Commands (Phase 2)

```bash
# Install new dependencies (LangGraph, Anthropic SDK, Levenshtein)
uv sync

# Run Phase 2 migration
uv run alembic upgrade head

# Start the server (Phase 1 + Phase 2 endpoints)
uv run uvicorn context_os.main:app --reload --port 8000

# Trigger a briefing (CLI shortcut)
uv run python -m context_os.cli briefing generate

# Build a golden dataset from recent approved briefings
uv run python -m context_os.cli eval build-dataset --type synthesizer --version "1.0.0"

# Run eval suite (all evals)
uv run pytest tests/evals/ -v

# Run only CI gate evals (fast path)
uv run pytest tests/evals/ -m "ci_gate" -v

# Lint + format
uv run ruff check . && uv run ruff format .

# Type check
uv run pyright
```

---

## Dependency Graph (phases)

```
Phase 0 (research.md)  ──complete──▶  resolved; see research.md
Phase 1 Foundation     ──required──▶  must be running before Phase 2 implementation
Phase 1 Design         ──complete──▶  data-model.md, contracts/api.yaml, quickstart.md
Phase 2 Implementation ──order──▶
  Setup: pyproject.toml + new deps (LangGraph, anthropic, levenshtein)
  Foundational: db/models.py extension, Alembic migration, repositories
  US1 (Briefing): agents/synthesizer/, workflows/briefing.py, api/briefing.py, api/inbox.py
  US2 (Inbox):    api/inbox.py approve/reject + graph promotion mutations
  US3 (Mapper):   agents/mapper/, workflows/dependency.py, api/mapper.py
  US4 (Eval):     eval/, tests/evals/, CLI eval commands
  Polish:         integration tests, pyright, ruff, quickstart validation
```
