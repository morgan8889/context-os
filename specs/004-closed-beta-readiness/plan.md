# Implementation Plan: Phase 4 — Closed Beta Readiness

**Branch**: `4-closed-beta-readiness` | **Date**: 2026-05-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/004-closed-beta-readiness/spec.md`

---

## Summary

Phase 4 makes Context-OS safe and navigable for three to five outside organizations
during closed beta. It ships six independently testable increments:

1. **Workflow-First Onboarding** — a seven-step self-serve activation journey (sign-up
   thesis → discovery survey → OAuth connect → scope selection → ingest → first
   briefing → activation moment) that an outside operator can complete in < 30 minutes
   active attention without founder support.
2. **Multi-Tenant Hardening** — an automated isolation test suite that proves zero
   cross-tenant reads succeed; new Postgres tables are tenant-stamped at insert time.
3. **Activation Telemetry + Admin Module** — a Platform-Operator-only surface showing
   each beta org's funnel position, timing segments, and discovery-survey responses.
4. **Support Workflows** — debug-trace retrieval + export and read-only tenant
   impersonation for the Platform Operator.
5. **Continuous Eval + Telemetry Dashboards** — nightly GitHub Actions eval gate
   (Synthesizer ≥ 40%, Mapper recall ≥ 50%) + Prometheus/Grafana operational
   dashboards (agent health, ingestion freshness).
6. **Doc Site** — Docusaurus 3 static site with Getting Started, Concepts, and
   Workflow Reference sections.

---

## Technical Context

| Dimension | Value |
|-----------|-------|
| **Backend language** | Python 3.12 (Phase 1/2 carry-forward) |
| **Package manager** | uv |
| **Web framework** | FastAPI 0.115+ |
| **ORM** | SQLAlchemy 2.0 async |
| **Graph DB** | Apache AGE 1.5+ via asyncpg |
| **Vector DB** | pgvector 0.7+ |
| **Auth** | Clerk JWT RS256 + backend-issued HS256 impersonation tokens |
| **Email** | Resend.com (`resend>=2.0`) — optional, no-op when unconfigured |
| **Telemetry** | OTEL SDK + Langfuse (existing) + Prometheus + Grafana (new) |
| **Workflow orchestration** | LangGraph (Phase 2 carry-forward, NOT used for onboarding wizard) |
| **Migrations** | Alembic — new `0003_phase4_closed_beta.py` |
| **Testing** | pytest + anyio (existing); `@pytest.mark.nightly_eval` (new) |
| **Frontend language** | TypeScript 5.x strict (Phase 3 carry-forward) |
| **Frontend build** | Vite 6 / React 19 (`web/` workspace) |
| **New frontend areas** | Onboarding flow, Admin panel (`web/src/onboarding/`, `web/src/admin/`) |
| **Doc site** | Docusaurus 3 (`docs-site/` workspace) |
| **CI** | GitHub Actions (existing workflows + new `nightly-eval.yml`) |
| **Target platform** | Local Docker Compose (dev); cloud deploy out of scope for Phase 4 |
| **Constraints** | Admin endpoints require Platform Operator Clerk claim; impersonation blocks all writes; cross-tenant reads must be zero in isolation test suite |
| **Scale** | 3–5 beta orgs; < 100 transactional emails/day; < 10k Prometheus series |

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

### Pre-design check (2026-05-20)

| Principle | Area Touched | Status | Notes |
|-----------|-------------|--------|-------|
| **I. Intent Over Tasks** | Onboarding session tracks the operator's path to their first briefing — a direct outcome expression, not a checklist of setup tasks | ✅ PASS | `OnboardingSession.survey_answer` captures intent context (which workflow pain the operator wants to address); this feeds §9.6 falsification. Discovery survey answer is stored as `{ option, free_text }` — an intent signal, not a task record. |
| **II. Persistent Semantic Memory** | `ActivationEvent`, `OnboardingSession`, `IngestJob` must be persisted in the graph with provenance | ⚠️ SCOPED EXCEPTION | See Complexity Tracking #1. Onboarding and activation records are stored in the relational module (Postgres tables), not the AGE graph. They are operational-metadata records — not the knowledge graph primitives (Goal, Initiative, Decision, etc.) that Principle II governs. The activation moment is captured as an `activation_event` telemetry trace (Principle VI) which satisfies the "facts recorded before considered complete" requirement. The AGE graph is not the right store for ephemeral wizard-state. |
| **III. Human Governance, AI Execution** | Admin module gated to Platform Operator only; impersonation blocks all writes; all agent actions behind approval gate | ✅ PASS | No new AI autonomy introduced in Phase 4. The nightly eval pipeline is deterministic (pytest + golden dataset). Impersonation is read-only by construction. FR-020 enforces write-block during impersonation. |
| **IV. Visualization as Cognition** | Admin funnel view and activation telemetry surface — these are table/list views, not topology-first | ⚠️ SCOPED EXCEPTION | See Complexity Tracking #2. The admin funnel is a secondary operational tool for the Platform Operator (single user), not a primary user-facing topology surface. Principle IV applies to primary interfaces for Strategic/Workflow Operators. Admin and Support surfaces are explicitly secondary detail panes. |
| **V. Evaluation-First** | Nightly eval pipeline runs Synthesizer + Mapper eval suites; Phase 2 agents already have eval suites | ✅ PASS | No new AI agents in Phase 4. Continuous eval hardens existing Phase 2 eval suites into a nightly CI gate. FR-022 requires the gate to block promotion on regression. |
| **VI. Observable Autonomy** | Every ingest job, OAuth flow, and activation event must emit OTEL traces | ✅ PASS | The activation moment is explicitly modeled as an `activation_event` telemetry trace (FR-008). Ingest jobs emit progress spans. Prometheus metrics surfaces agent invocation rates and ingestion freshness (FR-024, FR-025). The `DebugTrace` export redacts LLM content but preserves the full span structure — satisfying the "reconstruct any AI-driven outcome end-to-end" requirement. |
| **VII. Domain-Adapter Extensibility** | Three OAuth sources (Jira, GitHub, Slack) added to the existing adapter layer | ✅ PASS | OAuth tokens stored via the existing `OAuthToken` model (Phase 1). The onboarding wizard's scope selection maps project/repo/channel identifiers to the existing ingestion adapter interfaces. No new core ontology fields introduced. |
| **VIII. Test-Driven Development** | All new deterministic code (OnboardingService, OAuth handlers, impersonation JWT logic, admin queries, Resend email helper) must be test-first | ✅ PASS | Every task that creates deterministic application logic must begin with a failing test. Nightly eval tests for Synthesizer/Mapper were test-first in Phase 2 and are extended here. The isolation test suite (US2) is itself a test-first exercise. |

### Architectural Constraints Check (post-design)

| Constraint | Status | Notes |
|------------|--------|-------|
| Logically polyglot persistence | ✅ PASS | Three new Phase 4 tables (`onboarding_sessions`, `activation_events`, `ingest_jobs`) use the relational module correctly; graph and vector modules are unchanged. |
| Workflow orchestration durable | ✅ PASS | Onboarding wizard uses a Postgres state machine (not in-memory), surviving process restarts. LangGraph is correctly NOT used for the deterministic wizard. |
| Autonomy levels 0–5 only | ✅ PASS | No new AI actions. Existing Phase 2 agents retain their declared levels (Synthesizer L2, Mapper L1/2). |
| OTEL-compatible telemetry | ✅ PASS | Prometheus metrics added via `opentelemetry-exporter-prometheus`; no new non-OTEL telemetry stack. |
| Integration ingestion normalizes to core ontology | ✅ PASS | The three OAuth sources use existing Phase 1 ingestion adapters; no new raw vendor schema leaks. |

---

## Complexity Tracking

| # | Apparent Violation | Why Needed | Simpler Alternative Rejected Because |
|---|-------------------|------------|-------------------------------------|
| 1 | Principle II: `OnboardingSession` / `IngestJob` / `ActivationEvent` stored in relational module, not the AGE graph | These are operational-metadata records (wizard state, job progress), not semantic knowledge-graph primitives. Forcing them into AGE would require Cypher mutations for every wizard step advance — brittle, slow, and semantically wrong (a "current wizard step" is not a node in the organizational memory graph). | Storing in AGE would conflate platform metadata with organizational knowledge, violating Principle VII's domain-agnosticism and making the graph query surface noisy. The activation moment is captured as a telemetry trace (Principle VI), satisfying the auditability requirement without polluting the knowledge graph. |
| 2 | Principle IV: Admin funnel view and support trace view are table/list layouts | Platform Operator is a single power-user; their tooling is operational, not cognitive. The funnel view surfaces stage + drop-off — a sparse numerical table (≤ 5 rows for closed beta) where a topology graph would add zero clarity and significant complexity. | A topology-first admin funnel for 3–5 beta orgs is UI complexity for its own sake. Principle IV explicitly allows "secondary detail panes invoked from a topology surface." The admin module is invoked from the product nav, not presented as a primary surface. |

---

## Project Structure

### Documentation (this feature)

```text
specs/004-closed-beta-readiness/
├── spec.md              ← Feature specification
├── plan.md              ← This file
├── research.md          ← Phase 0 research output
├── data-model.md        ← Phase 1 data model
├── contracts/
│   └── onboarding-api.yaml  ← New API endpoints (OpenAPI 3.1)
├── quickstart.md        ← Phase 1 quickstart scenarios
└── tasks.md             ← Generated by /speckit.tasks (next)
```

### Source Code Layout

```text
# Backend (Phase 4 additions)
src/context_os/
├── api/
│   ├── onboarding.py          # GET/POST /onboarding/session, /survey, /scope, /ingest-status, /activation
│   ├── oauth.py               # GET /oauth/connect/{source}/start|callback
│   ├── admin.py               # GET /admin/funnel, /admin/survey-responses (Platform Operator only)
│   └── support.py             # GET /support/traces/{id}, POST /support/traces/{id}/export
│                              # POST /admin/impersonate/{org_id}, DELETE /admin/impersonate/revoke
├── services/
│   ├── onboarding_service.py  # OnboardingService — state machine advance/revert
│   ├── ingest_service.py      # IngestJob lifecycle (create, update progress, stall detection)
│   └── email_service.py       # notify_ingest_complete() — Resend integration
├── db/
│   └── migrations/
│       └── 0003_phase4_closed_beta.py  # New tables: onboarding_sessions, activation_events,
│                                        # ingest_jobs, oauth_pending_sessions,
│                                        # revoked_impersonation_tokens; add tenant columns
└── auth/
    └── impersonation.py       # Issue/verify/revoke HS256 impersonation JWTs

