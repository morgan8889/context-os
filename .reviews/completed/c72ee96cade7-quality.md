# Code Quality Review — c72ee96cade7

**Commit**: fix(phase4): review fixes — admin entities auth, oauth 302, revoke JTI verification  
**Reviewer**: code-quality  
**Date**: 2026-05-21

## Quality Assessment

### admin.py — GET /admin/entities
- Single-character change: `get_current_tenant` → `require_platform_operator`
- No structural concerns; dependency signature preserved
- **PASS**

### oauth.py — 302 redirect
- Single-value change: `status_code=301` → `status_code=302`
- No structural concerns
- **PASS**

### support.py — revoke impersonation
- `verify_impersonation_token()` is imported inside the function body (avoids circular import)
- The try/except correctly catches all exceptions from token verification and maps to 400
- Session is opened, token verified, JTI revoked, commit happens — all within one session context
- `revoke_impersonation_token` is a clean async call with its own error handling
- **PASS**

### onboarding.py — post_scope two-step advance
- Loop over `("scope", "ingest")` with `pass` on `InvalidTransitionError` is idiomatic
- Handles idempotency cleanly: if already at or past either step, continues without error
- `session.ingest_job_id` assigned before the loop — correct ordering
- **PASS**

### dependencies.py — simplifier cleanup
- Session factory variables consolidated; code is more readable
- No functional changes
- **PASS**

### tests/integration/test_oauth.py — AsyncMock fixes
- `AsyncMock()` is already imported at top of file; no new import needed
- Both test methods fixed consistently
- Assertion updated from `in (301, 302)` to `== 302` — stronger assertion matching actual behavior
- **PASS**

## Test Coverage
- 81 unit + fault tests pass (up from 71; new Phase 4 tests included)
- 4 OAuth integration tests pass (all previously failing tests now green)

## Verdict: PASS
