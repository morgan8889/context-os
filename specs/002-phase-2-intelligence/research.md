# Research: Phase 2 — Intelligence

**Feature**: 002-phase-2-intelligence  
**Date**: 2026-05-18  
**Status**: Complete — all unknowns resolved

---

## Decision 1: Durable workflow orchestration — LangGraph vs Temporal

**Decision**: LangGraph v0.2+ with `langgraph-checkpoint-postgres`  
**Rationale**:
- The briefing workflow crosses a human async boundary (agent drafts → human approves →
  agent resumes to commit). LangGraph's `interrupt_before` mechanism suspends the graph
  at any named node and resumes on demand with operator input — this is the exact pattern
  the approval inbox requires.
- `AsyncPostgresSaver` (from `langgraph-checkpoint-postgres`) stores checkpoint state in
  the existing Postgres instance — no new infrastructure required.
- Python-native; no separate server process.
- LangGraph's typed `StateGraph` makes autonomy-level enforcement explicit: write tools
  are never exposed to the LLM; only read tools are in the tool list. The graph node that
  writes to the canonical graph is a deterministic Python step, not an LLM step.
**Alternatives considered**:
- **Temporal**: Robust durable execution, but requires a separate Temporal server (Go
  binary + Postgres) and a Python worker SDK. Adds significant ops complexity for a
  solo MVP build; ruled out until Phase 4+.
- **Celery + Redis**: Task queues don't support human-in-the-loop interruption; ruled
  out immediately.
- **In-memory async (asyncio tasks)**: Violates the constitution's durable-orchestration
  requirement; ruled out.

---

## Decision 2: Agent implementation — Anthropic SDK direct vs framework

**Decision**: Anthropic Python SDK (`anthropic`) with a custom tool-use loop  
**Rationale**:
- Direct SDK gives full control over the tool-use loop, enabling precise autonomy-level
  enforcement: the LLM receives only read tools (`retrieve_graph_context`,
  `retrieve_vector_context`, `check_actor_exists`); write paths are never in the tool
  list and are executed deterministically by the workflow graph after human approval.
- Minimal dependency surface — the `anthropic` SDK is already likely a dependency;
  no additional framework abstractions are introduced.
- Tool definitions map 1:1 to Phase 1's graph/queries.py, vector/search.py, and
  relational/repositories.py — no translation layer.
- Cost and token count are captured directly from `response.usage` for OTEL telemetry.
**Alternatives considered**:
- **LangChain agents**: Adds significant abstraction; tool wrapping obscures token cost
  and makes autonomy-level enforcement harder to reason about. Ruled out.
- **smolagents (Hugging Face)**: Limited Claude support; ruled out.
- **LlamaIndex agent**: Another abstraction layer; ruled out in favor of direct SDK.

---

## Decision 3: Eval framework — deepeval vs inspect-ai vs custom pytest

**Decision**: Custom pytest-based eval runner using project's existing test toolchain  
**Rationale**:
- Phase 1 establishes `pytest + anyio` as the testing standard. Eval suites are spec'd
  as CI-integrated test jobs — keeping them in pytest allows the same `uv run pytest`
  invocation and the same CI step.
- The three metrics required (accept-as-is rate, edit distance, false-positive rate) are
  straightforward to implement directly: edit distance uses `python-Levenshtein` or the
  standard `difflib.SequenceMatcher`; accept-rate is a proportion; precision/recall is
  standard.
- Custom runner means full control over output format (JSON results for trending) and
  failure-mode injection (synthetic error fixtures).
- `EvalRun` results are written to the `eval_runs` table via existing SQLAlchemy
  repositories — no separate metrics store needed.
**Alternatives considered**:
- **deepeval**: Feature-rich but introduces a large dependency and its own DSL. Its LLM
  judge model adds cost and non-determinism to CI. Ruled out for MVP.
- **inspect-ai (UKAIS)**: Excellent framework but Python-only DSL that would diverge
  from the pytest standard. Ruled out.
- **Langfuse evals**: Langfuse is permitted as an add-on (Phase 1 already wires
  `LangfuseSpanProcessor`); Langfuse's eval scoring can annotate runs post-hoc but
  cannot serve as the CI gate. Supplementary, not primary.

---

## Decision 4: Pending output storage — Postgres JSONB vs graph nodes

**Decision**: Postgres `approval_items` table with JSONB content column  
**Rationale**:
- The canonical memory graph must not contain provisional AI-generated state.
  Constitution Principle II states that graph state is authoritative; polluting it with
  pending items that may be rejected would violate this invariant.
