# Tasks: Phase 4 — Closed Beta Readiness

**Input**: Design documents from `specs/004-closed-beta-readiness/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/onboarding-api.yaml ✓, quickstart.md ✓

**Tests**: Included — Principle VIII (TDD NON-NEGOTIABLE) requires a failing test to exist before every
deterministic implementation. Tests are written first and observed to fail before the implementation task.

**Organization**: Organized by user story (P1–P6) for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US6 from spec.md)

---

## Phase 1: Setup

**Purpose**: Database migration, config additions, and infrastructure containers for Phase 4.

- [ ] T001 Create Alembic migration `src/context_os/db/migrations/0003_phase4_closed_beta.py` — add tables: `onboarding_sessions` (id UUID PK, tenant_id FK UNIQUE, current_step TEXT, survey_answer JSONB, connected_integrations TEXT[], scope_selection JSONB, ingest_job_id UUID nullable, step_started_at JSONB, step_completed_at JSONB, activated_at TIMESTAMP nullable, created_at, updated_at); `activation_events` (id UUID PK, tenant_id FK UNIQUE, occurred_at, signup_to_connect_ms BIGINT, connect_to_ingest_ms BIGINT, ingest_to_briefing_ms BIGINT, total_active_attention_ms BIGINT, accept_as_is BOOL, created_at); `ingest_jobs` (id UUID PK, tenant_id FK, source TEXT, status TEXT, progress_pct INT, record_counts JSONB, started_at, completed_at nullable, last_record_at nullable, error_detail JSONB nullable, created_at, updated_at); `oauth_pending_sessions` (state TEXT PK, tenant_id UUID FK, source TEXT, code_verifier TEXT, expires_at TIMESTAMP); `revoked_impersonation_tokens` (jti TEXT PK, revoked_at TIMESTAMP); ALTER TABLE tenants ADD COLUMN beta_cohort_id TEXT, ADD COLUMN onboarded_by TEXT; run `uv run alembic upgrade head` and confirm all tables exist

- [ ] T002 [P] Add Phase 4 environment variables to `src/context_os/config.py` Settings class — `resend_api_key: str | None = None`, `resend_from_email: str = "noreply@contextops.ai"`, `impersonation_secret: str = ""`, `platform_operator_clerk_user_id: str = ""`; add corresponding entries to `docker/docker-compose.yml` environment sections and update `.env.example`

- [ ] T003 [P] Add OTEL Collector, Prometheus, Grafana to docker infrastructure — add three services to `docker/docker-compose.yml`: `otel-collector` (image: `otel/opentelemetry-collector-contrib:0.100.0`, ports: 4317/4318, config mount), `prometheus` (`prom/prometheus:v2.52`, port 9090, config mount), `grafana` (`grafana/grafana:10.4`, port 3001, dashboards mount); create `docker/otel/config.yaml` (receive OTLP gRPC+HTTP, export to prometheus remote-write), `docker/prometheus/prometheus.yml` (scrape `otel-collector:8889/metrics` and `app:8000/metrics`), `docker/grafana/provisioning/datasources/prometheus.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Platform Operator auth guard and impersonation write-block — required by US1 admin routes, US3 admin module, and US4 impersonation.

**⚠️ CRITICAL**: Admin and support endpoints cannot be correctly implemented until T004–T005 exist.

- [ ] T004 Add `require_platform_operator()` FastAPI dependency to `src/context_os/auth/dependencies.py` — reads `platform_operator_clerk_user_id` from `Settings`; checks `token_data["sub"] == settings.platform_operator_clerk_user_id`; raises `HTTPException(status_code=403, detail={"code":"not_platform_operator"})` for any other caller; write a failing unit test in `tests/unit/test_auth_dependencies.py` first asserting 403 for a non-PO user and 200 for the PO user, then implement

- [ ] T005 [P] Add `is_impersonation: bool = False` field to `TenantContext` dataclass in `src/context_os/auth/dependencies.py`; add `check_not_impersonation()` dependency that raises `HTTPException(status_code=403, detail={"code":"write_blocked_during_impersonation"})` when `TenantContext.is_impersonation` is True; write failing unit test in `tests/unit/test_auth_dependencies.py` asserting the 403 is raised during impersonation before implementing

**Checkpoint**: Platform Operator guard and impersonation write-block available — user story phases can now begin.

---

## Phase 3: User Story 1 — Workflow-First Onboarding (Priority: P1) 🎯 MVP

**Goal**: A new Strategic Operator completes sign-up → survey → OAuth connect → scope → ingest → first briefing approval in < 30 min active attention, without founder support.

**Independent Test**: Run quickstart.md Scenario 1 end-to-end with a fresh test Clerk org. Confirm `GET /onboarding/session` returns `current_step: activated` after briefing approval and that `activation_events` table has one row for the tenant.

### Backend — TDD (tests before implementations)

- [ ] T006 Write failing unit tests for `OnboardingService` state machine in `tests/unit/test_onboarding_service.py` — cases: `advance_step('survey'→'connect')` succeeds, `advance_step('connect'→'survey')` raises `InvalidTransition`, idempotent re-advance of completed step returns session unchanged, `revert_step('connect')` resets `current_step` to `connect` and clears `step_completed_at['connect']`, `get_or_create(tenant_id)` creates a new session at `survey` if none exists. Run tests — confirm all FAIL before T007.

