# Phase 4 Final Code Review — Branch `4-closed-beta-readiness`

**Reviewer**: Claude Code (claude-sonnet-4-6)
**Date**: 2026-05-21
**Scope**: All Phase 4 additions vs `main` — security, correctness, performance, style.
**Spec source**: `specs/004-closed-beta-readiness/spec.md`

---

## Spec Compliance: 24/29 criteria met

| # | Criterion (FR-) | Status | Test? | Evidence |
|---|-----------------|--------|-------|----------|
| FR-001 | Sign-up transformation thesis, no feature list | PARTIAL | NO | Doc site `01-sign-up.md` present; no product landing page in repo |
| FR-002 | Discovery survey immediately after account creation | YES | NO | `api/onboarding.py:141`, `OnboardingShell` routes to `SurveyStep` |
| FR-003 | Exactly 3 OAuth cards, partial (1/3) sufficient to proceed | YES | NO | `ConnectStep.tsx:119` `canContinue = connected.length >= 1` |
| FR-004 | Scope pre-checks active items; deselect allowed | PARTIAL | NO | Checkboxes present in `ScopeStep.tsx`; "active in last 90 days" filter not implemented in resources endpoint |
| FR-005 | Ingest progress, browser-safe, email on complete | PARTIAL | NO | Progress surface done; email stubbed with empty recipient — see CRITICAL-01 |
| FR-006 | Completion summary with actual counts | YES | NO | `IngestStep.tsx:142–148` |
| FR-007 | First briefing scheduled automatically at day-end | NO | NO | No scheduler wiring; `mark_complete` advances to briefing step but no briefing trigger |
| FR-008 | Activation event emitted on first briefing approval | YES | NO | `onboarding.py:343` creates `ActivationEvent` |
| FR-009 | Non-briefing pain users see forward-reference copy | NO | NO | Not found in `BriefingStep.tsx` |
| FR-010 | Each failure has ≤1-branch recovery path | PARTIAL | NO | OAuth stall handled; ingest stall has retry button; briefing failure shows waiting spinner — no explicit retry action |
| FR-011 | Every record carries tenant ID at ingest time | YES | NO | Existing Phase 1 pattern; Phase 4 new tables all carry `tenant_id` |
| FR-012 | Automated isolation test suite | NO | NO | Not found in `tests/` |
| FR-013 | Self-contained tenant provisioning | YES | NO | Clerk + DB tenant creation flows intact |
| FR-014 | Admin module: PO-only access | YES | YES (unit) | `admin.py:199,261` use `require_platform_operator`; `/entities` endpoint uses only `get_current_tenant` — see HIGH-01 |
| FR-015 | Funnel: stage, time-in-stage, drop-off flag (>48h) | YES | NO | `admin_funnel.py:64` |
| FR-016 | Activation timing 4 segments stored and displayed | YES | NO | `ActivationEvent` model + `onboarding.py:326–341` |
| FR-017 | Survey responses table | YES | NO | `admin.py:260–305` |
| FR-018 | PO retrieves debug trace by ID | YES | NO | `support.py:307` |
| FR-019 | Trace export redacts LLM content | YES | NO | `support.py:354`, `redact_trace()` handles GENERATION spans |
| FR-020 | Impersonation banner + all writes blocked | PARTIAL | NO | Banner done; `check_not_impersonation` dependency exists but must be applied per-endpoint; no middleware-level enforcement — see HIGH-02 |
| FR-021 | Nightly eval pipeline runs automatically | YES | NO | `nightly-eval.yml` |
| FR-022 | accept_rate < 40% OR recall < 50% blocks promotion | PARTIAL | NO | Thresholds in Phase 2 `conftest`; nightly workflow does not check exit code explicitly to block a separate promotion job |
| FR-023 | CI eval degrades gracefully without GPU | YES | NO | CLAUDE.md mentions `CI_GPU_AVAILABLE`; `nightly-eval.yml:33` sets it to empty string |
| FR-024 | Live dashboard: agent failure rates | YES | NO | `agent-health.json` Grafana dashboard provisioned |
| FR-025 | Ingestion freshness monitoring flags stalls >2h | YES | NO | `ingest_service.py:194–212 is_stalled()`, `ingestion-freshness.json` dashboard |
| FR-026–028 | Doc site: Getting Started, Concepts, Workflow Reference | YES | NO | All three sections present in `docs-site/docs/` |
| FR-029 | Doc site statically generated | YES | NO | Docusaurus config present |

