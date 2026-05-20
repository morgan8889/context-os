# Code Quality Review — 9e79763

**Commit**: `9e79763` feat(phase-2/us1-us4+polish): T009-T040 agents, workflows, evals, API, quality  
**Reviewer**: claude-sonnet-4-6 (automated review agent)  
**Date**: 2026-05-18  
**Verdict**: FAIL

---

## Code Review Findings

### CRITICAL

- [`src/context_os/eval/mapper_eval.py` — `_compute_recall`] Recall metric is always 1.0. The numerator `proposed_true` is computed with an identical expression to the denominator `ground_truth_count` — both count records where `r.ground_truth_exists` is true. The correct numerator must also check `r.proposed` (whether the mapper actually proposed that dependency). As written, the mapper recall CI gate can never fail regardless of mapper output quality. The corresponding test (`test_mapper_metrics_on_golden_dataset`) asserts `recall == 1.0` and passes vacuously, providing no regression protection.

  Fix: Change line to `proposed_true = sum(1 for r in records if r.ground_truth_exists and r.proposed)`.

- [`src/context_os/graph/mutations.py` — `promote_dependency_edge`] Key name mismatch between the mapper agent and the promotion function. `MapperAgent.enqueue_proposals` stores dependency proposals with keys `from_initiative_id` and `to_initiative_id`. `promote_dependency_edge` reads `approved_content.get("from_node_id", "")` and `approved_content.get("to_node_id", "")`. Both will always resolve to `""`. The AGE Cypher `MATCH (a {id: ''})` matches nothing — every approved dependency edge is silently dropped from the canonical graph.

  Fix: Change `promote_dependency_edge` to read `from_initiative_id`/`to_initiative_id`, or change the mapper to use the key names the mutation expects. The fix must be consistent between both files.

- [`src/context_os/api/eval_api.py` — `POST /eval/run`] When the request body omits `dataset_id`, the code passes `dataset_id=None` to `EvalRunRepository.create()`. The `eval_runs.dataset_id` column is `NOT NULL` in the migration. This will raise a `sqlalchemy.exc.IntegrityError` at runtime for any eval run that does not explicitly provide a dataset_id. The spec requires eval runs to be creatable independently; the DB schema must be reconciled (either make the column nullable or require dataset_id in the API schema).

### HIGH

- [`src/context_os/workflows/briefing.py` — `BriefingWorkflow.resume`] The method is a documented no-op. It logs and returns without calling `graph.ainvoke`. The LangGraph `AsyncPostgresSaver` checkpoint stored during `start()` is never used to resume agent execution after a human approval. Constitution Principle III requires that human-gated actions are reversible/auditable/gated — the interrupt-and-resume pattern is the mechanism for this. Storing a `workflow_thread_id` on `ApprovalItem` without ever resuming the thread is misleading and incomplete. `api/inbox.py::approve_item` does not call `resume()` at all.

- [`src/context_os/eval/synthesizer_eval.py` — line 1 import] `from unittest.mock import AsyncMock` is a top-level import in production application code. `unittest.mock` is a test-only module. This import will succeed at runtime but signals incorrect module boundaries — test infrastructure has leaked into the production package. Any dependency scanner or import auditor will flag this. Move the import inside a `TYPE_CHECKING` guard or remove it; the usage site should be in a test file.

- [`src/context_os/relational/repositories.py` — `GoldenDatasetRepository.get_latest_by_type`] `tenant_id` is an optional parameter — when `None`, no tenant filter is applied and the query returns the most recent golden dataset of the given type across all tenants. In a multi-tenant deployment any tenant can read another tenant's golden dataset if they know the type string. Either make `tenant_id` required, or add an explicit guard that raises if `None`.

- [`src/context_os/api/inbox.py` — `operator_id`] The `ApproveRequest` model defaults `operator_id` to `"system"`. The Clerk JWT in the request carries the authenticated user's subject claim (`sub`) which is the operator's Clerk user ID. The approval record in `approval_items.operator_id` should store this, not the literal string `"system"`. This is a governance audit gap — the trail of "who approved this" is lost. Extract `payload["sub"]` from the `TenantContext` or a separate auth dependency and pass it through.

- [`src/context_os/api/inbox.py` — `GET /inbox` pending_count] The pending count is computed as `len(items)` after fetching with `limit=1000`. For tenants with more than 1000 pending items, the reported count will be silently truncated. Use a separate `SELECT COUNT(*)` query for the count, or remove the limit on the count query.

- [`src/context_os/api/inbox.py` — `approve_item` transaction ordering] AGE graph promotion (`promote_briefing_to_artifact` / `promote_dependency_edge`) is called before `await session.commit()`. If the SQLAlchemy commit fails (e.g. transient DB error), the canonical AGE graph has a node/edge for an item that remains `pending` in `approval_items`. There is no compensating transaction or rollback for the AGE write. Recommendation: commit the relational status update first, then write to AGE; if the AGE write fails, mark the item `failed` with an error field.

### MEDIUM