- [ ] T007 Implement `OnboardingService` in `src/context_os/services/onboarding_service.py` — `get_or_create(tenant_id)`, `advance_step(session_id, step, data)` (validates legal next-step per state machine, writes `step_started_at[step]` if not set, writes `step_completed_at[prev_step]`, updates `current_step`), `revert_step(session_id, step)` (clears `step_completed_at[step]`, sets `current_step` back). Legal transitions: `survey→connect→scope→ingest→briefing→activated`. Run T006 tests — confirm all PASS.

- [ ] T008 [P] Write failing unit tests for `EmailService.notify_ingest_complete` in `tests/unit/test_email_service.py` — mock Resend client; assert: correct subject line `"Your Context-OS data is ready — {N} initiatives found"`, correct recipient (mocked Clerk user email), payload includes `record_counts`; assert no Resend call when `resend_api_key` is None (silent no-op). Run tests — confirm all FAIL before T009.

- [ ] T009 [P] Implement `EmailService` in `src/context_os/services/email_service.py` — `notify_ingest_complete(tenant_id: UUID, counts: dict)`: retrieve operator email via `clerk_client.users.get(user_id)` (cache per call), call Resend API via `httpx` async POST with inline-CSS HTML template; gracefully no-op when `settings.resend_api_key is None`. Run T008 tests — confirm all PASS.

- [ ] T010 Write failing unit tests for `IngestService` in `tests/unit/test_ingest_service.py` — cases: `create_job(tenant_id, source)` returns a new `IngestJob` at status `running`, `update_progress(job_id, pct, counts)` updates `progress_pct` and `record_counts` and sets `last_record_at`, `mark_complete(job_id)` sets `status=completed` and `completed_at`, `mark_stalled(job_id)` sets `status=stalled`, `is_stalled(job_id)` returns True when `last_record_at < now()-2h AND status=running`. Run tests — confirm all FAIL before T011.

- [ ] T011 Implement `IngestService` in `src/context_os/services/ingest_service.py` — `create_job`, `update_progress`, `mark_complete`, `mark_stalled`, `is_stalled`; `mark_complete` also calls `EmailService.notify_ingest_complete` and advances `OnboardingSession` to step `briefing`. Run T010 tests — confirm all PASS.

- [ ] T012 [P] Write failing integration test for OAuth flow in `tests/integration/test_oauth.py` — cases: `GET /oauth/connect/jira/start` creates an `oauth_pending_sessions` row and returns 302, `GET /oauth/connect/jira/callback` with invalid `state` returns 400, callback with expired state returns 400, valid callback updates `onboarding_sessions.connected_integrations`. Use `httpx` async test client with mocked Clerk JWT. Run tests — confirm all FAIL before T013.

- [ ] T013 [P] Implement `/oauth/connect/{source}/start` and `/oauth/connect/{source}/callback` endpoints in `src/context_os/api/oauth.py` — `start`: generate PKCE `state`+`code_verifier`, insert `oauth_pending_sessions` row (expires 10 min), return 302 redirect to provider auth URL (Jira/GitHub/Slack OAuth URLs from `Settings`); `callback`: validate `state` + expiry, exchange code for tokens (mocked in test, real `httpx` call in prod), Fernet-encrypt tokens, upsert `OAuthToken`, update `onboarding_sessions.connected_integrations`, delete `oauth_pending_sessions` row, 301 redirect to `/onboarding/connect?source={source}&status=success`. Run T012 tests — confirm all PASS.

- [ ] T014 Write failing integration test for complete onboarding API flow in `tests/integration/test_onboarding_flow.py` — simulate full sequence: `POST /onboarding/survey`, `POST /onboarding/scope`, poll `GET /onboarding/ingest-status`, `POST /onboarding/activation`; assert session advances correctly at each step, assert `activation_events` row created with non-null timing fields after activation. Run tests — confirm all FAIL before T015.

- [ ] T015 Implement `/onboarding/session`, `/onboarding/survey`, `/onboarding/scope`, `/onboarding/ingest-status`, `/onboarding/activation` endpoints in `src/context_os/api/onboarding.py` — `session`: get-or-create via OnboardingService; `survey`: validate option enum, advance step, persist `survey_answer`; `scope`: validate at least one source selected, create IngestJob via IngestService, advance step; `ingest-status`: return IngestJob for current session; `activation`: validate `briefing_id` exists in Phase 2 briefings table, advance session to `activated`, write `ActivationEvent` with timing segments derived from `step_started_at`/`step_completed_at`, emit OTEL `activation_event` trace. Run T014 tests — confirm all PASS.

### Frontend — TDD (tests before implementations)

- [ ] T016 [P] Write failing unit tests for `useOnboardingSession` hook in `web/tests/unit/onboarding.test.ts` — mock `GET /onboarding/session`; assert: hook returns `currentStep` correctly, returns `isLoading` true during fetch, `mutateAdvance(step, data)` calls `POST /onboarding/survey` (or appropriate endpoint), session is re-fetched after mutation. Run tests — confirm all FAIL before T017.