---

## Code Review Findings

### CRITICAL

**CRITICAL-01** — `src/context_os/services/ingest_service.py:146`
Email notification always fires with an empty `recipient_email=""`. The `notify_ingest_complete` method does not short-circuit on empty recipient — it checks for `resend_api_key` but then sends the API call with `"to": [""]`. When `RESEND_API_KEY` is set in production this will result in every ingest completion attempting to send email to an empty address, which will produce a Resend API error that silently gets swallowed by the `except httpx.HTTPError` handler. The side effect is: (a) operators never receive completion emails, and (b) every `mark_complete` call incurs an unnecessary HTTP round-trip to Resend. The recipient email must be looked up from the tenant record before `notify_ingest_complete` is called.

**CRITICAL-02** — `src/context_os/api/support.py:282–289`
The `revoke_impersonation` endpoint decodes the token **without signature verification** to extract the JTI, then inserts that JTI into the blocklist. An attacker (or any authenticated user, since the endpoint only requires `require_platform_operator`) can craft a token with an arbitrary JTI and submit it, poisoning the blocklist with fake JTIs. Because the blocklist is a permanent append-only table, this is a low-rate denial-of-service against future legitimate tokens whose UUIDs collide with injected ones (extremely unlikely but structurally unsound). More critically, a compromised operator account could pre-revoke tokens before they are issued. The fix is to verify the token signature before extracting the JTI, exactly as `verify_impersonation_token` does.

---

### HIGH

**HIGH-01** — `src/context_os/api/admin.py:102–152` — `GET /entities` missing PO guard
The `list_entities` endpoint uses `get_current_tenant` (any authenticated tenant) rather than `require_platform_operator`. This endpoint queries the AGE graph and returns all graph nodes for the requesting tenant, which is correct for a tenant-scoped view, but its placement in the `admin` router and its docstring say "Admin API endpoints", and the spec (FR-014) states the admin module MUST be accessible ONLY to the Platform Operator. Any beta tenant could call `/admin/entities` and browse their own graph data through the admin surface. Depending on how the frontend routes are gated, this may also inadvertently expose the `/admin` prefix to non-PO users. The dependency should be changed to `require_platform_operator` or the endpoint should be moved to a non-admin router prefix.

**HIGH-02** — `src/context_os/auth/dependencies.py:214–232` — Write-block is opt-in, not enforced globally
`check_not_impersonation` is a FastAPI dependency that endpoints must explicitly declare. Per the spec (FR-020) ALL write operations MUST be blocked during impersonation. However, any write endpoint that omits `Depends(check_not_impersonation)` from its signature silently allows writes during impersonation. There is no middleware-level enforcement. Review of `onboarding.py` and `oauth.py` shows `post_survey`, `post_scope`, `post_activation`, and `oauth_callback` all use only `get_current_tenant` with no impersonation write-block. A PO impersonating an org could mutate the org's onboarding state. The safest fix is a middleware or router-level dependency that applies `check_not_impersonation` to all non-GET routes rather than relying on per-endpoint declaration.

**HIGH-03** — `src/context_os/api/oauth.py:70–73` — OAuth redirect_uri is a relative path, invalid per RFC 6749
The Jira OAuth redirect_uri is constructed as `&redirect_uri=/oauth/connect/jira/callback`. OAuth 2.0 (RFC 6749 §3.1.2) requires redirect URIs to be absolute URIs. Atlassian's authorization server will reject this. The full base URL of the application must be included (e.g., `https://app.contextops.ai/oauth/connect/jira/callback`). This is a protocol-level correctness bug that will cause all Jira OAuth flows to fail silently with a provider error once a real `jira_client_id` is configured. A `base_url` setting should be added to `config.py` and used here.