- [`src/context_os/agents/synthesizer/tools.py` — `_retrieve_vector_context`] When `tenant_id` is not a valid UUID, the function catches `ValueError` and returns `[]` silently. Clerk org IDs (e.g. `org_abc123`) are not valid UUIDs. The Synthesizer's `tenant_id` is always a Clerk org ID. This means the vector retrieval tool always returns empty results for the Synthesizer — the vector context section of every briefing is blank. The function should use `db_tenant_id` (the internal DB UUID, available in `BriefingState`) for the pgvector query, not the Clerk org ID.

- [`src/context_os/workflows/dependency.py` — `_active_scans`] The in-memory `set[str]` guard prevents concurrent scans within a single process but provides no cross-process protection. In a multi-worker deployment (e.g. `uvicorn --workers 4`), two requests hitting different workers will both pass the `is_active()` check simultaneously. A DB-level advisory lock or a Redis-backed set is required for reliable mutual exclusion. Acceptable for single-worker dev/staging; must be addressed before multi-worker production.

- [`src/context_os/api/mapper.py` — `POST /mapper/scan` TOCTOU`] The `DependencyWorkflow.is_active(tenant_id)` check and the background task start are not atomic. Two concurrent HTTP requests can both pass the `is_active()` check before either background task has registered the tenant in `_active_scans`. This is a race condition that allows duplicate scans. Acceptable for low-traffic MVP; should be noted for production hardening.

- [`src/context_os/agents/synthesizer/failure_detection.py` — unused module-level variables] Three variables at the bottom of the file serve only to suppress import warnings: `_UNUSED_TIMEDELTA = timedelta`, `_UNUSED_DATETIME = datetime`, `_UNUSED_UTC = UTC`. These are artifacts of removed logic. Remove the unused `timedelta`, `datetime`, and `UTC` imports and the associated assignment statements; add `# noqa: F401` to the import line if the import is genuinely needed for re-export, or delete it.

- [`src/context_os/api/briefing.py` — circular import via `app.state`] `_get_checkpointer()` imports `from context_os.main import app` inside the function body to avoid a circular import. This pattern is fragile — it depends on module load order and will fail if the function is called before `main.py` finishes initializing. The checkpointer should be passed as a FastAPI dependency via `Depends` or retrieved from `request.app.state` using the `Request` object that is already available in the route handler.

- [`src/context_os/api/briefing.py` — `import time` inside function body] `import time` appears inside `_run_briefing_background` at line ~70. Move to top-level imports for consistency with the rest of the codebase.

### LOW

- [`src/context_os/agents/synthesizer/agent.py`] `_emit_agent_span` (inherited from `AbstractAgent`) is called after `await self._graph.ainvoke(...)` returns. The span's `with` block opens and closes in the same statement — the span covers only attribute-setting overhead, not actual agent execution time. This was identified in the `c2ded85` review; it surfaces as an observable issue in this commit because the Synthesizer is the first agent to actually run. Langfuse traces will show 0ms spans for all agent invocations.

- [`src/context_os/agents/mapper/agent.py` — `MapperState` `low_signal` / `data_stale` flags] These fields are declared in the TypedDict but never set by any node in the mapper StateGraph. The `classify_candidates` node populates `proposed_dependencies` but does not evaluate or set signal quality flags. If callers check these flags, they will always be `None` / falsy. Synthesizer equivalent fields are set correctly.

- [`tests/integration/test_approval_flow.py`] All three integration tests use fully mocked repos and AGE pools. They validate the control flow logic (correct mock calls, correct return value inspection) but provide no coverage of the actual SQL statements, AGE Cypher, or FastAPI request handling. These are unit tests with an "integration" label. True integration tests against a test DB would catch the `dataset_id NOT NULL` bug and the AGE key mismatch before production.

- [`tests/evals/test_mapper_eval.py` — `test_mapper_metrics_on_golden_dataset`] The test asserts `assert scores["recall"] == 1.0`. This assertion is trivially true given the broken metric and provides no regression protection. When `_compute_recall` is fixed, this assertion will need to be updated to match the expected value from the golden dataset.

---

## Summary

This commit contains three critical bugs that make the system incorrect at runtime:

1. Mapper recall is always 1.0 (broken CI gate).
2. Approved dependency edges are silently discarded (key name mismatch between mapper output and graph mutation).
3. `POST /eval/run` without a `dataset_id` crashes with an integrity error (NOT NULL violation).

These three issues, combined with the incomplete `BriefingWorkflow.resume()` stub (the human-in-the-loop gate does not resume agent execution), mean the core value proposition of Phase 2 — human-gated AI outputs promoted to the canonical graph — is not fully functional. The dependency graph write path is broken end-to-end.

The synthesizer briefing flow (T009-T018, T020-T021) works correctly modulo the vector search UUID bug. The approval UI flow (T022-T025) works for briefing drafts (since `promote_briefing_to_artifact` has correct key names) but fails for dependency proposals.

**Recommendation**: Block merge. Address all CRITICAL findings and the HIGH `BriefingWorkflow.resume()` finding before re-review.