- [ ] T017 [P] Implement `useOnboardingSession` TanStack Query hook in `web/src/lib/hooks/useOnboardingSession.ts` — `useQuery` on `GET /onboarding/session`; expose `session`, `isLoading`; mutations: `useSurveyMutation`, `useScopeMutation`, `useActivationMutation` each invalidating the session query on success. Run T016 tests — confirm all PASS.

- [ ] T018 Implement `OnboardingShell` in `web/src/onboarding/OnboardingShell.tsx` — calls `useOnboardingSession()` on mount; routes to correct step component based on `session.current_step`; renders a 5-step progress indicator (survey/connect/scope/ingest/briefing) with current step highlighted; shows loading skeleton during initial session fetch; if `current_step === 'activated'` redirects to `/galaxy`

- [ ] T019 [P] Implement `SurveyStep` in `web/src/onboarding/steps/SurveyStep.tsx` — renders `"Which part of your week would you most want to change?"` with 5 option buttons (briefings, dependencies, decision_retrieval, architecture_review_cycle_time, something_else); something_else shows a free-text `<textarea>`; on submit calls `useSurveyMutation`; shows spinner while mutating; forwards to ConnectStep on success

- [ ] T020 [P] Implement `ConnectStep` in `web/src/onboarding/steps/ConnectStep.tsx` — renders 3 OAuth cards (Jira, GitHub, Slack) each with provider icon, one-sentence role description, and "Connect" button; clicking "Connect" opens `window.open('/oauth/connect/{source}/start', 'oauth_{source}', 'width=600,height=700')`; parent polls `GET /onboarding/session` every 2 seconds; marks card green with checkmark when `connected_integrations` includes the source; shows "Skip (not recommended)" link beneath each unconnected card with a warning; "Continue" button enabled when ≥1 source connected

- [ ] T021 [P] Implement `ScopeStep` in `web/src/onboarding/steps/ScopeStep.tsx` — fetches available projects/repos/channels from connected integration APIs (via `GET /api/v1/integrations/{source}/resources`); pre-checks items active in last 90 days; allows multi-select deselection; shows count summary "N projects, M repos, K channels selected"; on confirm calls `useScopeMutation` which POSTs to `/onboarding/scope`

- [ ] T022 [P] Implement `IngestStep` in `web/src/onboarding/steps/IngestStep.tsx` — polls `GET /onboarding/ingest-status` every 5 seconds; shows animated progress bar with `progress_pct`; shows estimated time remaining (derived from elapsed time and pct); shows last-updated timestamp; if user returns to tab and `status === 'completed'` shows completion summary `"Found {initiatives} initiatives, {prs} PRs, {threads} active threads. Drafting your first briefing now."`; if `status === 'stalled'` shows stall recovery UI with retry button (POST to `/api/v1/ingest/retry/{job_id}`); leave-and-return: page restored from session `ingest_job_id`

- [ ] T023 [P] Implement `BriefingStep` in `web/src/onboarding/steps/BriefingStep.tsx` + `OnboardingComplete` in `web/src/onboarding/OnboardingComplete.tsx` — BriefingStep: fetches first briefing via TanStack Query on `GET /api/v1/briefings/{id}`; renders briefing content with inline edit capability; Approve button calls `useActivationMutation` (POST `/onboarding/activation`); on success renders OnboardingComplete; OnboardingComplete: renders activation celebration screen with copy `"You just did in 5 minutes what used to take 60"`, then reveals full nav (Galaxy, Topology, Decisions) via React Router redirect to `/galaxy` after 3-second delay

- [ ] T024 Wire onboarding routes into `web/src/App.tsx` + `web/src/router.tsx` — add route `/onboarding` → `OnboardingShell`; unauthenticated users redirect to Clerk sign-in; authenticated users with no existing onboarding session redirect to `/onboarding` on first load; create `web/src/pages/SignUp.tsx` as a Clerk-mediated sign-up page wrapper that shows transformation thesis copy above the Clerk `<SignUp>` component: `"Right now your weekly briefing takes ~60 minutes to write. Context-OS drafts it in 5 from your Jira / GitHub / Slack; you review and approve."`

- [ ] T025 Write Playwright visual fixtures for onboarding in `web/tests/visual/onboarding.spec.ts` — 9 fixtures: for each viewport `[[1024,768],[1440,900],[2560,1440]]` and step `['survey','connect','scope']`, seed appropriate session state via dev API, navigate to `/onboarding`, wait for stable render, call `expect(page).toHaveScreenshot('onboarding-{viewport}-{step}.png', { maxDiffPixelRatio: 0.02 })`

**Checkpoint**: Full onboarding flow end-to-end functional. Run quickstart.md Scenario 1 to validate.

---

## Phase 4: User Story 2 — Multi-Tenant Data Isolation (Priority: P2)

**Goal**: Zero cross-tenant records returned across all data-read endpoints, verified by automated tests.

**Independent Test**: `uv run pytest tests/integration/test_tenant_isolation.py -v` — all assertions must pass with zero cross-tenant records returned.