**HIGH-04** — `src/context_os/services/onboarding_service.py:201` — Survey data saved under wrong step key
In `_apply_step_data`, the condition is `if step == "connect" and "option" in data:` — but `advance_step` is called with `step="connect"` and `data={"option": ..., "free_text": ...}` (the survey answer). The data is stored correctly on `session.survey_answer`, however the guard checks `step == "connect"` rather than `step == "connect"` *because that is when the survey is being transitioned from* — this is semantically confusing but functionally correct because the `advance_step` is called with `"connect"` as the target step and the survey data. However, line 201's comment is misleading and the step label is wrong: "connect" is the destination step, not "survey". This will cause the `survey_answer` to be lost if someone calls `advance_step(..., "connect", data)` without the `"option"` key — the else-branch silently does nothing. **More importantly**: a retry call to `post_survey` after a session is already past `survey` will hit `InvalidTransitionError`, then check `session.current_step != "survey"` and return the existing session without re-saving the new survey answer. If the operator changes their survey answer on retry, the change is silently discarded. (MEDIUM severity on the retry case; HIGH on the overall fragility.)

**HIGH-05** — `src/context_os/api/oauth.py:301` — OAuth callback uses HTTP 301 (permanent redirect)
`oauth_callback` returns `RedirectResponse(url=..., status_code=301)`. HTTP 301 is a permanent redirect; browsers cache it. If the callback URL or success URL ever changes, users with a cached 301 will be silently routed to the old location. The correct status code for a post-OAuth callback redirect is 302 (Found/temporary). The `oauth_start` endpoint correctly uses 302; this is an inconsistency and a correctness bug.

---

### MEDIUM

**MEDIUM-01** — `src/context_os/auth/dependencies.py:148–188` — Three separate DB sessions opened in one request
`get_current_tenant` opens up to three independent sessions (lines 112–113, 150–152, 167–169) within a single FastAPI dependency call: one for the normal Clerk JWT tenant lookup, one for the impersonation token revocation check, and one for the impersonated tenant lookup. Each opens and closes via `async with factory() as session`. While not incorrect, this adds two extra connection checkouts from the pool per impersonated request. A single session should be opened at the top and passed to both `verify_impersonation_token` and the follow-up repo query.

**MEDIUM-02** — `src/context_os/api/admin.py:283` — Raw `text()` ORDER BY with JSONB path injection surface
The `get_survey_responses` query uses `text("(onboarding_sessions.step_completed_at->>'survey') DESC NULLS LAST")` as an ORDER BY clause. The table name is hardcoded, not user-supplied, so there is no injection risk here. However, this is brittle: if the table is renamed (e.g., during a schema migration), the string literal will silently fail or produce a runtime error. The ORDER BY should use SQLAlchemy column expressions, e.g. `OnboardingSession.step_completed_at["survey"].as_string().desc()`.

**MEDIUM-03** — `src/context_os/api/onboarding.py:175` — `advance_step` called with wrong step name, suppressed by `type: ignore`
`svc.advance_step(session.id, "connect", data)` has a `# type: ignore[arg-type]` comment. The `advance_step` signature accepts `step: str` (not a `Literal`), so the ignore is puzzling — likely suppressing a Pyright narrowing warning about the `data` dict type. Regardless, the suppression masks any future type errors on this call site and should be resolved properly.

**MEDIUM-04** — `src/context_os/services/ingest_service.py:30–31` — Module-level OTEL meter creation
`_meter = metrics.get_meter("context_os")` and `_last_record_gauge = _meter.create_gauge(...)` execute at module import time. If `ingest_service` is imported before the `TracerProvider` / `MeterProvider` is initialized (e.g., in tests or during Alembic migration runs), this silently creates a no-op meter rather than raising. This is not a crash risk, but it means the gauge will silently produce no metrics in environments where the service module is imported early. The meter should be created lazily or inside the FastAPI lifespan.

**MEDIUM-05** — `src/context_os/api/onboarding.py:212` — Source list joined as a comma-delimited string
`source = ",".join(body.sources) if len(body.sources) > 1 else body.sources[0]` produces a string like `"jira,github,slack"` stored as the `source` column in `ingest_jobs`. The model docstring says `"jira | github | slack | all"` (pipe-delimited). The `is_stalled()` and other service methods read `job.source` but do not parse it, so the multi-source case is treated as an opaque label. If any downstream code splits on `|` or tries to match against the documented values, it will fail. The format should match the docstring, or the model should use a list/JSONB column.

