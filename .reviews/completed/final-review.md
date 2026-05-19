# Final Branch Code Review — 2-phase-2-intelligence

**Reviewer**: Claude Sonnet 4.6  
**Branch**: 2-phase-2-intelligence  
**HEAD**: 6da500bbf0db389a510b74aa2267e5531875dfe0  
**Date**: 2026-05-18

## Summary

All Critical and High review blockers from the initial review have been resolved. The branch implements Phase 2 intelligence layer: Synthesizer agent, Dependency Mapper agent, executive briefing E2E workflow, human approval inbox, and eval suites.

## Resolved Issues

### CRITICAL
- **eval/mapper_eval.py**: `_compute_recall` numerator fixed — was `ground_truth_count` (identical to denominator, always returning 1.0); now correctly filters `ground_truth_exists AND proposed`.
- **graph/mutations.py**: `promote_dependency_edge` now reads `from_initiative_id`/`to_initiative_id` from approved content (mapper stores these keys, not `from_node_id`/`to_node_id`).
- **api/eval_api.py**: `POST /eval/run` looks up the latest dataset before creating the `EvalRun` record, preventing `NULL` violation against the NOT NULL `dataset_id` column.
- **eval/golden_dataset.py**: `GoldenRecord.proposed` field added (defaults True); `load_dataset` now accepts and passes `tenant_id` to `get_latest_by_type`.

### HIGH
- **workflows/briefing.py**: `resume()` implemented — injects `operator_action` into LangGraph state via `aupdate_state` and resumes the thread via `ainvoke`, completing the Constitution Principle III human governance gate.
- **eval/synthesizer_eval.py**: `AsyncMock` import moved inside patch helper functions (was a top-level production import of a test utility).
- **api/inbox.py**: `operator_id` now uses `tenant.user_id` (Clerk subject from JWT) instead of the client-provided `"system"` default; relational `session.commit()` now happens before AGE graph write.
- **auth/dependencies.py**: `TenantContext.user_id` added, extracted from `payload["sub"]`.
- **relational/repositories.py**: `_assert_tenant_id` guard added to `get_latest_by_type`; zero UUID check extended.

## Verification

- `uv run ruff check src/` — all checks passed
- `uv run pyright src/` — 0 errors, 0 warnings
- `uv run pytest tests/` — 57 passed, 0 failed

## Verdict

**APPROVED** — no outstanding Critical or High issues. Ready for merge to `1-phase-1-foundation`.