# Backend tests (Phase 4)
tests/
├── unit/
│   ├── test_onboarding_service.py     # OnboardingService state transitions
│   ├── test_email_service.py          # notify_ingest_complete (mocked Resend)
│   └── test_impersonation.py          # JWT issue/verify/revoke
├── integration/
│   ├── test_onboarding_flow.py        # Full wizard: survey → connect → scope → activation
│   ├── test_tenant_isolation.py       # Cross-tenant read attempts → zero records
│   └── test_admin_routes.py           # Non-PO access → 403; PO access → correct data
└── evals/                             # Extended from Phase 2 (nightly_eval marker)
    ├── conftest.py
    └── test_nightly_gates.py          # Synthesizer accept_rate + Mapper recall gates

# Frontend (Phase 4 additions — within web/)
web/src/
├── onboarding/
│   ├── OnboardingShell.tsx            # Multi-step wizard shell (progress indicator, step routing)
│   ├── steps/
│   │   ├── SurveyStep.tsx             # Discovery survey (one question, five options)
│   │   ├── ConnectStep.tsx            # OAuth wizard (three cards + popup handler)
│   │   ├── ScopeStep.tsx              # Scope selection (project/repo/channel picker)
│   │   ├── IngestStep.tsx             # Ingest progress surface (poll /onboarding/ingest-status)
│   │   └── BriefingStep.tsx           # First briefing review + approve
│   └── OnboardingComplete.tsx         # Activation moment celebration + nav reveal
├── admin/
│   ├── AdminShell.tsx                 # Platform Operator admin wrapper (PO-only guard)
│   ├── FunnelView.tsx                 # Activation funnel table
│   ├── SurveyResponsesTable.tsx       # Discovery survey responses
│   └── OrgDetail.tsx                  # Per-org timing breakdown + impersonation button
└── lib/
    ├── api/
    │   ├── onboarding.ts              # API client for /onboarding/* endpoints
    │   └── admin.ts                   # API client for /admin/* + /support/* endpoints
    └── hooks/
        ├── useOnboardingSession.ts    # TanStack Query wrapper for /onboarding/session
        └── useImpersonation.ts        # Manages X-Impersonation-Token in memory

