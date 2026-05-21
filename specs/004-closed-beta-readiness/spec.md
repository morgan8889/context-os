# Feature Specification: Phase 4 — Closed Beta Readiness

**Feature Branch**: `4-closed-beta-readiness`
**Created**: 2026-05-20
**Status**: Draft
**Source**: docs/prd.md §8.3.9, §8.6, §9.5, §10 Phase 4 scope

## Overview

Phase 4 hardenes Context-OS for contact with three to five outside organizations.
It adds the activation story (Workflow-First onboarding), makes multi-tenant data
isolation provably correct, surfaces telemetry and admin tooling for the Platform
Operator, establishes continuous-eval infrastructure, and publishes a doc site so
new operators can succeed without founder support.

The guiding frame: every outside organization that stalls or drops off in week 1
is a falsification of the MVP thesis. This phase exists to validate that the product
can onboard, activate, and retain beta operators without founder intervention.

---

## User Scenarios & Testing

### User Story 1 — Workflow-First Onboarding (Priority: P1)

A new Strategic Operator discovers Context-OS, signs up, connects their three
source integrations (Jira, GitHub, Slack), scopes their first briefing, waits for
ingest to complete, reviews and approves their first AI-drafted briefing, and
arrives at a populated operational intelligence surface — all without contacting
support.

**Why this priority**: This is the activation moment. Without it, no beta org
reaches value. Every other Phase 4 capability is worthless if operators cannot
activate.

**Independent Test**: A net-new test account can complete sign-up → integration
connect → scope selection → ingest → first briefing approval without any
founder/support intervention. Timer from sign-up email click to activation approval
must be < 30 minutes active attention and < 24 hours wall-clock.

**Acceptance Scenarios**:

1. **Given** a prospect lands on the sign-up page, **When** they read the hero section, **Then** they see a plain-language transformation thesis ("Right now your weekly briefing takes ~60 minutes to write. Context-OS drafts it in 5 from your Jira / GitHub / Slack; you review and approve.") — no feature list.

2. **Given** a new account is created via Clerk sign-up, **When** the operator enters the product for the first time, **Then** they are immediately presented with a single-question discovery survey ("Which part of your week would you most want to change?") with five options (briefings, dependencies, decision retrieval, architecture-review cycle time, something-else free-text).

3. **Given** the discovery survey is answered, **When** the operator proceeds, **Then** they see an integration wizard with exactly three OAuth cards (Jira, GitHub, Slack) framed as workflow-inputs, each with a one-sentence explanation of why it is needed for their briefing.

4. **Given** at least one integration is connected, **When** the operator proceeds, **Then** they see a scope-selection screen titled "Which initiatives should your briefing cover?" pre-checking all projects/repos/channels active in the last 90 days; they can deselect without breaking the flow.

5. **Given** scope is confirmed, **When** ingest begins, **Then** the operator sees a progress surface with estimated time, can safely close the browser, and receives an email notification on completion.

6. **Given** ingest completes, **When** the operator returns, **Then** they see a completion summary ("Found {N} initiatives, {M} PRs, {K} active threads. Drafting your first briefing now.") and a scheduler that confirms the briefing will be ready by end of day.

7. **Given** the first briefing is generated, **When** the operator opens it, **Then** they can review the full content, make edits, and approve it; approval emits an activation telemetry event and reveals the full nav (Galaxy, Topology, Decisions).

8. **Given** an operator selected a non-briefing pain in the discovery survey, **When** the briefing is presented, **Then** forward-reference copy appears: "You picked {X}. We're starting with briefings. Here's where {X} sits." with a single-line roadmap reference.

9. **Given** any step fails (OAuth rejection, ingest stall > 30 minutes, briefing generation failure), **When** the operator returns to that step, **Then** they see a specific, actionable recovery path — not a generic error — and the path has at most one additional decision branch.

---

### User Story 2 — Multi-Tenant Data Isolation (Priority: P2)

A Platform Operator can add a second beta organization to the system with the
certainty that its data is completely isolated from all other tenants — verified
by automated tests that deliberately attempt cross-tenant reads.

**Why this priority**: A single cross-tenant data exposure during closed beta
ends the company. This must be provably correct before any external org is
onboarded.

**Independent Test**: Run the isolation test suite against a two-tenant seed;
zero cross-tenant reads must succeed. Admin surfaces must refuse to display data
from a tenant the requesting operator does not belong to.

**Acceptance Scenarios**:

1. **Given** two organizations (Org A and Org B) are both active tenants, **When** any data read is performed on behalf of Org A, **Then** zero records belonging to Org B are returned, including in graph queries, vector searches, briefing history, and approval inbox.

2. **Given** a Platform Operator uses the admin impersonation feature to view Org A, **When** they switch to Org B, **Then** all views refresh entirely to Org B data; no Org A data is visible or accessible.

