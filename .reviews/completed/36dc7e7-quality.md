# Quality Review — 36dc7e7

**Commit**: fix(phase4): 3 bugs from code review — migration type, state machine, revoke auth
**Branch**: 4-closed-beta-readiness
**Verdict**: pass for this commit — three prior bugs fixed; one minor new type inconsistency

## Bugs Fixed

- QUAL-1: `connected_integrations` ORM/migration type mismatch — Fixed (JSONB in migration now)
- QUAL-2: `post_scope` state machine no-op — Fixed (two-step loop)
- QUAL-3: `revoke_impersonation` auth — Fixed (require_platform_operator)

## New Issue (introduced by this commit)

### QUAL-4: ORM `Integer` vs migration `BIGINT` for `ActivationEvent` timing columns (Confidence 85)

Migration correctly uses `sa.BIGINT()` but ORM model uses `Integer`. No overflow risk for typical durations (minutes to hours), but type declaration contradicts Postgres schema. Fix: use `BigInteger` in models.py for the four timing columns.

## Pre-existing Issues (not introduced by this commit)

### QUAL-5: `build_funnel_rows` AttributeError for activated tenants (Confidence 90)

Admin funnel SELECT has no JOIN to `activation_events`. Accessing `row.signup_to_connect_ms` on SQLAlchemy Row raises `AttributeError` for any activated tenant → 500 at `GET /admin/funnel`.

### QUAL-6: `post_scope` creates orphaned IngestJob on retry (Confidence 80)

`create_job()` is called unconditionally before step check. Retrying scope creates a new job and orphans the prior one with `status=running` indefinitely.
