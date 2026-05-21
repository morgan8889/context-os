# Final Code Simplification Pass — Phase 4 Closed-Beta Readiness

Branch: `4-closed-beta-readiness`
Date: 2026-05-21

## Scope

Reviewed all 10 designated Phase 4 files for safe, behaviour-preserving
simplifications. Four files received changes; six were already clean and were
left untouched.

## Verification

- **Tests**: `41 passed, 2 failed`. The 2 failures
  (`test_oauth.py::TestOAuthCallback::test_callback_expired_state_returns_400`
  and `test_valid_callback_updates_connected_integrations`) are **pre-existing**
  and unrelated to this pass — they fail identically on the unmodified branch
  HEAD and stem from mock-setup issues in the test file, not in `oauth.py`. No
  new failures were introduced.
- **Type checking**: `pyright` reports `0 errors` on all changed files.
- **Lint/format**: `ruff check` and `ruff format --check` pass on all changed
  files.

Net change: **+49 / -72 lines** across 4 files.

## Files changed

### 1. `src/context_os/auth/dependencies.py`

What was complex: the impersonation header branch created three separate
session factories (`factory`, `factory2`, `factory3`) for sequential lookups,
and caught exceptions with the redundant `except (pyjwt.InvalidTokenError,
Exception)`.

Changes:
- Reused the already-bound `factory` for both impersonation sessions instead of
  creating `factory2` / `factory3` (identical objects — `get_session_factory()`
  returns the same factory each call).
- Simplified `except (pyjwt.InvalidTokenError, Exception)` to `except
  Exception` (`Exception` already subsumes `InvalidTokenError`).
- Removed the now-unused `import jwt as pyjwt`.

Trade-offs: none — behaviour identical, fewer names to track.

### 2. `src/context_os/api/support.py`

What was complex: two endpoints (`get_debug_trace`, `export_debug_trace`)
duplicated an identical ~14-line span-serialisation dict literal, and three
imports (`datetime`, `jwt as pyjwt`, `json`) were declared function-locally.

Changes:
- Extracted `_trace_to_dict(trace)` helper and used it in both trace endpoints,
  removing the duplicated span-serialisation block.
- Hoisted the function-local imports (`json`, `datetime`/`UTC`/`timedelta`,
  `jwt as pyjwt`) to module level.

Trade-offs: none — single source of truth for trace serialisation.

### 3. `src/context_os/api/onboarding.py`

What was complex: `post_activation` defined a defensive `_ts` closure that did
`mapping.get(key) if hasattr(mapping, "get") else None` plus `str(...)`
coercion, guarding against a non-dict that the JSONB columns can never be.

Changes:
- Removed the `_ts` closure; read step timestamps directly via
  `started.get(...)` / `completed.get(...)` after a `or {}` default.
- Widened `_compute_ms` signature to accept `object` (the real type of JSONB
  values) and coerce internally with `str(...)`, so the simplification stays
  fully type-safe under `pyright`.

Trade-offs: `_compute_ms` parameter type is now `object` rather than `str |
None`, which honestly reflects the JSONB-sourced inputs and keeps parsing
guarded.

### 4. `src/context_os/api/oauth.py`

What was complex: `_provider_auth_url` repeated the dev mock-callback URL
literal in four places with hard-coded `source=jira` / `source=github` strings.

Changes:
- Computed `mock_url` once at the top and returned it from every fallback path.
- Collapsed the redundant `if source == "slack"` plus the trailing unknown-
  source return into a single fallback `return mock_url` with a clarifying
  comment.

Trade-offs: none — for the jira/github branches the literal `source=jira` /
`source=github` is provably equal to `source={source}` (the branch only runs
when `source` holds exactly that value).

## Files reviewed, left unchanged (already clean)

- `src/context_os/services/onboarding_service.py` — clear state machine, well-
  documented, idempotent transitions. The `_apply_step_data` "connect → stores
  survey_answer" branch is intentional (survey payload arrives with the connect
  transition); left as-is to avoid behaviour change.
- `src/context_os/services/email_service.py` — straightforward; `_build_html`
  is template assembly that does not benefit from further decomposition.
- `src/context_os/services/ingest_service.py` — `mark_complete` best-effort
  side-effects (email + onboarding advance) are correctly isolated in
  try/except; the inline OnboardingSession lookup is justified (no public
  find-by-tenant method that avoids creating a session).
- `src/context_os/auth/impersonation.py` — concise issue/verify/revoke; nothing
  to remove.
- `src/context_os/api/admin.py` — Pydantic schemas + two PO-only endpoints are
  appropriately structured; the `list_entities` log-and-reraise preserves
  useful failure context.
- `src/context_os/api/admin_funnel.py` — single well-tested helper; clean.
