# Spec Review — 36dc7e7

**Commit**: fix(phase4): 3 bugs from code review — migration type, state machine, revoke auth
**Branch**: 4-closed-beta-readiness
**Verdict**: pass for this commit — all three claimed fixes are spec-compliant; pre-existing deviations unchanged

## Fixes Verified

### FIX-1: `post_scope` state machine — SPEC-1 (Resolved)

Two-step loop `("scope", "ingest")` correctly advances session from `connect` → `scope` → `ingest`.

### FIX-2: `connected_integrations` migration type — QUAL-1 (Resolved)

Migration now uses `postgresql.JSONB()` matching the ORM model. No crash risk.

### FIX-3: Revoke endpoint Platform Operator guard — FR-020 (Resolved)

`DELETE /admin/impersonate/revoke` now uses `Depends(require_platform_operator)`.

## Pre-existing Spec Deviations (not introduced by this commit)

- SPEC-2: Scope body uses `sources: list[str]` vs contract's per-source arrays (Confidence 92)
- SPEC-3: Admin funnel missing `time_in_stage` field required by FR-015 (Confidence 88)
- SPEC-4: Drop-off flag uses `updated_at` not `step_started_at[current_step]` (Confidence 85)
- SPEC-5: Write endpoints not guarded by `check_not_impersonation` (Confidence 80)