# Onboarding frontend tests
web/tests/
├── unit/
│   ├── onboarding.test.ts             # OnboardingService state machine (step advance/revert)
│   └── impersonation.test.ts          # useImpersonation hook state
└── visual/
    └── onboarding.spec.ts             # Playwright: 9 fixtures across 3 viewports × 3 steps

# Doc site (new workspace)
docs-site/
├── docusaurus.config.ts
├── sidebars.ts
└── docs/
    ├── getting-started/               # FR-026
    │   ├── 01-sign-up.md
    │   ├── 02-connect-integrations.md
    │   ├── 03-scope-selection.md
    │   └── 04-your-first-briefing.md
    ├── concepts/                      # FR-027
    │   ├── briefing.md
    │   ├── initiative.md
    │   ├── dependency.md
    │   ├── decision.md
    │   └── activation-moment.md
    └── workflow-reference/            # FR-028
        ├── executive-briefing.md
        ├── dependency-scan.md
        └── onboarding-flow.md

# CI (new file)
.github/workflows/
└── nightly-eval.yml                   # schedule: cron + workflow_dispatch; -m nightly_eval
```

---

## Phase 4 Dependency Order

These user stories can be developed mostly independently but have ordering constraints:

```
US2 (Multi-Tenant Hardening) — no dependencies; start immediately
US1 (Onboarding Flow) — requires:
  ├── Migration 0003 (onboarding_sessions, ingest_jobs)
  ├── Existing OAuthToken model (Phase 1) ← already available
  └── Phase 2 briefing API ← already available