3. **Given** a new tenant is provisioned, **When** they connect integrations, **Then** all ingested records are stamped with the tenant's identifier and cannot be queried without it.

---

### User Story 3 — Activation Telemetry + Admin Module (Priority: P3)

A Platform Operator can open an admin surface that shows, for each beta
organization: where they are in the onboarding funnel, when they activated
(approved their first briefing), and the raw activation timing breakdowns — all
visible only to the Platform Operator persona.

**Why this priority**: Without this surface, the Platform Operator is flying
blind on beta cohort health and cannot intervene before an org drops off.

**Independent Test**: Seed three orgs at different funnel stages. Confirm the
admin funnel view shows each at the correct stage, and that activation timing
data appears on the org that has activated.

**Acceptance Scenarios**:

1. **Given** a Platform Operator opens the admin module, **When** they view the activation funnel, **Then** they see every beta org as a row with their current funnel stage (sign-up, integration-connect, ingest, first-briefing, activated), time-in-stage, and drop-off flag if > 48 hours at any pre-activation stage.

2. **Given** an org activates, **When** the Platform Operator views that org's row, **Then** activation timing breakdowns are visible: time from sign-up to connect, connect to ingest-complete, ingest-complete to first-briefing approval, and total active attention.

3. **Given** an org completed the discovery survey, **When** the Platform Operator views the survey-responses table, **Then** they see each org's chosen pain option and any free-text from "something-else."

4. **Given** a non-Platform-Operator attempts to access the admin module, **When** the request is evaluated, **Then** the response is a permission-denied state, not an error page revealing internal information.

---

### User Story 4 — Support Workflows (Priority: P4)

A Platform Operator can handle a support request from a beta org without needing
direct database access: they can view a debug trace for a specific operation, export
it, and impersonate the affected tenant to reproduce the issue.

**Why this priority**: Beta orgs will have issues. Without lightweight support
tooling, the Platform Operator loses hours per incident to raw log triage.

**Independent Test**: Simulate a briefing-generation failure for Org A. Confirm
the Platform Operator can retrieve the failure trace, export it, and view Org A's
inbox as if they were that operator.

**Acceptance Scenarios**:

1. **Given** a support request names a specific operation (e.g., a briefing run ID), **When** the Platform Operator opens the debug-trace view for that ID, **Then** they see the full span tree: agent calls, tool invocations, LLM inputs/outputs (redacted to token counts), latency per step, and the failure location.

2. **Given** the Platform Operator wants to share a trace externally, **When** they click export, **Then** they receive a structured export bundle (spans + metadata) with all LLM inputs/outputs redacted; no raw prompt content leaves the system.

3. **Given** the Platform Operator activates tenant impersonation for Org A, **When** they navigate any product surface, **Then** they see exactly what the Org A operator sees; a persistent banner indicates impersonation is active; all write operations are blocked during impersonation.

---

### User Story 5 — Continuous Eval + Telemetry Dashboards (Priority: P5)

Every night, the CI system runs the intelligence evaluation suite against the
golden dataset. A regression in Synthesizer accept rate or Mapper recall triggers
an alert that blocks the next promotion to main. The Platform Operator has a
live dashboard showing agent failure rates and ingestion freshness.

**Why this priority**: Phase 2 established the eval framework; Phase 4 makes it
a nightly gate so regressions are caught within 24 hours, not at the next demo.

**Independent Test**: Introduce a deliberate regression in the Synthesizer prompt.
Confirm the nightly eval catches it and the promotion is blocked. Confirm the
telemetry dashboard reflects the failure within the observation window.

**Acceptance Scenarios**:

1. **Given** nightly eval runs complete, **When** the Synthesizer accept rate drops below 40% or Mapper recall drops below 50%, **Then** the promotion pipeline is blocked and a notification is sent to the Platform Operator.

2. **Given** the telemetry dashboard is open, **When** agent failure rates spike above baseline, **Then** the alert surface updates within the observation window and the affected agent is highlighted.

3. **Given** an ingestion source stalls (no new records for > 2 hours during active ingest), **When** the Platform Operator views the ingestion-freshness panel, **Then** the stalled source is flagged with the time since last successful record.

---

### User Story 6 — Doc Site (Priority: P6)

A new Strategic Operator can complete their first 30 minutes with Context-OS
using only the doc site — no Slack DM to the founder required.

**Why this priority**: Supports the self-serve activation thesis. Even if
in-product copy is excellent, some operators will seek external documentation.

**Independent Test**: A net-new user follows the getting-started guide from the
doc site and reaches the integration-connect step in the product without any
external help.

**Acceptance Scenarios**:

1. **Given** an operator is at the integration-connect step and is unsure why Slack is required, **When** they open the doc site, **Then** the "Getting Started" page explains each integration's role in plain language in < 200 words.

2. **Given** an operator wants to understand what a "briefing" is, **When** they search or navigate the doc site, **Then** they find a concepts page that explains briefings, their relation to the operator's workflow, and how approval works — without assuming any product knowledge.

---

### Edge Cases

- An operator completes sign-up but never answers the discovery survey (browser closed mid-flow). On return, they are taken back to the discovery survey step, not to the beginning.
- An OAuth connection is rejected by the provider (expired credentials, scope denied). The specific provider shows a re-connect prompt; other already-connected providers retain their status.
- Ingest stalls because the Jira project contains 0 issues in the last 90 days. The completion message reflects the actual count ("Found 0 initiatives from Jira") and the scope-selection screen is shown again with a warning.
- A second user from the same org attempts the onboarding flow. The system detects the org already has an active operator and routes the second user to the existing operator surface, not the onboarding flow.
- The first briefing generation fails. The operator sees a specific failure message ("We couldn't generate your briefing — here's what we tried") and a single retry action. The retry uses the same ingest data; no re-ingest required.
- A Platform Operator's impersonation session is active when the impersonated org's operator logs in simultaneously. The Platform Operator's view is a read-only snapshot; the real operator's session takes precedence for any in-flight actions.
- The golden dataset nightly eval runs but the CI system has no GPU access. The eval degrades gracefully: LLM-dependent metrics still run (they use the CPU-based API), only the frame-render timing fixtures are marked as "infrastructure-unavailable" rather than "fail."

---

## Requirements

### Functional Requirements

**Onboarding Flow**
- **FR-001**: The sign-up page MUST present the transformation thesis in plain language (before/after format) with no feature list.
- **FR-002**: The system MUST present a single-question discovery survey immediately after account creation; the answer MUST be captured per organization and persisted.
- **FR-003**: The integration wizard MUST offer exactly three OAuth cards (Jira, GitHub, Slack); partial connection (1 of 3) MUST be sufficient to proceed with explicit per-source warnings.
- **FR-004**: The scope-selection screen MUST pre-check projects/repos/channels active in the last 90 days; operators MUST be able to deselect without blocking forward progress.
- **FR-005**: The ingest progress surface MUST show estimated time, allow the operator to leave and return safely, and send an email notification on completion.
- **FR-006**: The completion summary MUST show actual counts of discovered initiatives, PRs, and active threads before scheduling the first briefing.
- **FR-007**: The first briefing MUST be scheduled automatically at end of the ingest-completion day using the first-run briefing variant.
- **FR-008**: Approval of the first briefing MUST emit an activation telemetry event and MUST reveal the full navigation surface (Galaxy, Topology, Decisions).
- **FR-009**: Operators who selected a non-briefing pain in the discovery survey MUST see contextual forward-reference copy alongside their first briefing.
- **FR-010**: Every onboarding step (OAuth failure, ingest stall, briefing failure) MUST have a documented recovery path with at most one decision branch.

**Multi-Tenant Hardening**
- **FR-011**: Every data record MUST carry a tenant identifier applied at ingest time; no query path MAY return results without filtering by tenant identifier.
- **FR-012**: An automated isolation test suite MUST exist; it MUST deliberately attempt cross-tenant reads and assert zero records are returned.
- **FR-013**: New tenant provisioning MUST be a self-contained operation that does not require direct infrastructure access.

**Admin Module**
- **FR-014**: The admin module MUST be accessible ONLY to the Platform Operator persona; all other personas MUST receive a permission-denied response.
- **FR-015**: The admin funnel view MUST show each beta organization's current funnel stage, time-in-stage, and a drop-off flag when a pre-activation org exceeds 48 hours at any stage.
- **FR-016**: Activation timing breakdowns (four segments: sign-up-to-connect, connect-to-ingest, ingest-to-briefing, total active attention) MUST be stored per org and displayed in the admin view.
- **FR-017**: The discovery survey table MUST show each organization's selected pain option and free-text entry where applicable.

**Support Workflows**
- **FR-018**: The Platform Operator MUST be able to retrieve a debug trace for any named operation by its identifier (briefing run ID, ingest job ID, agent invocation ID).
- **FR-019**: Debug-trace export MUST redact all LLM prompt and completion content, replacing with token counts; the export MUST be structurally complete otherwise.
- **FR-020**: Tenant impersonation MUST display a persistent "impersonation active" banner; ALL write operations MUST be blocked during an impersonation session.