- [ ] T026 Write tenant isolation test suite in `tests/integration/test_tenant_isolation.py` — fixture creates Org A and Org B tenants with distinct seed data (separate initiatives, briefings, workflows, decisions); for each data-read endpoint in the API (graph.py, vector.py, briefing.py, inbox.py, mapper.py, onboarding.py, admin.py): call with Org A JWT, assert zero records with `tenant_id == org_b_id` in response; assert same with Org B JWT (zero Org A records); mark all tests `@pytest.mark.nightly_eval` so isolation runs nightly. Run tests — confirm all FAIL (no endpoint-level isolation enforcement to exercise yet — tests should fail by surfacing any gaps), then resolve any gaps found in T027.

- [ ] T027 Audit all existing API endpoints for missing `tenant_id` filter — read `src/context_os/api/ingest.py`, `graph.py`, `vector.py`, `admin.py`, `briefing.py`, `inbox.py`, `mapper.py`, `eval_api.py`; for any query that does not filter by `tenant_id`, add the filter; run `uv run pytest tests/integration/test_tenant_isolation.py` after each fix until all tests pass; document any non-data endpoints (health checks, OAuth callbacks) in the test file as explicitly excluded with rationale.

- [ ] T028 [P] Add tenant isolation test step to `.github/workflows/ci.yml` — add job or step running `uv run pytest tests/integration/test_tenant_isolation.py -q --no-header` that runs on every PR; failure blocks merge; note this is separate from the `@pytest.mark.nightly_eval` tagging (isolation runs both on PR and nightly).

**Checkpoint**: Zero cross-tenant reads on all endpoints. Isolation test suite runs on every PR and nightly.

---

## Phase 5: User Story 3 — Activation Telemetry + Admin Module (Priority: P3)

**Goal**: Platform Operator can view beta org funnel positions, activation timing, and discovery survey responses in an admin surface.

**Independent Test**: Seed 3 orgs at different funnel stages. `GET /admin/funnel` (Platform Operator JWT) returns correct stage, timing, and drop-off flag for each. Non-PO JWT returns 403.

### Backend

- [ ] T029 Write failing unit tests for admin funnel query in `tests/unit/test_admin_funnel.py` — cases: `AdminFunnelQuery.compute(tenant_ids)` returns correct `current_step` for each org, `drop_off_flag=True` when a pre-activated org has been at current step > 48 hours, timing segments populated from `activation_events` for activated orgs, non-activated orgs have `activation_timing=None`. Run tests — confirm all FAIL before T030.

- [ ] T030 Implement `/admin/funnel` endpoint in `src/context_os/api/admin.py` — protected by `require_platform_operator()` dependency; executes the `AdminFunnelRow` SQL query from `data-model.md`; returns `{ "rows": [AdminFunnelRow, ...] }` ordered by `created_at DESC`; add `AdminFunnelRow` Pydantic schema. Run T029 tests — confirm all PASS.

- [ ] T031 [P] Implement `/admin/survey-responses` endpoint in `src/context_os/api/admin.py` — protected by `require_platform_operator()`; queries `onboarding_sessions.survey_answer` joined with `tenants.name`; returns `{ "responses": [{ tenant_id, tenant_name, option, free_text, answered_at }] }` ordered by `answered_at DESC`.

### Frontend

- [ ] T032 [P] Implement admin API client functions in `web/src/lib/api/admin.ts` — `fetchFunnel(): Promise<AdminFunnelRow[]>` (GET /admin/funnel), `fetchSurveyResponses(): Promise<SurveyResponseRow[]>` (GET /admin/survey-responses); TypeScript types for `AdminFunnelRow` (tenant_id, tenant_name, current_step, connected_integrations, drop_off_flag, activated_at, activation_timing) and `SurveyResponseRow`; inject `X-Impersonation-Token` header from `useImpersonation` context when present.

- [ ] T033 Implement `AdminShell` in `web/src/admin/AdminShell.tsx` — checks Clerk custom claim `platform_operator === true` via `useUser()` hook; renders 403 "Not authorized" page for non-PO users; renders admin nav sidebar (Funnel, Survey Responses, Org Detail) and main content area for PO users; wraps all admin routes.

- [ ] T034 [P] Implement `FunnelView` in `web/src/admin/FunnelView.tsx` — TanStack Query `useQuery` on `fetchFunnel()`; renders table with columns: Org Name, Current Step (badge), Connected Integrations (icon chips), Time in Step (relative), Drop-off (⚠️ badge when true), Activated At; rows with `drop_off_flag=true` highlighted with amber background; clicking a row navigates to `/admin/orgs/{tenant_id}`.

- [ ] T035 [P] Implement `SurveyResponsesTable` in `web/src/admin/SurveyResponsesTable.tsx` — TanStack Query `useQuery` on `fetchSurveyResponses()`; renders table with columns: Org Name, Pain Option (badge), Free Text (truncated, expand on click), Answered At; option badges use distinct colors per option value.

- [ ] T036 [P] Implement `OrgDetail` in `web/src/admin/OrgDetail.tsx` — route `/admin/orgs/:tenantId`; shows timing breakdown card (4 segments as horizontal bar segments, each labeled with duration and target), survey answer, connected integrations, ingest job status; "Impersonate" button triggers `POST /admin/impersonate/{tenantId}` and stores returned token via `useImpersonation`; button disabled when `is_impersonation` is already active.

**Checkpoint**: Platform Operator can monitor all beta org activation states and survey data.

---

## Phase 6: User Story 4 — Support Workflows (Priority: P4)