US3 (Admin + Activation Telemetry) — requires:
  └── US1 activation_events table ← from US1 migration
US4 (Support Workflows) — requires:
  └── Migration 0003 (revoked_impersonation_tokens) — independent otherwise
US5 (Continuous Eval + Dashboards) — no new backend dependencies;
      extends Phase 2 eval suite; docker-compose additions are independent
US6 (Doc Site) — fully independent; no backend dependency
```

**Safe to start in parallel**: US2 + US5 + US6 + US4 (impersonation logic only)
**Block on US1 migration**: US3

---

## Agent Context Update

The following additions apply to the project's agent context for Phase 4:

| Layer | Technology | Notes |
|-------|------------|-------|
| Email | Resend.com (`resend>=2.0`) | Transactional; optional (no-op when `RESEND_API_KEY` not set) |
| Metrics | `opentelemetry-exporter-prometheus` | Registered alongside existing Langfuse span processor |
| Dashboards | Grafana 10.4 + Prometheus 2.52 | Added to docker-compose; no production cloud dependency |
| OTEL Collector | `otel/opentelemetry-collector-contrib:0.100.0` | Receives OTLP; scrapes Prometheus endpoint |
| Doc site | Docusaurus 3 | Separate `docs-site/` workspace; `npm` only; no Python |
| Impersonation | Backend-issued HS256 JWT | `X-Impersonation-Token` header; `python-jose` or `PyJWT` for signing |
| CI eval | GitHub Actions cron + `workflow_dispatch` | `@pytest.mark.nightly_eval`; `CI_GPU_AVAILABLE` env var gates GPU fixtures |

### Key Patterns (Phase 4)

- **Onboarding state machine**: `OnboardingService.advance_step(session, step, data)` —
  validates legal next step, writes timestamp to `step_completed_at[step]`, updates
  `current_step`. Never skip forward. `revert_step` on failure.
- **Admin guard**: FastAPI dependency `require_platform_operator()` — checks
  `payload["platform_operator"] == true` in Clerk JWT; raises 403 otherwise.
- **Impersonation write-block**: middleware or dependency checks
  `TenantContext.is_impersonation`; any write-path handler that sees it raises
  `HTTP 403 {"code": "write_blocked_during_impersonation"}`.
- **Isolation test pattern**: pytest fixtures create Org A and Org B tenants;
  every data-read endpoint is called with Org A's JWT; assert zero records
  belonging to Org B appear in any response.
- **Nightly eval graceful degradation**: `@pytest.mark.nightly_eval` fixtures check
  `os.environ.get("CI_GPU_AVAILABLE")`; GPU-dependent fixtures call
  `pytest.skip(reason="infrastructure-unavailable")` when absent.
- **Prometheus metrics**: use `from opentelemetry.metrics import get_meter`;
  `meter.create_counter("context_os.agent.invocations", ...)` and
  `meter.create_gauge("context_os.ingest.last_record_at", ...)`.
