# Research: Phase 4 — Closed Beta Readiness

**Date**: 2026-05-20
**Branch**: `4-closed-beta-readiness`
**Status**: Complete — all decisions resolved

---

## Static Site Generator (Doc Site)

**Decision**: Docusaurus 3

**Rationale**: The frontend is already React 19 + TypeScript. Docusaurus 3 ships
with a left-nav sidebar that maps cleanly to the three required doc sections
(Getting Started, Concepts, Workflow Reference), full-text local search, and
builds to plain static HTML that deploys anywhere without a server (FR-029).
MDX allows embedding React screenshots where useful.

**Key implementation points**:
- Place at `docs-site/` (separate workspace from `web/`) with its own `package.json`.
- `docusaurus.config.ts` defines three sidebar categories: `Getting Started`
  (FR-026), `Concepts` (FR-027), `Workflow Reference` (FR-028).
- Deploy via GitHub Pages or Cloudflare Pages on every push to `main`; add a
  `docs-site` job to the existing GHA workflow running `npm run build`.
- Operator-facing audience → use the default Docusaurus theme; no custom
  code-block developer themes; prose-first layout with mermaid diagram support.
- `@docusaurus/theme-mermaid` for flow diagrams illustrating the onboarding flow.

**Alternatives considered**: Astro (more flexible but unnecessary complexity for
a small docs site); MkDocs Material (Python-native, simpler, but weaker
versioning and no TypeScript ecosystem fit).

---

## Transactional Email

**Decision**: Resend.com

**Rationale**: Clerk's built-in email templates only cover auth lifecycle events
(magic link, password reset, MFA). It cannot be triggered by application events
like ingest completion. Resend provides a single API key, simple `httpx` async
call, and a free tier covering 3,000 emails/month — far more than the < 100/day
closed-beta volume. The existing `httpx` dependency covers the API call.

**Key implementation points**:
- Add `resend>=2.0` to `pyproject.toml`; add `RESEND_API_KEY: str | None` and
  `RESEND_FROM_EMAIL: str` to `Settings` in `config.py`. When `None`, the
  notification is logged but not sent (safe for local dev).
- Trigger point: `IngestJob.status` transition to `completed` → call
  `notify_ingest_complete(tenant_id, counts)`.
- Retrieve operator email via `clerk_client.users.get(user_id)` (cache per job).
- Subject: `"Your Context-OS data is ready — {N} initiatives found"`.
- Use Resend's `html` parameter with inline-CSS Python string template (no
  React Email server-side rendering needed at closed-beta scale).

**Alternatives considered**: Clerk built-in (cannot trigger on app events);
SendGrid (8–12 MB SDK, excessive for < 100 emails/day).

---

## OTEL Collector + Telemetry Dashboards

**Decision**: Self-hosted OTEL Collector + Prometheus + Grafana in docker-compose

**Rationale**: The platform already runs Langfuse via docker-compose (for LLM
trace storage). Adding three containers (otel-collector, prometheus, grafana)
adds zero new vendors and zero new paid dependencies. Agent failure rates and
ingestion freshness monitoring are metric-query patterns (Prometheus gauges/
counters), not trace-query patterns — Langfuse handles traces, Prometheus handles
operational metrics. They coexist cleanly.

**Key implementation points**:
- Add to `docker-compose.yml`: `otel-collector` (image:
  `otel/opentelemetry-collector-contrib:0.100.0`), `prometheus`
  (`prom/prometheus:v2.52`), `grafana` (`grafana/grafana:10.4`).
  Config files in `docker/otel/`, `docker/prometheus/`, `docker/grafana/`.
- Add `opentelemetry-exporter-prometheus` to `pyproject.toml`; register a
  `PrometheusMetricReader` in `init_tracer()` alongside the existing batch span
  processor. FastAPI exposes `/metrics`.
- **Agent health dashboard**: `rate(context_os_agent_invocations_total{status="error"}[5m])`
  per agent type; alert at > 5% error rate.
- **Ingestion freshness**: gauge `context_os_ingest_last_record_at{source,tenant_id}`;
  alert when `time() - value > 7200` during an active ingest job.
- Langfuse continues to handle LLM trace + eval result storage. No overlap.

**Alternatives considered**: Grafana Cloud (external SaaS, data-residency
question for beta orgs); Honeycomb (trace store, not metric store — second
Langfuse rather than a complement).

---

## Nightly CI Eval Scheduling

**Decision**: GitHub Actions `schedule: cron` workflow

**Rationale**: The project already has GHA workflows. A third file with
`on: schedule: - cron: '0 2 * * *'` costs nothing, appears in the Actions tab,
integrates with branch protection rules to block promotion on regression, and
supports `on: workflow_dispatch: {}` for manual re-runs without waiting for
midnight.

**Key implementation points**:
- `.github/workflows/nightly-eval.yml` with both `schedule` and `workflow_dispatch`
  triggers.
- Start Postgres + Langfuse via `docker compose up -d` as a setup step before
  pytest runs.
- Add pytest marker `@pytest.mark.nightly_eval`; workflow passes `-m nightly_eval`
  so unit and fault tests are not re-run.