**Goal**: Platform Operator can retrieve + export debug traces and impersonate any tenant (read-only).

**Independent Test**: Run quickstart.md Scenarios 4 and 5. Confirm trace retrieval, redacted export, impersonation write-block, and revocation all function correctly.

### Backend

- [ ] T037 Write failing unit tests for impersonation JWT in `tests/unit/test_impersonation.py` — cases: `issue_impersonation_token(operator_id, target_org_id)` returns a valid HS256 JWT with `impersonating_tenant_id` and `jti` claims, `verify_impersonation_token(token)` returns correct claims, `verify_impersonation_token` raises on expired token, `revoke_impersonation_token(jti)` inserts into `revoked_impersonation_tokens`, `verify_impersonation_token` raises on revoked JTI. Run tests — confirm all FAIL before T038.

- [ ] T038 Implement `src/context_os/auth/impersonation.py` — `issue_impersonation_token(operator_user_id, target_clerk_org_id)`: uses `PyJWT` to issue HS256 JWT with claims `{ sub, impersonating_tenant_id, impersonator: true, jti: str(uuid4()), exp: now+1800 }` signed with `settings.impersonation_secret`; raises `RuntimeError` when `settings.impersonation_secret` is empty; `verify_impersonation_token(token)`: verifies HS256, checks expiry, checks `revoked_impersonation_tokens` table for JTI; `revoke_impersonation_token(jti)`: inserts row. Run T037 tests — confirm all PASS.

- [ ] T039 Implement impersonation endpoints in `src/context_os/api/support.py` — `POST /admin/impersonate/{target_clerk_org_id}`: `require_platform_operator()` guard, calls `issue_impersonation_token`, returns `{ token, expires_at, target_tenant_name }`; returns 501 when `settings.impersonation_secret` is empty; `DELETE /admin/impersonate/revoke`: extracts JTI from `X-Impersonation-Token` header, calls `revoke_impersonation_token`; extend `get_current_tenant` in `src/context_os/auth/dependencies.py` to check for `X-Impersonation-Token` header — if present and valid, set `TenantContext(tenant_id=impersonating_tenant_id, is_impersonation=True)`.

- [ ] T040 [P] Write failing unit tests for debug trace retrieval and redaction in `tests/unit/test_debug_trace.py` — cases: `DebugTraceService.get_trace(operation_id)` returns a `DebugTrace` with spans ordered by `started_at`, `redact_trace(trace)` replaces all spans' raw LLM inputs/outputs with token counts leaving other fields intact, an operation_id not found raises `NotFound`. Run tests — confirm all FAIL before T041.

- [ ] T041 [P] Implement `GET /support/traces/{operation_id}` in `src/context_os/api/support.py` — `require_platform_operator()` guard; `DebugTraceService.get_trace(operation_id)`: queries Langfuse API (or OTEL collector storage) for spans with `operation_id` tag matching `briefing_run_id`, `ingest_job_id`, or `agent_invocation_id`; returns `DebugTrace` with span tree (ordered, parent-child linked); returns 404 when no spans found. Run T040 tests — confirm all PASS.

- [ ] T042 [P] Implement `POST /support/traces/{operation_id}/export` in `src/context_os/api/support.py` — `require_platform_operator()` guard; retrieves trace via `DebugTraceService.get_trace`, calls `redact_trace()` which replaces `input_token_count` and `output_token_count` with actual counts from span attributes and sets `raw_input = null` / `raw_output = null`; returns JSON with `Content-Disposition: attachment; filename="trace-{operation_id}.json"` header.

### Frontend

- [ ] T043 [P] Write failing unit tests for `useImpersonation` hook in `web/tests/unit/impersonation.test.ts` — cases: initial state is `{ token: null, isImpersonating: false }`, `startImpersonation(token)` sets token in memory and `isImpersonating: true`, `endImpersonation()` clears token and calls `DELETE /admin/impersonate/revoke`, hook exposes `isImpersonating` and injects `X-Impersonation-Token` into subsequent API calls. Run tests — confirm all FAIL before T044.

- [ ] T044 [P] Implement `useImpersonation` hook in `web/src/lib/hooks/useImpersonation.ts` — React context + hook; stores token in memory ref (NOT localStorage or sessionStorage); `startImpersonation(token, expiresAt)`: sets token, schedules `endImpersonation` timer at `expiresAt`; `endImpersonation()`: clears token, calls `DELETE /admin/impersonate/revoke` (best-effort, swallow error); expose `isImpersonating: boolean` and `impersonationToken: string | null`; create `ImpersonationContext.Provider` to wrap app in `web/src/App.tsx`; extend axios client in `web/src/lib/api/client.ts` to inject `X-Impersonation-Token` header from context when `impersonationToken` is non-null. Run T043 tests — confirm all PASS.

- [ ] T045 Implement `ImpersonationBanner` in `web/src/admin/ImpersonationBanner.tsx` — renders a fixed top banner (amber background, `position: fixed; top: 0; z-index: 9999; width: 100%`) showing `"Impersonating: {target_tenant_name} — read-only"` and an "End impersonation" button; visible only when `useImpersonation().isImpersonating` is true; clicking "End" calls `endImpersonation()`; add `<ImpersonationBanner />` to `web/src/App.tsx` above all routes; add `data-testid="impersonation-banner"` for Playwright assertions.