**Continuous Eval**
- **FR-021**: The nightly eval pipeline MUST run the Synthesizer and Mapper golden-dataset evaluations automatically.
- **FR-022**: Synthesizer accept rate < 40% OR Mapper recall < 50% MUST block promotion and notify the Platform Operator.
- **FR-023**: The CI eval job MUST degrade gracefully when GPU infrastructure is unavailable, marking infrastructure-dependent fixtures as "infrastructure-unavailable" rather than failing the entire suite.

**Telemetry Dashboards**
- **FR-024**: The Platform Operator MUST have a live dashboard showing agent failure rates, with an alert threshold configurable per agent type.
- **FR-025**: Ingestion-freshness monitoring MUST flag any active ingest source that has produced no new records for more than two hours.

**Doc Site**
- **FR-026**: The doc site MUST include a Getting Started guide covering sign-up → integration-connect → scope-selection → briefing-approval in sequence.
- **FR-027**: The doc site MUST include a Concepts section covering: briefing, initiative, dependency, decision, and the activation moment.
- **FR-028**: The doc site MUST include a Workflow Reference section covering the Executive Briefing, Dependency Scan, and the onboarding flow.
- **FR-029**: The doc site MUST be statically generated and deployable without a backend runtime.

### Key Entities

- **OnboardingSession**: Per-organization record tracking which onboarding step was last completed, discovery-survey answer, connected integrations, scope selections, ingest job reference, and activation timestamp.
- **ActivationEvent**: Immutable telemetry record capturing the activation moment: organization ID, timestamp, funnel timing segments (four durations), first-briefing accept-as-is flag.
- **IngestJob**: Record of a single ingest run: source, status (running/completed/stalled), progress percentage, record counts by type, start/end timestamps, error details if any.
- **DebugTrace**: Exportable span bundle for a named operation: ordered spans with agent identity, tool calls, token counts (no raw prompt content), latency per step, failure location if any.
- **AdminFunnelRow**: Derived view of one org's position in the activation funnel: current stage, time-in-stage, drop-off flag, timing segments where available.
- **TenantImpersonationSession**: Time-bounded read-only session initiated by the Platform Operator; all write operations blocked; records start time and operator identity.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: A new operator completes sign-up → first briefing approval in under 30 minutes of active attention and under 24 hours wall-clock, across representative source-data shapes.
- **SC-002**: The activation completion rate across the beta cohort is ≥ 80% (per §9.5).
- **SC-003**: Drop-off rate at any single onboarding step is < 10% of entrants to that step.
- **SC-004**: Day-1 support contact rate is < 30% of the onboarded cohort.
- **SC-005**: The tenant isolation test suite passes with zero cross-tenant record exposures across 100% of test runs.
- **SC-006**: Nightly eval regressions are detected and reported within 24 hours of being introduced.
- **SC-007**: A new operator can complete the getting-started guide from the doc site and reach the integration-connect screen without external help.
- **SC-008**: The first briefing for a new org achieves a ≥ 30% accept-as-is rate on the first submission (cold-start bar, per §9.5).
- **SC-009**: Debug-trace retrieval for a named operation takes under 60 seconds from the Platform Operator entering the identifier to seeing the full span tree.

---

## Assumptions

- The Platform Operator persona is a single individual (the founder) for MVP closed beta; multi-operator admin access is out of scope.
- "Activation" is defined as approval of the first AI-generated briefing, not arrival at a populated view (per §8.3.9).
- Exactly three OAuth sources (Jira, GitHub, Slack) are supported for closed beta; no additional adapters are in scope.
- The doc site is a static site requiring no backend; it will be authored in Markdown and rendered by an appropriate static-site generator.
- Email notification on ingest completion uses an existing transactional email provider already configured in the Clerk environment.
- The nightly eval golden dataset is the same dataset used in Phase 2 evals, extended with any new test cases added during Phase 3.
- "Platform Operator only" visibility means a feature flag or role attribute in Clerk; it does not require a separate application.
- Bulk-import of historical data (e.g., past year of Jira) is explicitly out of scope; only forward sync from integration-connect date.
- SSO/SAML, white-label onboarding, team invitations beyond a single operator, and custom integration adapters are all out of scope for this phase.
- The first-run briefing variant (colder start, partial data) is already specified in §7.2.1; this spec does not redefine its content, only its scheduling trigger.

---

## Dependencies

- Phase 1 backend: tenant-scoped data model, Clerk JWT auth (required — must be deployed and stable).
- Phase 2 agents: Synthesizer and Mapper agents, eval runner, golden dataset (required — Phase 4 wraps these in nightly CI).
- Phase 3 frontend: Galaxy, Topology, Decision views (required — these are revealed at the activation moment via progressive disclosure).
- Clerk SDK: account creation, OAuth token management, platform-operator role flag.
- Transactional email provider: ingest-completion notification, any error notification in recovery paths.
- OTEL managed collector: must be provisioned before telemetry dashboards can receive live data.