**MEDIUM-06** — `web/src/onboarding/steps/BriefingStep.tsx:88–93` — Fallback fetches briefing by `ingest_job_id`
The BriefingStep fallback path calls `/api/v1/briefings/${session.ingest_job_id}` — using an IngestJob UUID as a briefing ID. There is no endpoint that maps an ingest job ID to a briefing. This will always return a 404 in production. The only valid briefing-fetch path is through the inbox (`/api/v1/inbox`). The fallback branch is dead code that will confuse users with an "error" when it hits the 5-retry cap.

**MEDIUM-07** — `docker/docker-compose.yml:26–27,36,80` — Hardcoded weak secrets in compose file
`NEXTAUTH_SECRET: changeme-nextauth-secret-32chars!!`, `SALT: changeme-salt-value-here`, `LANGFUSE_INIT_USER_PASSWORD: changeme123`, `GF_SECURITY_ADMIN_PASSWORD: admin`. These are development defaults. The risk is that these values get copy-pasted into a staging/production `.env` without replacement, since compose files are often used directly for beta deployments. Each should be replaced with an env var reference (e.g., `${LANGFUSE_NEXTAUTH_SECRET}`) and a corresponding entry in `.env.example` with a clear "CHANGE THIS" comment.

**MEDIUM-08** — `src/context_os/config.py:138–141` — `impersonation_secret` has no minimum-length validator
The `impersonation_secret` field defaults to `""`. The check in `issue_impersonation_token` is a runtime guard (`if not settings.impersonation_secret: raise RuntimeError`), but this check is bypassed by `verify_impersonation_token` which calls `jwt.decode` with an empty string as the key — PyJWT will accept this and produce a technically valid HS256 JWT signed with an empty secret. A `field_validator` should enforce a minimum length (e.g., 32 bytes) at startup, consistent with the `encryption_key` validator pattern.

---

### Informational (not blocking)

- `nightly-eval.yml:20` uses `sleep 15` instead of a proper `pg_isready` poll loop; fragile on slow CI runners.
- `IngestStep.tsx:35` — `useElapsed` returns a stale value because it is wrapped in `useMemo` with `[startedAt]` as the sole dependency; the value won't update every second. An interval-based hook is needed for a live elapsed timer.
- `web/src/admin/FunnelView.tsx:70–75` — `relativeTime` accepts `seconds` but the API returns values in milliseconds (column is `*_ms`). The `OrgDetail` component also renders `time_in_current_step_seconds` but `AdminFunnelRow` from the API client does not have this field — it is a frontend-only computed field that needs to be derived from `updated_at`, which is not present in the API response shape.
- `src/context_os/api/oauth.py:32–45` — `_encrypt_mock_token` is used in production `oauth_callback`. The name `mock` signals this is a placeholder. In production with a real provider, this function would need to exchange the `code` for a real token via the provider's token endpoint.

---

## Recommendation: REQUEST CHANGES

**Blocking issues** (must fix before first external org is onboarded):

1. **CRITICAL-01**: Email notification fires with empty recipient — operators will never get the completion email, and every `mark_complete` call silently fails against Resend in production.
2. **CRITICAL-02**: Revoke endpoint accepts unverified tokens — JTI blocklist can be poisoned by any PO-authenticated caller.
3. **HIGH-01**: `/admin/entities` accessible to any tenant — admin surface bypass.
4. **HIGH-02**: Write-block during impersonation is opt-in — FR-020 compliance gap; write endpoints in `onboarding.py` and `oauth.py` are unguarded.
5. **HIGH-03**: Jira OAuth redirect_uri is a relative URL — all Jira OAuth flows will fail with a real `jira_client_id`.
6. **HIGH-05**: `oauth_callback` returns HTTP 301 (permanent) instead of 302 — browser caching will break future redirects.

**Should fix before beta launch** (degrade silently but affect beta experience):

7. **HIGH-04**: Survey data silently discarded on retry when survey answer changes.
8. **MEDIUM-06**: BriefingStep fallback dead code path — will 404 and confuse users at retry cap.
9. **MEDIUM-07**: Hardcoded compose secrets need env var references before any production/staging use.
10. **MEDIUM-08**: `impersonation_secret` empty string is not caught at startup validation.