**Checkpoint**: Platform Operator can retrieve traces, export redacted bundles, and impersonate tenants read-only.

---

## Phase 7: User Story 5 — Continuous Eval + Telemetry Dashboards (Priority: P5)

**Goal**: Nightly eval catches Synthesizer/Mapper regressions within 24 hours; Grafana shows live agent health and ingestion freshness.

**Independent Test**: Run quickstart.md Scenario 6 (manual nightly eval run). Run Scenario 7 (Grafana dashboard populated). Introduce deliberate Synthesizer regression, re-run, confirm gate fires.

- [ ] T046 Add otel-collector, prometheus, grafana services to `docker/docker-compose.yml`; create `docker/otel/config.yaml` (receivers: otlp gRPC 4317 + HTTP 4318; exporters: prometheusremotewrite to prometheus:9090; service: pipelines); create `docker/prometheus/prometheus.yml` (scrape_configs: job `otel-collector` target `otel-collector:8889`, job `context-os-app` target `app:8000`); create `docker/grafana/provisioning/datasources/prometheus.yaml`; run `docker compose up -d` and verify Grafana accessible at port 3001.

- [ ] T047 Add `opentelemetry-exporter-prometheus` to `pyproject.toml` via `uv add opentelemetry-exporter-prometheus`; in `src/context_os/observability/tracer.py` register a `PrometheusMetricReader` alongside the existing `BatchSpanProcessor`; add `GET /metrics` endpoint to `src/context_os/main.py` returning Prometheus text format; run `curl http://localhost:8000/metrics` and confirm `process_` and any existing OTEL metrics appear.

- [ ] T048 Add Prometheus metric instrumentation — in `src/context_os/agents/base.py` add `context_os_agent_invocations_total` counter (labels: `agent_type`, `status=[success,error]`) incremented after every agent invocation; in `src/context_os/services/ingest_service.py` `update_progress()` method update a `context_os_ingest_last_record_at` gauge (labels: `tenant_id`, `source`) with `time.time()` after each successful record insert; run `curl http://localhost:8000/metrics | grep context_os_` to verify metrics appear.

- [ ] T049 [P] Create Grafana dashboard JSON configs — `docker/grafana/dashboards/agent-health.json`: panel showing `rate(context_os_agent_invocations_total{status="error"}[5m])` per agent_type with alert threshold > 5%; `docker/grafana/dashboards/ingestion-freshness.json`: panel showing `time() - context_os_ingest_last_record_at` per source per tenant with alert threshold > 7200 seconds; add dashboard provisioning config to `docker/grafana/provisioning/dashboards/dashboards.yaml`; import via Grafana REST API or `grafana-cli`; verify dashboards render in Grafana UI.

- [ ] T050 Create `.github/workflows/nightly-eval.yml` — triggers: `on: schedule: [{cron: '0 2 * * *'}]` and `on: workflow_dispatch: {}`; job: `runs-on: ubuntu-latest`; steps: checkout, install uv, `uv sync`, `docker compose -f docker/docker-compose.yml up -d postgres langfuse`, `uv run alembic upgrade head`, `uv run pytest tests/evals/ -m nightly_eval -v --tb=short`; env: `CI_GPU_AVAILABLE: ""` (absent → graceful degradation); on failure: send notification (GitHub annotation sufficient); upload pytest output as artifact.

- [ ] T051 Add `@pytest.mark.nightly_eval` marker to existing eval tests — in `tests/evals/test_synthesizer_eval.py` add `@pytest.mark.nightly_eval` to all test functions; same in `tests/evals/test_mapper_eval.py`; add `markers = ["nightly_eval: marks tests as nightly evaluation gates"]` to `pytest.ini` or `pyproject.toml [tool.pytest.ini_options]`; run `uv run pytest -m nightly_eval --collect-only` and confirm correct tests are selected.

- [ ] T052 [P] Add `CI_GPU_AVAILABLE` graceful degradation to `tests/evals/conftest.py` — add fixture `ci_gpu_available` that checks `os.environ.get("CI_GPU_AVAILABLE")`; update any eval test that depends on GPU-accelerated rendering (Playwright screenshot comparisons used in visual regression only — eval tests do not currently use GPU fixtures, but add the fixture stub and `skipif` decorator pattern for future use); confirm `CI_GPU_AVAILABLE="" uv run pytest tests/evals/ -m nightly_eval` exits 0.

**Checkpoint**: Nightly eval runs on schedule, metrics appear in Grafana, deliberate regression is caught.

---

## Phase 8: User Story 6 — Doc Site (Priority: P6)

**Goal**: A new operator can complete their first 30 minutes using only the doc site.

**Independent Test**: Follow `docs-site/docs/getting-started/01-sign-up.md` through `04-your-first-briefing.md` and reach the integration-connect step in the product without external help.

