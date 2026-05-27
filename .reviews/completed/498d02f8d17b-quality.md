# Quality Review — 498d02f8d17b

**Commit**: fix(phase4): admin funnel LEFT JOIN, scope idempotency, IngestService.get_job
**Branch**: 4-closed-beta-readiness
**Verdict**: pass — clean, targeted fixes; no new issues introduced

## Changes Verified

**admin.py LEFT JOIN**: `ActivationEvent` import added correctly; `outerjoin()` is the correct SQLAlchemy method for LEFT OUTER JOIN. Timing columns accessed via `ActivationEvent.column` are correctly nullable — `build_funnel_rows` already guards with `if is_activated else None`.

**post_scope idempotency**: `session.ingest_job_id is not None` check is correct (uses identity, not truthiness). `IngestService.get_job()` raises `JobNotFoundError` if the stored UUID is dangling — appropriate behavior; callers should treat this as a 500.

**IngestService.get_job()**: Simple delegation to `_get_job`. Docstring is complete. No risk.

## No Issues Found

All three changes are minimal, correct, and well-scoped. No security, performance, or maintainability concerns.
