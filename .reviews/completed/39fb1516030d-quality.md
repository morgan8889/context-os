# Quality Review — 39fb1516030d

**Commit**: fix(types): safe accessor for JSON column mapping in onboarding activation
**Branch**: 4-closed-beta-readiness
**Verdict**: block — 1 critical bug (ORM type mismatch), 1 important bug (state machine), 1 security gap

## Critical

### QUAL-1: `connected_integrations` ORM/migration type mismatch — production crash (Confidence 90)

Migration creates column as `ARRAY(TEXT)` with `server_default="ARRAY[]::TEXT[]"`. ORM maps it as `JSONB` with `server_default="'[]'::jsonb"`. asyncpg will raise a codec error on every read/write of this column on a real Postgres deployment.

## Important

### QUAL-2: `post_scope` state machine always silent no-op (Confidence 90)

See SPEC-1. `advance_step("ingest")` from "connect" raises `InvalidTransitionError`, silently swallowed. Session step never advances.

### QUAL-3: `revoke_impersonation` not restricted to Platform Operator (Confidence 82)

`DELETE /admin/impersonate/revoke` uses `Depends(get_current_tenant)` — any authenticated user can revoke any impersonation token. Should use `Depends(require_platform_operator)`.

## Commit-Specific Assessment

The `_ts` helper is correct. Defensive `hasattr` guard handles JSONB column deserialization edge cases properly. `_compute_ms` handles `None` inputs and clamps negatives to 0. No regressions introduced by this commit.