- [ ] T053 Initialize Docusaurus 3 workspace — from repo root: `npx create-docusaurus@latest docs-site classic --typescript`; update `docs-site/docusaurus.config.ts`: `title: "Context-OS"`, `url: "https://docs.contextops.ai"`, configure three sidebar categories in `docs-site/sidebars.ts`: `Getting Started` (items: 01-sign-up, 02-connect-integrations, 03-scope-selection, 04-your-first-briefing), `Concepts` (items: briefing, initiative, dependency, decision, activation-moment), `Workflow Reference` (items: executive-briefing, dependency-scan, onboarding-flow); install `@docusaurus/theme-mermaid`; add `docs-site/` to top-level `.gitignore` patterns: `docs-site/.docusaurus/`, `docs-site/build/` (not node_modules — that's already ignored); run `npm run build` inside `docs-site/` and confirm it exits 0.

- [ ] T054 [P] Write `docs-site/docs/getting-started/` pages (4 pages) — `01-sign-up.md`: explains transformation thesis, what happens after sign-up (discovery survey), < 800 words, no implementation language; `02-connect-integrations.md`: explains why each integration (Jira/GitHub/Slack) is needed for briefings, how to connect, what partial connection means; `03-scope-selection.md`: explains "which initiatives should your briefing cover", what 90-days-active means, how to deselect; `04-your-first-briefing.md`: explains the wait period, what the completion summary means, how to review/edit/approve, what happens at approval (activation). All pages: prose-first, operator-facing tone, no code blocks, no tech stack references.

- [ ] T055 [P] Write `docs-site/docs/concepts/` pages (5 pages) — `briefing.md`: what a briefing is, how it differs from a report, what "approve" means, < 400 words; `initiative.md`: what an initiative is in the context-OS model, relation to Jira/GitHub entities; `dependency.md`: what a dependency is, how it's detected, why it matters for briefings; `decision.md`: what a decision record is, how decisions are captured; `activation-moment.md`: why activation = first briefing approval (not arrival at a view), what changes after activation (full nav, ongoing briefings). Tone: explain as to a VP of Engineering who is new to the product.

- [ ] T056 [P] Write `docs-site/docs/workflow-reference/` pages (3 pages) — `executive-briefing.md`: step-by-step reference for the Executive Briefing workflow (triggers, ingest inputs, AI drafting, operator review, approval, scheduling); `dependency-scan.md`: step-by-step for the Dependency Scan workflow (trigger, graph traversal, proposed edges, operator approval in inbox); `onboarding-flow.md`: reference diagram of the seven-step onboarding journey with expected time per step and recovery paths. Include mermaid flowchart in `onboarding-flow.md` for the step sequence and recovery branches.

- [ ] T057 Create `.github/workflows/docs.yml` — triggers: `on: push: branches: [main]` and `on: pull_request:`; job `build`: `runs-on: ubuntu-latest`, steps: checkout, `npm ci` in `docs-site/`, `npm run build` in `docs-site/`; job `deploy` (only on `main` push): deploys `docs-site/build/` to GitHub Pages using `actions/deploy-pages@v4`; confirm `npm run build` exits 0 in the workflow.

**Checkpoint**: Doc site builds successfully and all three sections contain readable content.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final verification gates confirming the complete Phase 4 implementation meets spec acceptance criteria.

- [ ] T058 Run full pytest suite — `uv run pytest tests/unit tests/integration -q --no-header --tb=short` — must exit 0; fix any failures before continuing; verify total test count has grown from Phase 3 baseline.

- [ ] T059 [P] Run TypeScript typecheck for web/ additions — `cd web && npm run typecheck` — must exit 0 with zero errors; pay particular attention to: `AdminFunnelRow` and `SurveyResponseRow` types fully typed, `useImpersonation` context type, onboarding step component prop types, all new TanStack Query hooks fully typed with generics.

- [ ] T060 Commit 9 Playwright visual baseline PNGs for onboarding — run `cd web && npm run test:visual -- --update-snapshots -- tests/visual/onboarding.spec.ts` against a seeded local dev server with animations disabled; verify 9 PNG files committed to `web/tests/visual/snapshots/`; add filenames to `web/tests/visual/SNAPSHOTS.md` manifest.

- [ ] T061 Validate SC-001 timing — follow quickstart.md Scenario 1 with a fresh Clerk test org; record wall-clock and active-attention times at each step transition; document in `specs/004-closed-beta-readiness/timing-validation.md`; confirm total active attention < 30 minutes and wall-clock < 24 hours; if timing exceeds thresholds, identify the bottleneck step and file as a follow-up task.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — T001–T003 can start immediately; T001 must complete before any US work touches DB
- **Foundational (Phase 2)**: Requires T001 (migration must exist); T004–T005 must complete before any admin/impersonation endpoint is built
- **US1 Onboarding (Phase 3)**: Requires T001 (migration), T002 (config); backend TDD pairs are mostly sequential within the story; frontend can overlap with backend after T007
- **US2 Isolation (Phase 4)**: Requires T001 (migration); can start in parallel with US1 — T026 isolation test suite can be written while US1 is in progress
- **US3 Admin (Phase 5)**: Requires T001 (activation_events table from T015); requires T004 (PO guard); can start after US1 backend is complete
- **US4 Support (Phase 6)**: Requires T001 (revoked_impersonation_tokens table), T005 (is_impersonation), T002 (impersonation_secret config); can largely start in parallel with US3
- **US5 Eval + Dashboards (Phase 7)**: Requires T001 (docker-compose additions); largely independent of US1–US4; T046–T052 can start at any time after Phase 1
- **US6 Doc Site (Phase 8)**: Fully independent — can start at any time; no backend dependency
- **Polish (Phase 9)**: Requires all user stories complete

### Within-Story TDD Sequencing

Each test-impl pair is strictly sequential: write test → observe fail → implement → observe pass:
- T006 → T007 (OnboardingService)
- T008 → T009 (EmailService) — can parallel with T006/T007
- T010 → T011 (IngestService) — must follow T007 (IngestService calls OnboardingService)
- T012 → T013 (OAuth) — can parallel with T010/T011
- T014 → T015 (Onboarding API) — must follow T007, T011
- T016 → T017 (useOnboardingSession hook) — can parallel with backend
- T037 → T038 (ImpersonationJWT)
- T039 (impersonation endpoints) — must follow T038
- T040 → T041, T042 (DebugTrace) — can parallel with T037/T038
- T043 → T044 (useImpersonation hook) — can parallel with backend
- T029 → T030 (admin funnel query)

### Parallel Opportunities by Phase

**Phase 1**: T002 and T003 can run in parallel after T001 or even independently (different files)
**Phase 2**: T004 and T005 can run in parallel (same file but non-overlapping sections)
**Phase 3 Backend**: T008/T009 (Email) parallel with T006/T007 (OnboardingService); T012/T013 (OAuth) parallel with T010/T011 (IngestService)
**Phase 3 Frontend**: T016/T017 parallel with T019/T020/T021/T022/T023 (all different files); front-end can be developed against mocked API once T015 contracts are defined
**Phase 5**: T031 parallel with T030 (same file, separate endpoints); T032/T034/T035/T036 parallel (different files)
**Phase 6**: T040/T041/T042 (debug trace) parallel with T037/T038/T039 (impersonation); T043/T044 (frontend hook) parallel with T039
**Phase 7**: T049 (Grafana JSON) parallel with T048 (metrics instrumentation); T051 and T052 parallel
**Phase 8**: T054, T055, T056 fully parallel (different doc directories)

---

## Parallel Execution Examples

### Phase 3 Backend (two tracks)

```text
Track A: Core onboarding state machine
  T006 (tests) → T007 (OnboardingService) → T010 (tests) → T011 (IngestService) → T014 (tests) → T015 (API endpoints)

Track B: Email + OAuth (parallel to Track A after T007)
  T008 (tests) → T009 (EmailService)
  T012 (tests) → T013 (OAuthHandlers)
```

### Phase 3 Frontend (after T015 contract is defined)

```text
T016 → T017 (useOnboardingSession)
T018 (OnboardingShell)
T019 [P] (SurveyStep)
T020 [P] (ConnectStep)
T021 [P] (ScopeStep)
T022 [P] (IngestStep)
T023 [P] (BriefingStep)
```

### Phase 7 (all largely independent)

```text
T046 (docker infra) → T047 (metrics reader) → T048 (instrumentation) → T049 [P] (Grafana JSON)
T050 (nightly CI) → T051 → T052 [P]
```

---

## Implementation Strategy

### MVP First (US1 + US2 Only)

1. Complete Phase 1 (Setup) + Phase 2 (Foundation)
2. Complete Phase 3 (US1 — Onboarding Flow)
3. Complete Phase 4 (US2 — Tenant Isolation)
4. **STOP and VALIDATE**: Run quickstart.md Scenarios 1, 2, 3 independently
5. This MVP allows one external org to be onboarded safely

### Incremental Delivery

1. Setup + Foundation → foundation ready
2. US1 (Onboarding) → can onboard one beta org, SC-001 verifiable
3. US2 (Isolation) → can safely add second beta org
4. US3 (Admin) → Platform Operator has visibility into cohort health
5. US4 (Support) → Platform Operator can handle incidents
6. US5 (Eval + Dashboards) → continuous quality gate + live health monitoring
7. US6 (Doc Site) → operators can self-serve without founder

### Suggested Parallel Team Strategy

With two developers:

- **Developer A**: US1 backend (T006–T015), US3 backend (T029–T031), US4 backend (T037–T042)
- **Developer B**: US1 frontend (T016–T025), US2 (T026–T028), US4 frontend (T043–T045), US5 (T046–T052), US6 (T053–T057)

US3 and US4 frontend (T032–T036, T043–T045) overlap and can be distributed based on momentum.

---

## Notes

- **[P]** tasks have different files and no incomplete dependencies — safe to run concurrently
- TDD pairs (T006→T007, T008→T009, etc.) are strictly sequential — test must FAIL before implementation starts
- Every test must be observed to fail before the implementation is written (Principle VIII)
- Commit after each TDD pair (failing test commit + passing implementation commit)
- Stop at each **Checkpoint** to validate story independently before proceeding
- `activation_events.tenant_id` UNIQUE constraint ensures exactly one activation event per org
- The `oauth_pending_sessions` table has no FK cascade — expired rows must be cleaned up in the callback handler (delete by `state`) or by a background periodic query
- All admin endpoints require both Clerk JWT (for PO identity) AND `require_platform_operator()` dependency — do not use one without the other
- `ImpersonationBanner` z-index must be above Sigma canvas and React Flow canvas — use `z-index: 9999`
