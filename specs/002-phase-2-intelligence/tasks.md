# Tasks: Phase 2 — Intelligence

**Input**: Design documents from `specs/002-phase-2-intelligence/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/api.yaml ✓, quickstart.md ✓
**Assumes**: Phase 1 Foundation fully implemented (src/context_os/ exists, Phase 1 migration applied, Phase 1 API running)

**Tests**: Eval suite tests included per spec US4 (explicitly required by constitution Principle V); integration test for approval flow included per US2 acceptance scenarios.

**Organization**: Tasks grouped by user story; each story independently testable after its phase completes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other [P] tasks in the same phase (different files, no unresolved dependencies)
- **[US#]**: Which user story this task belongs to
- All paths relative to repository root

---

## Phase 1: Setup

**Purpose**: Add Phase 2 dependencies and configuration to the existing Phase 1 project

- [ ] T001 Update pyproject.toml — add `langgraph>=0.2`, `langgraph-checkpoint-postgres`, `anthropic`, `python-levenshtein` to `[project.dependencies]`; run `uv sync` to verify resolution
- [ ] T002 [P] Update .env.example — add Phase 2 variables: `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL=claude-sonnet-4-6`, `ANTHROPIC_MAX_TOKENS=4096`, `BRIEFING_COST_BUDGET_TOKENS=50000`, `SLACK_WEBHOOK_URL`, `BRIEFING_SCHEDULE_CRON`
- [ ] T003 [P] Extend src/context_os/config.py — add Pydantic Settings fields for all Phase 2 env vars (`anthropic_api_key: SecretStr`, `anthropic_model: str`, `anthropic_max_tokens: int`, `briefing_cost_budget_tokens: int`, `slack_webhook_url: str | None`, `briefing_schedule_cron: str | None`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared data layer, base abstractions, and error taxonomy — MUST complete before any user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Extend src/context_os/db/models.py — add 4 SQLAlchemy models per data-model.md: `ApprovalItem` (id, tenant_id, item_type, status, content JSONB, failure_flags JSONB, created_at, updated_at, operator_id, acted_at, rejection_reason, edit_delta JSONB, stale_notified_at, run_id, graph_node_id, workflow_thread_id), `BriefingRun` (id, tenant_id, trigger_type, window_days, window_start, window_end, status, input_signal_counts JSONB, retrieval_hit_rate, cost_tokens, latency_ms, error_detail, created_at, completed_at, approval_item_id), `EvalRun` (id, tenant_id, eval_type, dataset_id, dataset_version, status, scores JSONB, gates_passed, compared_to_run_id, score_deltas JSONB, created_at, completed_at, duration_ms, error_detail), `GoldenDataset` (id, tenant_id, dataset_type, version, description, record_count, content JSONB, created_at, built_from_approval_items JSONB)
- [ ] T005 [P] Write src/context_os/db/migrations/0002_phase2_intelligence.py — Alembic migration creating all 4 new tables with indexes: `ix_approval_items_tenant_status (tenant_id, status)`, `ix_approval_items_tenant_created (tenant_id, created_at DESC)`, `ix_approval_items_run_id (run_id) WHERE run_id IS NOT NULL`, `ix_briefing_runs_tenant (tenant_id, created_at DESC)`, `ix_eval_runs_tenant_type (tenant_id, eval_type, created_at DESC)`; down migration drops all 4 tables
- [ ] T006 [P] Add 4 new repositories to src/context_os/relational/repositories.py — `ApprovalItemRepository` (create, get_by_id, list_by_tenant with status/item_type/stale filters, update_status, update_approval, update_rejection), `BriefingRunRepository` (create, get_by_id, get_active_for_tenant, update_status), `EvalRunRepository` (create, get_by_id, list_by_tenant, update_scores), `GoldenDatasetRepository` (create, get_by_id, get_latest_by_type); all methods async, all queries filter `tenant_id`
- [ ] T007 [P] Create src/context_os/agents/__init__.py, src/context_os/agents/synthesizer/__init__.py, src/context_os/agents/mapper/__init__.py, and src/context_os/agents/base.py — `AbstractAgent` with: `agent_identity: str`, `autonomy_level: int`, `async def _emit_agent_span(self, input_summary, output_summary, cost_tokens, governance_markers)` that creates an OTEL span with all required `context_os.*` attributes (`context_os.agent_identity`, `context_os.autonomy_level`, `context_os.tenant_id`, `context_os.input_summary`, `context_os.output_summary`, `context_os.governance_markers`, `context_os.cost_tokens`); `async def run()` abstract method
- [ ] T008 [P] Add new error types to src/context_os/core/errors.py — `AgentError(ContextOSError)`, `ApprovalError(ContextOSError)` (with `item_id: str` field), `EvalError(ContextOSError)`, `BudgetExceededError(AgentError)` (with `tokens_used: int`, `budget: int` fields), `WorkflowError(ContextOSError)` (with `thread_id: str | None` field)

**Checkpoint**: Run `uv run alembic upgrade head` — must complete without error before proceeding

---

## Phase 3: User Story 1 — Receive a useful weekly briefing (Priority: P1) 🎯 MVP

**Goal**: Trigger briefing generation, have the Operational Synthesizer agent produce a structured draft, and surface the draft in the approval inbox within 5 minutes.

**Independent Test**: With ≥ 1 week of ingested data, POST `/briefing/generate`, poll status until `complete`, GET `/inbox`, verify a `briefing_draft` ApprovalItem with 5 populated sections appears within 5 minutes.

- [ ] T009 [US1] Add synthesizer graph read queries to src/context_os/graph/queries.py — `find_signals_in_window(tenant_id, window_start, window_end, sources)` returns Signal nodes with provenance in time window; `check_actor_exists(tenant_id, name_fragment)` returns bool (used for hallucination detection); `find_stale_dependencies(tenant_id, older_than_days)` returns DEPENDS_ON edges with `updated_at` older than threshold; all queries tenant-scoped via AGE parameter map
- [ ] T010 [P] [US1] Create src/context_os/agents/synthesizer/tools.py — 3 Anthropic tool-use schema dicts: `retrieve_graph_context` (query: str, node_types: list[str], max_hops: int — wraps graph/queries.py traversal), `retrieve_vector_context` (query: str, k: int — wraps vector/search.py top-k), `check_actor_exists` (name: str — wraps `check_actor_exists` query from T009); `async def execute_tool(tool_name, tool_input, tenant_id, db_session, age_conn)` dispatcher; module-level `SYNTHESIZER_TOOLS` list for Anthropic API
- [ ] T011 [P] [US1] Create src/context_os/agents/synthesizer/prompts.py — `BRIEFING_SYSTEM_PROMPT` string: instructs Claude to produce a JSON structure with 5 sections (progress, risks, decisions, dependencies, escalations); each item must cite `source_ids` from retrieved graph nodes; includes low-signal handling instruction (acknowledge sparsity, do not fabricate); `build_briefing_user_prompt(window_start, window_end, signal_count)` function
- [ ] T012 [US1] Create src/context_os/agents/synthesizer/failure_detection.py — 4 async functions: `detect_hallucinated_stakeholder(name, tenant_id, age_conn) -> FailureFlag | None` (calls `check_actor_exists`; returns flag if not found), `detect_stale_dependency(edge_id, tenant_id, age_conn) -> FailureFlag | None` (checks `updated_at < now() - 90 days`), `detect_missed_escalation(draft_sections, tenant_id, age_conn) -> FailureFlag | None` (queries high-severity Risk nodes not referenced in escalations section), `detect_citation_error(source_id, tenant_id, session) -> FailureFlag | None` (checks node_embeddings table); `async def run_all_failure_checks(draft, tenant_id, age_conn, session) -> list[FailureFlag]` runs all 4 and returns list
- [ ] T013 [US1] Create src/context_os/agents/synthesizer/agent.py — `BriefingState` TypedDict (tenant_id, window_start, window_end, window_days, signals_retrieved, draft_sections, failure_flags, cost_tokens, approval_item_id, error); `SynthesizerAgent(AbstractAgent)` with `agent_identity="synthesizer"`, `autonomy_level=2`; `StateGraph` nodes: `retrieve_signals` (calls graph + vector tools, populates signals_retrieved), `synthesize_draft` (Anthropic `client.messages.create` tool-use loop using SYNTHESIZER_TOOLS, accumulates cost from `response.usage`; halts if cost_tokens exceeds `BRIEFING_COST_BUDGET_TOKENS`), `detect_failures` (calls T012 `run_all_failure_checks`), `enqueue_approval` (writes ApprovalItem to DB via ApprovalItemRepository, sets `workflow_thread_id`); edges: retrieve_signals → synthesize_draft → detect_failures → enqueue_approval → END; `AsyncPostgresSaver` passed in at construction
- [ ] T014 [US1] Create src/context_os/workflows/briefing.py and src/context_os/workflows/__init__.py — `BriefingWorkflow` class: `__init__(self, agent: SynthesizerAgent, briefing_run_repo, approval_item_repo, checkpointer)`, `async def start(tenant_id, window_days, trigger_type) -> str` (creates BriefingRun record with status=generating, computes window, invokes agent graph, returns run_id; updates BriefingRun to complete/failed on finish), `async def resume(thread_id, operator_action, edited_content=None)` (resumes suspended LangGraph thread after operator approval action; updates BriefingRun if applicable); low-signal check (< 5 signals) sets `low_signal=True` in draft content; data-stale check (last ingest > 7 days) sets `data_stale=True`
- [ ] T015 [P] [US1] Create src/context_os/api/inbox.py — `GET /inbox` router: reads `status`, `item_type`, `stale_only`, `limit`, `offset` query params; calls `ApprovalItemRepository.list_by_tenant`; computes `stale = (now() - item.created_at) > timedelta(hours=24)` at query time; returns `ApprovalItemSummary` list with `preview` (first 200 chars of primary content field), `pending_count`; `GET /inbox/{item_id}`: returns full `ApprovalItem` including `failure_flags` and complete `content`; both endpoints require Clerk auth and scope to tenant
- [ ] T016 [US1] Create src/context_os/api/briefing.py — `POST /briefing/generate`: validates no active BriefingRun for tenant (returns 409 if found); validates ≥ 1 ingest record exists (returns 400 if no data); instantiates BriefingWorkflow and runs `start()` as background task; returns 202 with BriefingRunStatus; `GET /briefing/status/{run_id}`: reads BriefingRun by id, scoped to tenant; returns BriefingRunStatus including `approval_item_id` when complete
- [ ] T017 [US1] Update src/context_os/main.py — import and `app.include_router` for `/briefing` and `/inbox` routers; in FastAPI `lifespan` context manager: call `await AsyncPostgresSaver.setup(db_pool)` after engine setup; add BriefingWorkflow dependency to app state

**Checkpoint**: POST `/briefing/generate` with real ingested data returns 202; polling `/briefing/status/{run_id}` reaches `complete` within 5 minutes; GET `/inbox` returns the draft with 5 populated sections.

---

## Phase 4: User Story 2 — Review and act on the approval inbox (Priority: P2)

**Goal**: Approve, reject, or edit-then-approve any pending ApprovalItem; approved items are promoted to canonical graph state; rejected items are recorded as provenance with no graph write.

**Independent Test**: Create 3 pending ApprovalItems directly in DB (one of each item_type); call approve on first, reject on second, edit-then-approve on third; verify graph has 2 new nodes/edges, rejection log has 1 entry, edit_delta is populated on the edit-approve item.

- [ ] T018 [US2] Add graph promotion mutations to src/context_os/graph/mutations.py — `async def promote_briefing_to_artifact(tenant_id, approved_content, approval_item_id, operator_id, age_conn)` writes Artifact {subtype:'briefing', title, content, window_start, window_end, approval_item_id, operator_id, approved_at} node via AGE MERGE; `async def promote_risk_node(tenant_id, approved_content, approval_item_id, operator_id, age_conn)` writes Risk node; `async def promote_dependency_edge(tenant_id, approved_content, approval_item_id, operator_id, age_conn)` writes DEPENDS_ON edge with mapper_confidence, evidence_item_ids, approval_item_id, operator_id; all functions return the created node/edge id
- [ ] T019 [US2] Implement POST /inbox/{item_id}/approve in src/context_os/api/inbox.py — validate item exists for tenant and status=pending (400 if not); accept optional `edited_content` body; compute edit_delta (token diff using `difflib.SequenceMatcher` between original and final content text); call graph promotion function matching `item.item_type` (briefing_draft → promote_briefing_to_artifact, proposed_risk → promote_risk_node, proposed_dependency → promote_dependency_edge); update ApprovalItem (status=approved, operator_id, acted_at, graph_node_id, edit_delta); if item has workflow_thread_id: resume LangGraph thread via `BriefingWorkflow.resume(thread_id, action="approve", edited_content=...)`; return updated ApprovalItem
- [ ] T020 [US2] Implement POST /inbox/{item_id}/reject in src/context_os/api/inbox.py — validate item exists for tenant and status=pending; accept optional `reason` body; update ApprovalItem (status=rejected, operator_id, acted_at, rejection_reason); emit OTEL span with `context_os.governance_markers=["rejected"]`; no graph write; return updated ApprovalItem
- [ ] T021 [US2] Create tests/integration/test_approval_flow.py — 3 integration tests using real DB (pytest-anyio, test DB session fixture): `test_approve_briefing_draft` (create ApprovalItem with item_type=briefing_draft, POST approve, assert status=approved, assert AGE Artifact node exists with correct tenant_id), `test_reject_proposed_risk` (create ApprovalItem with item_type=proposed_risk, POST reject with reason, assert status=rejected, assert no Risk node in graph), `test_edit_and_approve_proposed_dependency` (create ApprovalItem, POST approve with edited_content, assert edit_delta populated, assert DEPENDS_ON edge in graph)

**Checkpoint**: All 3 integration tests in test_approval_flow.py pass; canonical graph contains promoted nodes/edges only for approved items; rejected items have no graph state.

---

## Phase 5: User Story 3 — Dependency surface discovers hidden relationships (Priority: P3)

**Goal**: Trigger a Dependency Mapper scan; the agent walks the memory graph and Slack signals to discover undocumented dependency relationships; proposed edges appear in the approval inbox.

**Independent Test**: With ≥ 2 active Initiatives and cross-initiative Slack signals ingested, POST `/mapper/scan`, wait for completion, GET `/inbox?item_type=proposed_dependency` — verify ≥ 1 proposed_dependency ApprovalItem with `evidence` citations and `confidence` score.

- [ ] T022 [US3] Add Dependency Mapper graph queries to src/context_os/graph/queries.py — `find_cross_initiative_signals_for_mapper(tenant_id, max_depth)` walks up to max_depth hops from each Initiative node and returns Signal nodes that connect multiple Initiatives (potential dependency evidence); `find_pr_review_patterns(tenant_id)` returns pairs of (Initiative, Initiative) where shared Actor nodes appear as reviewer on Artifact nodes for both; queries must include `tenant_id` in all AGE MATCH predicates
- [ ] T023 [P] [US3] Create src/context_os/agents/mapper/tools.py — 2 Anthropic tool-use schema dicts: `walk_graph` (start_node_id: str, max_depth: int, edge_types: list[str] — wraps graph/queries.py traverse returning nodes + edges), `find_cross_initiative_signals` (max_depth: int — wraps `find_cross_initiative_signals_for_mapper` from T022); `async def execute_tool(tool_name, tool_input, tenant_id, age_conn)` dispatcher; module-level `MAPPER_TOOLS` list
- [ ] T024 [P] [US3] Create src/context_os/agents/mapper/prompts.py — `MAPPER_SYSTEM_PROMPT`: instructs Claude to identify dependency relationships from graph evidence, classify each candidate with a confidence score (0.0–1.0), cite the specific Signal/Artifact node IDs as evidence, and output a JSON list of candidates; `MAPPER_CONFIDENCE_THRESHOLD = 0.60` constant (candidates below threshold are not enqueued); `build_mapper_user_prompt(initiative_count, signal_count)` function
- [ ] T025 [US3] Create src/context_os/agents/mapper/agent.py — `MapperState` TypedDict (tenant_id, max_depth, focus_node_id, walk_results, candidates, enqueued_count, cost_tokens); `DependencyMapperAgent(AbstractAgent)` with `agent_identity="mapper"`, `autonomy_level=2`; `StateGraph` nodes: `walk_graph` (uses find_cross_initiative_signals tool to gather evidence), `classify_candidates` (Anthropic tool-use loop using MAPPER_TOOLS to classify each candidate with confidence score), `enqueue_proposals` (for each candidate above MAPPER_CONFIDENCE_THRESHOLD: create proposed_dependency ApprovalItem via ApprovalItemRepository; set evidence, confidence, from_node_id, to_node_id in content); edges: walk_graph → classify_candidates → enqueue_proposals → END; check for duplicate proposed/existing DEPENDS_ON edges before enqueuing (skip if duplicate)
- [ ] T026 [US3] Create src/context_os/workflows/dependency.py — `DependencyWorkflow` class: `async def scan(tenant_id, max_depth=3, focus_node_id=None) -> MapperScanStatus` instantiates DependencyMapperAgent, runs graph (no interrupt — mapper terminates after enqueue), returns MapperScanStatus with proposed_count; no BriefingRun equivalent (scans are stateless — status computed from approvals); track scan in a minimal in-memory dict keyed by tenant_id to support 409 conflict check
- [ ] T027 [US3] Create src/context_os/api/mapper.py — `POST /mapper/scan`: validates no active scan for tenant (409 if found); validates graph has ≥ 2 Initiative nodes (400 if not); runs DependencyWorkflow.scan() as background task; returns 202 MapperScanStatus; register /mapper router in src/context_os/main.py via `app.include_router`

**Checkpoint**: POST `/mapper/scan` returns 202; after completion, GET `/inbox?item_type=proposed_dependency` returns ≥ 1 item with populated `content.evidence` and `content.confidence` fields; approving the item via POST `/inbox/{id}/approve` creates a DEPENDS_ON edge in the AGE graph.

---

## Phase 6: User Story 4 — Eval suite confirms agent quality (Priority: P4)

**Goal**: Both eval suites run against golden datasets, report structured scores, and enforce CI regression gates before Phase 3 promotion.

**Independent Test**: Build golden dataset from 5 known approved briefings; run `POST /eval/run` with `eval_type=synthesizer`; verify `GET /eval/runs/{run_id}` returns `gates_passed` bool, `scores.accept_rate`, `scores.median_edit_distance`, and all 4 failure-mode detection results within the report.

- [ ] T028 [P] [US4] Create src/context_os/eval/golden_dataset.py and src/context_os/eval/__init__.py — `GoldenRecord` dataclass (for synthesizer: window_start, window_end, draft_content, approved_content, accepted_as_is: bool, edit_delta, failure_mode_injections: list[dict]); (for mapper: from_node_id, to_node_id, ground_truth_exists: bool, evidence_signals: list[str]); `GoldenDataset` dataclass (records: list[GoldenRecord], version, dataset_type); `async def load_dataset(eval_type, version, repo: GoldenDatasetRepository) -> GoldenDataset` reads from DB; `async def build_synthesizer_dataset(approval_item_ids, injections, repo) -> GoldenDataset` constructs from approved ApprovalItems with optional failure-mode injections (injects synthetic errors at specified positions); `async def build_mapper_dataset(dependency_pairs, repo) -> GoldenDataset` constructs held-out dependency set
- [ ] T029 [P] [US4] Create src/context_os/eval/runner.py — `EvalRunner` abstract base: `async def run(dataset: GoldenDataset, tenant_id: str, session) -> EvalRunResult`; `_compute_score_deltas(current_scores, prior_run_id, repo)` reads prior EvalRun and computes deltas; `_write_eval_run(eval_type, dataset, scores, gates_passed, deltas, session, repo) -> EvalRun`; `_check_ci_gates(scores) -> bool` abstract method raising `EvalError` on failure; `EvalRunResult` dataclass (run_id, eval_type, scores, gates_passed, score_deltas, duration_ms)
- [ ] T030 [US4] Create src/context_os/eval/synthesizer_eval.py — `SynthesizerEvalRunner(EvalRunner)`: `_compute_accept_rate(records)` proportion where `SequenceMatcher(None, draft, approved).ratio() >= 0.90` (treat as accepted-as-is); `_compute_median_edit_distance(records)` median of `1 - SequenceMatcher(None, draft, approved).ratio()` across all records; `_compute_false_positive_risk_rate(records)` proportion of Risk items in draft that were rejected by operator; `_run_failure_mode_tests(records)` runs 4 injected failure-mode records and returns {hallucinated_stakeholder: bool, stale_dependency: bool, missed_escalation: bool, citation_error: bool} based on whether the failure_detection functions flagged the injection; `_check_ci_gates(scores)` raises `EvalError` if `accept_rate < 0.40`; overrides `run()` to call all 4 metric methods
- [ ] T031 [P] [US4] Create src/context_os/eval/mapper_eval.py — `MapperEvalRunner(EvalRunner)`: `_compute_precision(records)` proportion of proposed edges that have `ground_truth_exists=True`; `_compute_recall(records)` proportion of ground-truth edges (where `ground_truth_exists=True`) that were proposed by the mapper in the eval set; `_compute_false_positive_rate(records)` proportion of proposed edges where `ground_truth_exists=False`; `_check_ci_gates(scores)` raises `EvalError` if `recall < 0.50`; overrides `run()` to call all 3 metric methods
- [ ] T032 [P] [US4] Add eval CLI subcommands to src/context_os/cli.py — `app eval build-dataset --type [synthesizer|mapper] --version TEXT --description TEXT` (calls build_synthesizer_dataset or build_mapper_dataset from recent approved ApprovalItems, writes to GoldenDataset table, prints dataset ID); `app eval run --type [synthesizer|mapper] [--dataset-id UUID] [--compare-to UUID]` (runs EvalRunner subclass, prints scores table, exits non-zero if gates_passed=False)
- [ ] T033 [US4] Create src/context_os/api/eval_api.py — `POST /eval/run`: validates eval_type, finds or uses latest golden dataset, runs EvalRunner as background task (synthesizer or mapper based on type), returns 202 with run_id; `GET /eval/runs`: paginated list of EvalRun records for tenant filtered by optional eval_type; `GET /eval/runs/{run_id}`: full EvalRunResult; register /eval router in src/context_os/main.py
- [ ] T034 [US4] Create tests/evals/conftest.py and tests/evals/golden/ directory — `load_golden_dataset(eval_type)` fixture reads JSON files from `tests/evals/golden/{eval_type}_v1.json`; `assert_ci_gate(metric_name, value, threshold)` session-scoped accumulator that fails the session if any metric falls below threshold; `synthesizer_agent_fixture` that returns a mock SynthesizerAgent for unit-level eval tests; create `tests/evals/golden/synthesizer_v1.json` with 5 sample records (3 real-shaped + 2 failure-mode injection records) and `tests/evals/golden/mapper_v1.json` with 10 dependency pairs (7 ground-truth-exists=True, 3 false)
- [ ] T035 [P] [US4] Create tests/evals/test_synthesizer_eval.py — 4 parametrized `@pytest.mark.parametrize` failure-mode injection tests: one test per failure mode (hallucinated_stakeholder, stale_dependency, missed_escalation, citation_error) — each injects a synthetic error into the draft, runs `run_all_failure_checks`, asserts the correct FailureFlag is returned; `test_synthesizer_metrics_on_golden_dataset` runs SynthesizerEvalRunner against the 5-record golden dataset, asserts scores dict has all 4 keys, asserts `accept_rate` and `median_edit_distance` are floats in [0,1]
- [ ] T036 [P] [US4] Create tests/evals/test_mapper_eval.py — `test_mapper_metrics_on_golden_dataset` runs MapperEvalRunner against the 10-record golden dataset, asserts `precision`, `recall`, `false_positive_rate` are all floats in [0,1] and sum approximately correctly; `test_ci_gate_fails_on_low_recall` creates a dataset where all ground-truth records are absent (recall=0), runs MapperEvalRunner, asserts `EvalError` is raised
- [ ] T037 [P] [US4] Create tests/unit/test_failure_detection.py — 4 unit test functions using `AsyncMock` for graph/repo dependencies: `test_detect_hallucinated_stakeholder_flags_unknown_name` (mock check_actor_exists returns False, assert FailureFlag returned), `test_detect_hallucinated_stakeholder_passes_known_name` (returns True, assert None returned), `test_detect_stale_dependency_flags_old_edge`, `test_detect_citation_error_flags_missing_node_id`

**Checkpoint**: `uv run pytest tests/evals/ tests/unit/test_failure_detection.py -v` — all tests pass; `uv run python -m context_os.cli eval build-dataset --type synthesizer --version 1.0.0` completes without error; `GET /eval/runs/{run_id}` returns structured scores with `gates_passed` field.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: OTEL instrumentation completeness, code quality, type safety, end-to-end validation

- [ ] T038 Audit OTEL instrumentation in src/context_os/agents/base.py and all agent/workflow modules — verify every synthesizer and mapper agent action emits a span with all 7 required `context_os.*` attributes (`agent_identity`, `autonomy_level`, `tenant_id`, `input_summary`, `output_summary`, `governance_markers`, `cost_tokens`); add missing instrumentation to api/briefing.py, api/inbox.py, api/mapper.py handlers; verify briefing-specific attributes (FR-027) and mapper-specific attributes (FR-028) are present on respective spans
- [ ] T039 [P] Run `uv run ruff check . && uv run ruff format .` across all Phase 2 modules (agents/, workflows/, eval/, api/briefing.py, api/inbox.py, api/mapper.py, api/eval_api.py); fix all violations
- [ ] T040 [P] Run `uv run pyright` and resolve all type errors in Phase 2 modules; annotate all return types; add `py.typed` marker if missing; ensure `AsyncPostgresSaver`, LangGraph `StateGraph`, and Anthropic SDK types pass strict mode
- [ ] T041 Execute quickstart.md Scenario 1 end-to-end — run each curl command in sequence (POST /briefing/generate → poll /briefing/status → GET /inbox → POST /inbox/{id}/approve → verify Artifact in graph via GET /admin/entities?type=Artifact); document actual response shapes vs expected; fix any discrepancies

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories; T004 must complete before T005/T006; T007/T008 are independent
- **US1 (Phase 3)**: Depends on Foundational (Phase 2) — requires ApprovalItem model + repositories; no dependency on other user stories
- **US2 (Phase 4)**: Depends on US1 — approval actions operate on inbox items created by the Synthesizer agent; T018 graph mutations must precede T019/T020 endpoints
- **US3 (Phase 5)**: Depends on Foundational (Phase 2) + US2 approval infrastructure (T018 promote_dependency_edge used when mapper proposals are approved) — can begin after US2's T018 completes; does not require US1 full completion
- **US4 (Phase 6)**: Depends on US1 (golden dataset built from briefing approvals) and US3 (mapper eval requires mapper agent); T028/T029 are independent; T030/T031 depend on T028/T029
- **Polish (Phase 7)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: After Foundational — independently testable
- **US2 (P2)**: After US1 — requires items in inbox to act on
- **US3 (P3)**: After Foundational + T018 — independently testable for scan → proposal flow; full E2E (scan → approve → edge) requires US2
- **US4 (P4)**: After US1 + US3 — eval suites require agents to evaluate

### Within Each Phase — Sequential Order Required

Within US1: T009 → T010, T012 (parallel, both use T009) → T013 → T014 → T015 [P], T016 (parallel) → T017  
Within US2: T018 → T019 → T020 → T021  
Within US3: T022 → T023 [P], T024 [P] (parallel) → T025 → T026 → T027  
Within US4: T028 [P], T029 [P] (parallel) → T030, T031 [P], T032 [P], T033 (parallel) → T034 → T035 [P], T036 [P], T037 [P] (parallel)

---

## Parallel Opportunities by Phase

### Phase 2 Foundational
```
T004 (models.py — complete first)
  ↓ then launch in parallel:
T005 [P] migration  |  T006 [P] repositories  |  T007 [P] base.py  |  T008 [P] errors.py
```

### Phase 3 US1
```
T009 (graph queries)
  ↓ then:
T010 [P] tools.py  |  T011 [P] prompts.py  |  T012 failure_detection.py
  ↓ (T010 + T011 + T012 complete):
T013 agent.py
  ↓
T014 briefing workflow
  ↓
T015 [P] inbox GET  |  T016 briefing API
  ↓
T017 main.py wiring
```

### Phase 5 US3
```
T022 (mapper queries)
  ↓ then:
T023 [P] mapper/tools.py  |  T024 [P] mapper/prompts.py
  ↓
T025 mapper/agent.py
  ↓
T026 dependency workflow
  ↓
T027 mapper API + router
```

### Phase 6 US4
```
T028 [P] golden_dataset.py  |  T029 [P] runner.py  (fully parallel)
  ↓
T030 synthesizer_eval.py  |  T031 [P] mapper_eval.py  |  T032 [P] CLI  |  T033 eval API
  ↓
T034 tests/evals/conftest.py
  ↓
T035 [P] test_synthesizer  |  T036 [P] test_mapper  |  T037 [P] test_failure_detection
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Phase 1: Setup (3 tasks)
2. Phase 2: Foundational (5 tasks)
3. Phase 3: US1 — Weekly briefing (9 tasks)
4. **STOP and VALIDATE**: POST /briefing/generate → see draft in inbox
5. Deploy / dogfood for one week before proceeding

### Incremental Delivery

1. Setup + Foundational → infrastructure ready
2. US1 → briefings in inbox (read-only approval surface — can read but not approve yet)
3. US2 → approval actions live (briefing lifecycle complete)
4. US3 → dependency mapper active (cross-initiative intelligence)
5. US4 → eval suites passing (Phase 3 promotion gate cleared)
6. Polish → code quality + quickstart validation

### Total Task Count

| Phase | Tasks | [P] tasks |
|---|---|---|
| Setup | 3 | 2 |
| Foundational | 5 | 4 |
| US1 (P1) | 9 | 3 |
| US2 (P2) | 4 | 0 |
| US3 (P3) | 6 | 2 |
| US4 (P4) | 10 | 7 |
| Polish | 4 | 2 |
| **Total** | **41** | **20** |