- `CI_GPU_AVAILABLE` env var controls graceful degradation: absent → infra-
  dependent fixtures call `pytest.skip(reason="infrastructure-unavailable")`
  (not fail). The overall eval job still passes when only GPU fixtures are skipped.
- Branch protection on `main` uses the `workflow_run` event to gate the merge
  queue on the last nightly eval result.

**Alternatives considered**: Cron container in docker-compose (local-only, no
PR visibility, cannot block promotion).

---

## Onboarding State Machine Persistence

**Decision**: Postgres table `onboarding_sessions` + application-code state machine

**Rationale**: The seven-step flow is fully deterministic and UI-driven — no LLM
decision point, no branching agent reasoning. LangGraph's `AsyncPostgresSaver` is
designed for AI agent workflows and would be a category error here. A plain
`onboarding_sessions` table with `current_step TEXT` enum + `step_data JSONB` +
timestamps gives full leave-and-return resumability via a single
`GET /onboarding/session` endpoint that the React wizard calls on mount.

**Key implementation points**:
- Added to migration `0003_phase4_onboarding.py`.
- `OnboardingService.advance_step(session_id, step, data)` validates legal
  next-step (no skipping), writes `step_completed_at[step]`, updates
  `current_step`. ~40 lines of Python.
- `revert_step(session_id, step)` clears step's timestamp, sets `current_step`
  back. Used by OAuth failure and ingest stall recovery.
- `step_started_at` / `step_completed_at` JSONB dicts feed `ActivationEvent`
  timing segments directly.

**Alternatives considered**: LangGraph (correct for AI workflows; wrong for
deterministic wizard navigation).

---

## OAuth Integration Wizard Pattern

**Decision**: Server-side OAuth flow — popup window + backend callback + session polling

**Rationale**: The `OAuthToken` model (with Fernet-encrypted tokens) already
exists from Phase 1. Phase 4 only adds the flow endpoints. Keeping OAuth server-
side ensures refresh tokens never touch the client, matching the encryption-at-
rest guarantee already in the model.

**Key implementation points**:
- `GET /oauth/connect/{source}/start`: generates server-side PKCE `state`,
  stores in `oauth_pending_sessions` table (10-min TTL), redirects to provider.
- `GET /oauth/connect/{source}/callback`: validates `state`, exchanges code for
  tokens, Fernet-encrypts, upserts `OAuthToken`, updates
  `onboarding_sessions.connected_integrations`, redirects to
  `/onboarding/connect?source={source}&status=success`.
- React wizard opens a popup: `window.open('/oauth/connect/jira/start', ...)`.
  Parent polls `GET /onboarding/session` every 2 seconds; marks card green when
  `connected_integrations` includes the source.
- `oauth_pending_sessions` table added to migration `0003_phase4_onboarding.py`.

**Alternatives considered**: Frontend PKCE (tokens client-side — contradicts
encryption-at-rest guarantee already in the architecture).

---

## Tenant Impersonation Pattern

**Decision**: Backend-issued HS256 impersonation JWT in `X-Impersonation-Token` header

**Rationale**: Clerk issues all production JWTs via RS256 — the backend cannot
add claims to Clerk tokens. The existing auth is entirely stateless (no session
store). An HS256 JWT signed with `IMPERSONATION_SECRET` (new env var) fits
naturally into the `get_current_tenant` dependency with no new infrastructure.

**Key implementation points**:
- `POST /admin/impersonate/{target_clerk_org_id}` (Platform Operator only —
  gated by Clerk custom claim): issues `{ sub, impersonating_tenant_id,
  impersonator: true, jti, exp: now + 1800 }` signed with `IMPERSONATION_SECRET`.
- `get_current_tenant` checks for `X-Impersonation-Token` header; if present,
  verifies HS256 locally and returns `TenantContext(tenant_id=impersonating_tenant_id,
  is_impersonation=True)`.
- All write-path endpoints check `TenantContext.is_impersonation` and return
  `HTTP 403 {"code": "write_blocked_during_impersonation"}`.
- `revoked_impersonation_tokens` table (columns: `jti PK`, `revoked_at`);
  `/admin/impersonate/revoke` records the jti; `get_current_tenant` checks the
  table on each impersonation request.
- Token stored in React memory only (not localStorage) — page refresh ends the
  impersonation session.
- New env vars: `IMPERSONATION_SECRET: str`, `PLATFORM_OPERATOR_CLERK_USER_ID: str`.

**Alternatives considered**: Server session store (requires Redis or new Postgres
session table — contradicts stateless JWT architecture); Clerk JWT tampering
(backend cannot modify Clerk-issued tokens).

---

## New Env Vars Summary

| Var | Required? | Notes |
|-----|-----------|-------|
| `RESEND_API_KEY` | Optional | No-op when absent (logs only) |
| `RESEND_FROM_EMAIL` | Optional | Defaults to `noreply@contextops.ai` |
| `IMPERSONATION_SECRET` | Required for impersonation | 501 when absent |
| `PLATFORM_OPERATOR_CLERK_USER_ID` | Required for admin routes | Gating mechanism |