- Pending items need CRUD operations (list, update status, paginate, filter by stale) —
  relational queries are idiomatic here; Cypher traversal is not.
- On approval, the workflow deterministically writes the approved content to the canonical
  graph (AGE) and relational tables; the `approval_items` row is updated to "approved".
  Rejected rows stay in the table as a provenance record (they are never deleted).
- JSONB content accommodates heterogeneous item types (BriefingDraft, ProposedRisk,
  ProposedDependency) in one table without separate tables per type.
**Alternatives considered**:
- **Separate table per item type**: Three tables instead of one; adds migration overhead
  for each new agent output type. Ruled out for MVP.
- **Graph nodes with `status: pending`**: Violates the invariant that graph nodes are
  canonical facts. Ruled out.

---

## Decision 5: Approval inbox interface — REST polling vs WebSocket

**Decision**: REST polling (standard FastAPI JSON endpoints)  
**Rationale**:
- Phase 2 is a single-user localhost deployment. The operator checks the inbox manually;
  no push notification latency requirement exists.
- REST endpoints are already the project standard (Phase 1 api/ module); adding
  WebSocket support adds protocol complexity and a new connection lifecycle.
- A `stale` flag computed at query time (compare `created_at + 24h` to `now()`) satisfies
  the staleness visibility requirement without server-sent events.
**Alternatives considered**:
- **WebSocket**: Unnecessary for localhost single-user Phase 2; deferred to Phase 3+ if
  real-time push is needed for multi-user scenarios.
- **Server-Sent Events (SSE)**: Same rationale; deferred.

---

## Decision 6: Briefing delivery channels — Phase 2 scope

**Decision**: Approval inbox UI (localhost) is the only delivery mechanism in Phase 2;
Slack/email delivery is wired but opt-in and not required for Phase 2 exit  
**Rationale**:
- Spec assumption A-005 explicitly scopes delivery channels as optional in Phase 2.
- The Slack bot integration required for delivery is a non-trivial addition (separate
  OAuth scope, outbound API calls); deferring keeps Phase 2 focused.
- The approval inbox REST API is sufficient for the single-operator dogfooding scenario.
- Slack delivery: implement as a thin `notify_slack(webhook_url, content)` call wired
  into the post-approval step; gated on `SLACK_WEBHOOK_URL` env var being set.

---

## Decision 7: LangGraph checkpoint table management

**Decision**: Use `langgraph-checkpoint-postgres` library's built-in migration; do not
add LangGraph checkpoint tables to Alembic migrations  
**Rationale**:
- `AsyncPostgresSaver.setup()` creates its own tables (`checkpoints`,
  `checkpoint_blobs`, `checkpoint_writes`) on first use via the library's internal
  DDL. These are implementation details of the orchestrator, not the application schema.
- Adding them to Alembic would create a split ownership problem (Alembic and the library
  both want to own table shape). The library's DDL is idempotent; calling `setup()` in
  the FastAPI lifespan is safe.
- The Alembic migrations own the application tables (`approval_items`, `briefing_runs`,
  `eval_runs`, `golden_datasets`); the LangGraph library owns its checkpoint tables.

---

## Decision 8: Failure-mode detection implementation

**Decision**: Rule-based checks in Python executed after LLM synthesis, before
the ApprovalItem is written to the `approval_items` table  
**Rationale**:
- Four failure modes (hallucinated stakeholder, stale dependency, missed escalation,
  citation error) have deterministic detection conditions:
  - **Hallucinated stakeholder**: named person in draft not found in Actor graph (graph
    query: `MATCH (a:Actor {tenant_id: $tid}) WHERE a.name CONTAINS $name RETURN a`)
  - **Stale dependency**: cited DEPENDS_ON edge has `updated_at` older than 90 days
  - **Missed escalation**: Risk node in graph with `severity >= HIGH` and no
    corresponding risk item in draft sections
  - **Citation error**: claimed source_id in draft not found in `node_embeddings` table
- These checks run synchronously in the Synthesizer's LangGraph `detect_failures` node
  before the draft is enqueued. Detected issues are annotated on the draft (`failure_flags`
  field in the BriefingDraft JSONB).
- The operator sees failure flags in the approval inbox and can dismiss or confirm each.
- LLM-as-judge detection is deliberately rejected: it adds cost, non-determinism, and
  a secondary LLM dependency to a CI-integrated eval suite.
