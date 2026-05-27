# Feature Specification: Phase 5 — Goal-Driven UX & In-Context Guidance

**Feature Branch**: `5-goal-driven-ux`
**Created**: 2026-05-21
**Updated**: 2026-05-22 (aligned with AI process re-architecture objective; scope tiered A/B)
**Status**: Tier A ready for implementation; Tier B captured as deferred seed (Phase 6/7)
**Source**: User testing feedback (post Phase 4 activation); research from `/speckit.specify` session

## Overview

After completing onboarding and first briefing approval, Strategic Operators
arrive at the operational intelligence surface — Galaxy, Topology, Decisions,
and Inbox — and consistently report confusion. The views render correctly with
data, but users cannot answer three fundamental questions: *What am I looking
at? What should I do here? How do I get from here to my goal?*

Phase 5 resolves this by making the product self-explanatory for beta users
through contextual, goal-oriented guidance that lives inside the experience
itself. The guidance is not a separate help system — it is the product
communicating its own purpose clearly at the moment of first encounter.

The guiding principle, inherited from the PRD: teach through the product.
Every surface that can explain itself should. Every action should declare its
consequence. Every empty state should be honest about why it's empty and what
needs to happen next.

---

## Strategic Reframe (2026-05-22)

This phase is now explicitly framed as one layer inside a larger objective:
Context-OS must help organisations re-architect existing processes for AI,
implement those changes safely, and prove impact with measurable outcomes.

The current UX guidance work remains in scope and valid, but is reclassified
as the operator-comprehension layer. The product objective now includes:

1. Process baseline modelling (how work runs today).
2. AI-native redesign recommendations (how work should run).
3. Implementation planning and execution tracking (how to change safely).
4. Operational monitoring and KPI measurement (whether change is working).
5. Continuous optimisation (how to improve over time).

### Scope tiers

To keep this spec pack executable while honestly capturing the larger
objective, requirements are split into two tiers:

- **Tier A — Operator-Comprehension Layer (Phase 5, this build).** User
  Stories 1–5, FR-001–FR-014, SC-001–SC-008. Frontend-only (`web/`), no
  backend changes. Ready to implement now.
- **Tier B — Process Re-Architecture Layers (Deferred — Phase 6/7).** User
  Stories 6–9, FR-015–FR-022, SC-009–SC-016, Key Entities 7–10. These
  capabilities require new agents, workflows, persistence, and telemetry, and
  therefore engage the NON-NEGOTIABLE constitution principles (I, II, III, V,
  VI, VII). They are captured here as the validated seed for a dedicated
  Phase 6/7 spec + plan + evaluation suite. **No Tier B implementation begins
  until that follow-on spec passes its own Constitution Check.**

---

## User Scenarios & Testing

### User Story 1 — First Encounter: Understanding Each View's Purpose (Priority: P1)

A Strategic Operator has just completed activation (first briefing approved) and
navigates to the Galaxy view for the first time. They see a force-directed graph
of nodes and edges but don't know what any of it represents or what they should
do. They need immediate context — without reading a manual or watching a tutorial
— to understand the purpose of what they're looking at and the single most
valuable action they can take.

**Why this priority**: This is the moment of truth for the product. If a user
can't orient themselves within 30 seconds of arriving at any view, they lose
trust and disengage. Solving orientation is the highest-leverage UX investment
the team can make at this stage.

**Independent Test**: A net-new user (no prior product knowledge) lands on each
of the four main views and, without any external help, can correctly state:
(1) what the view shows, (2) what the primary action is, and (3) how to start.
Testable via a 60-second think-aloud session with each view open.

**Acceptance Scenarios**:

1. **Given** a user arrives at the Galaxy view for the first time after activation,
   **When** the view fully loads, **Then** a brief, non-blocking orientation message
   appears that names the view's purpose, identifies the primary object type (initiatives),
   and points to the highest-value feature (the overlay controls for Load/Risk/Autonomy/Ownership).

2. **Given** a user arrives at the Workflow Topology view for the first time,
   **When** the view loads, **Then** an orientation message appears explaining that
   each row in the sidebar is a workflow, that colours indicate status, and that clicking
   a workflow navigates the canvas to it.

3. **Given** a user arrives at the Decision Graph for the first time,
   **When** the view loads, **Then** an orientation message appears explaining that
   decisions are captured with rationale and alternatives, that search is the primary
   way to find a decision, and that edges show predecessor and dependent relationships.

4. **Given** a user arrives at the Inbox for the first time with pending items,
   **When** the view loads, **Then** an orientation message appears explaining the
   approval workflow: AI drafts content; the user reviews and approves or rejects;
   approved items enter the knowledge graph.

5. **Given** a user has dismissed the orientation message for a view,
   **When** they return to that view in a future session, **Then** the orientation
   message does not appear again — it was shown once, it was absorbed.

6. **Given** a user dismisses an orientation message, **When** they do so, **Then**
   the dismissal is effortless (single click or keyboard shortcut) and does not
   interrupt their workflow.

---

### User Story 2 — Feature Discoverability: The Galaxy Overlay System (Priority: P2)

A Strategic Operator is using the Galaxy view for its primary purpose: understanding
their org's initiative landscape. The four overlay controls (Load, Risk, Autonomy,
Ownership) are the highest-value features in this view — they recolour the entire
graph to reveal a different operational dimension. But without knowing these controls
exist or what they do, users ignore them and see only a static, unlabelled graph.

**Why this priority**: The overlay system is the main analytical value of Galaxy.
If users don't discover and use it, the view is a map with no key — visually impressive
but operationally useless. Discoverability of these controls is the difference between
a user saying "wow" and a user churning.

**Independent Test**: A user who has never been told about overlay controls
can, within 2 minutes of arriving at Galaxy, identify at least one overlay by name,
understand what it reveals before clicking it, and correctly interpret the result
after applying it. Testable via moderated usability session.

**Acceptance Scenarios**:

1. **Given** a user views the Galaxy overlay controls (Load, Risk, Autonomy, Ownership),
   **When** they hover over any control button, **Then** a tooltip appears that describes
   what that overlay reveals, what a high value looks like, and what action the user
   might take in response (e.g., "Risk — highlights at-risk initiatives. Red = flagged.
   Amber = moderate. Use this to find initiatives that need your attention.").

2. **Given** a user is viewing Galaxy with no overlay active, **When** they look at
   any node, **Then** the node's colour and size follows a legend that is visible
   somewhere on the canvas — the user does not need to guess what blue vs. purple means.

3. **Given** a user opens the Galaxy legend, **When** they read it, **Then** it explains
   both the node-type colour system (Goal, Project, Signal, Artifact) and the status
   indicator system (Active, At-risk, Paused, Complete) in plain operator language.

4. **Given** a user has applied an overlay, **When** they look at coloured nodes,
   **Then** the overlay's own colouring is distinct from the base node-type colours
   and does not create ambiguity about which system is active.

5. **Given** a user opens the Galaxy legend, **When** they are done, **Then** they
   can collapse it without losing their place in the graph or disrupting layout.

---

### User Story 3 — Approval Workflow Clarity: The Inbox (Priority: P3)

The Inbox contains three types of AI-generated items: briefing drafts, proposed
dependency relationships, and proposed risk flags. These three types have meaningfully
different stakes and review criteria, yet they appear in an undifferentiated list.
A user reviewing a briefing draft should think about whether the synthesis is accurate;
a user reviewing a proposed dependency should think about whether the relationship is real;
a user reviewing a risk flag should think about whether the flag is applicable. None of
this distinction is currently communicated.

Additionally, "failure flags" — quality checks the AI ran on its own output — are shown
as warnings without explanation. Users see a caution indicator and don't know if it
means "the AI is unsure" or "you should reject this."

**Why this priority**: Inbox is where users exercise governance over the AI. If
they don't understand what they're reviewing or what failure flags mean, they will
either approve everything blindly (undermining quality) or reject everything nervously
(blocking the AI's utility). Both outcomes damage trust and retention.

**Independent Test**: A user reviewing their Inbox can, for each card, state:
(1) what type of item it is, (2) what decision they're being asked to make,
(3) what a failure flag means and whether it affects their decision.
Testable without any prior product training.

**Acceptance Scenarios**:

1. **Given** a user views an Inbox card with a "briefing draft" type badge,
   **When** they hover over or tap the type badge, **Then** a brief explanation
   appears: "A weekly synthesis drafted by the AI from your connected sources.
   Approve to schedule delivery to your team; reject to flag an issue with the draft."

2. **Given** a user views an Inbox card with a "proposed dependency" type badge,
   **When** they hover over or tap the type badge, **Then** a brief explanation
   appears: "A dependency relationship between two initiatives, inferred from your
   work signals. Approve to record this relationship in the knowledge graph."

3. **Given** a user views an Inbox card with a "proposed risk" type badge,
   **When** they hover over or tap the type badge, **Then** a brief explanation
   appears: "A risk flag raised by the AI against a specific initiative. Approve
   to acknowledge and track; reject if the flag does not apply."

4. **Given** an Inbox card has one or more failure flags, **When** the user views
   the flags section, **Then** contextual help text explains what failure flags are
   ("Quality checks the AI ran on its own draft — they don't block approval, but
   review them before deciding") and each flag specifies exactly what the AI found
   uncertain or potentially incorrect.

5. **Given** a first-time Inbox user sees items for approval, **When** they view
   the page, **Then** the review intent is communicated clearly: approve to confirm,
   reject to send back. The consequence of each action is stated before the user acts.

---

### User Story 4 — Navigation Signals: Knowing When Attention Is Needed (Priority: P4)

The Inbox contains time-sensitive approvals — briefing drafts waiting for review,
proposed graph updates pending confirmation. Currently there is no signal in the
navigation that anything is waiting. A user focused on Galaxy or Decisions has
no reason to check the Inbox and may miss approvals for days.

Additionally, there is no in-app path to documentation or help. Users who are
confused or who want to learn more have no escape hatch within the product.

**Why this priority**: Missed approvals directly delay the AI's feedback loop.
If a briefing waits three days for approval, the briefing cycle loses its weekly
cadence and value. Navigation signals are a low-effort, high-impact fix that
maintains the product's core rhythm.

**Independent Test**: A user with 3 pending Inbox approvals, currently viewing
Galaxy, can identify that approvals are waiting and navigate to them without
checking a URL or external notification. Testable in 30 seconds.

**Acceptance Scenarios**:

1. **Given** there are pending items in the Inbox, **When** a user views any main
   view (Galaxy, Topology, Decisions), **Then** the Inbox navigation item shows a
   visual indicator (numeric badge or dot) indicating unreviewed items exist.

2. **Given** the numeric badge is visible, **When** the user navigates to the Inbox
   and reviews all pending items, **Then** the badge disappears — it reflects real-time
   pending count, not a notification history.

3. **Given** a user is confused about a feature or concept, **When** they look at
   the main navigation, **Then** there is a clearly labelled help or documentation
   link accessible without leaving the view they're in.

4. **Given** a user clicks the help link, **When** the link opens, **Then** it takes
   them to the product documentation in a new context (tab or panel) without disrupting
   their current view state.

---

### User Story 5 — Honest Empty States: Accurate Expectations (Priority: P5)

Two views — Galaxy and Decisions — have empty states with calls-to-action that link
to pages that don't exist. A user who clicks "Adjust source scope" lands on a 404.
A user who clicks "Capture a decision manually" lands on a 404. This is the worst
possible first impression: the product promises an action it cannot deliver.

Beyond broken links, the empty-state copy doesn't set accurate expectations. A user
who has just completed ingest doesn't know if an empty Galaxy means "still processing"
or "nothing was found" or "something went wrong." The distinction matters enormously
for what the user does next.

**Why this priority**: Broken CTAs destroy trust immediately and in a way that's
hard to recover. A user who hits a 404 on their first interaction loses confidence
in the entire product. This is a P5 only because the fix is simpler — not because
the problem is minor.

**Independent Test**: A user encountering an empty state in any view can answer:
(1) why it's empty, (2) what will change it, (3) what — if anything — they can do
right now to move forward. No broken links encountered.

**Acceptance Scenarios**:

1. **Given** the Galaxy view is in an empty state (no initiatives yet),
   **When** the user reads the empty state, **Then** the copy accurately explains the
   reason (ingest is processing, or no sources are connected) and sets an honest
   expectation (initiatives will appear automatically; the user does not need to act).

2. **Given** the Galaxy empty state includes a call-to-action, **When** the user
   clicks it, **Then** they arrive at a functional page that delivers on the CTA's promise.

3. **Given** the Decisions view is in an empty state (no decisions captured yet),
   **When** the user reads the empty state, **Then** the copy explains that decisions
   accumulate from briefing review approvals — the user doesn't need to do anything
   special; decisions will appear after their first briefing cycle.

4. **Given** the Decisions empty state previously offered "Capture a decision manually",
   **When** the updated state is displayed, **Then** no call-to-action promises a
   capability that doesn't exist yet.

5. **Given** any view is in an activating state (data loading),
   **When** the user reads the activating state, **Then** the copy distinguishes
   "still loading" from "empty" — the user knows whether to wait or to act.

---

### User Story 6 — Process Baseline: Modelling How Work Runs Today (Priority: P6, Tier B — Deferred)

> **Scope: Tier B (Phase 6/7).** Seed requirement captured here for forward
> planning. Not implemented in the Phase 5 build.

An operator selects an existing business workflow (e.g., incident response,
vendor onboarding, change approval) and asks Context-OS to map how it actually
runs today. They need an evidence-based current-state model — drawn from
ingested work signals, not a hand-drawn diagram — so they can see where time,
quality, and ownership break down before proposing any AI changes.

**Why this priority**: Re-architecture without a measured baseline is guesswork.
The baseline is the comparison anchor every later tier (redesign, KPIs,
optimisation) depends on. It is therefore the first deferred capability to build.

**Independent Test**: For a workflow with ingested signals, the operator can view
a baseline that names its stages, owners, handoffs, cycle-time distribution, and
the top wait-time and rework hotspots — and can pin that baseline as the anchor
for later comparison.

**Acceptance Scenarios**:

1. **Given** a workflow with ingested work signals, **When** the operator
   requests a baseline, **Then** the system produces a current-state model with
   ordered stages, owners, handoffs, cycle-time p50/p90, and identified
   wait-time and rework hotspots.
2. **Given** a generated baseline, **When** the operator reviews it, **Then**
   each datum is traceable to its source signals (provenance is inspectable).
3. **Given** a baseline the operator accepts, **When** they pin it, **Then** it
   is persisted as the immutable comparison anchor for that process.

---

### User Story 7 — AI-Native Redesign Recommendations (Priority: P7, Tier B — Deferred)

> **Scope: Tier B (Phase 6/7).** Seed requirement captured here for forward
> planning. Not implemented in the Phase 5 build.

Starting from a pinned baseline, the operator asks Context-OS to propose how the
process should run when AI agents take on parts of the work. They need a redesign
that is explicit about who does what — which steps stay human, which become agent
responsibilities, where escalation boundaries sit, and what governance
checkpoints gate the autonomous steps — plus an honest statement of expected
benefit and the risk assumptions behind it.

**Why this priority**: This is the core "re-architect for AI" deliverable. It
depends on the baseline (US6) and must declare autonomy levels and governance
explicitly to be safe and reviewable.

**Independent Test**: For a pinned baseline, the operator receives a redesign
proposal that allocates each stage to human or agent, declares an autonomy level
and escalation boundary per agent step, lists governance checkpoints, and states
expected KPI deltas with explicit risk assumptions — and can approve or reject it.

**Acceptance Scenarios**:

1. **Given** a pinned baseline, **When** the operator requests a redesign,
   **Then** the proposal defines human responsibilities, agent responsibilities,
   escalation boundaries, and governance checkpoints for every stage.
2. **Given** a redesign proposal, **When** the operator reviews it, **Then** each
   agent-performed step carries an explicit autonomy level (0–5) and the proposal
   states expected benefit hypotheses (cycle-time, quality, cost, SLA) and risk
   assumptions.
3. **Given** a redesign proposal, **When** the operator decides, **Then** they
   can approve, reject, or request changes, and the decision is recorded with
   rationale.

---

### User Story 8 — Implementation Planning & Execution Tracking (Priority: P8, Tier B — Deferred)

> **Scope: Tier B (Phase 6/7).** Seed requirement captured here for forward
> planning. Not implemented in the Phase 5 build.

After approving a redesign, the operator needs a safe path from today's process
to the new one. They want a phased implementation plan with owners,
dependencies, readiness gates, and rollback conditions — and then live tracking
of how the rollout is progressing, including which milestones are blocked and why.

**Why this priority**: Approved redesigns deliver no value until rolled out
safely. This tier turns a blueprint into a governed, trackable change. It depends
on US7.

**Independent Test**: For an approved redesign, the operator can view an
implementation plan with phased milestones (each with owner, dependencies,
readiness gate, rollback condition) and see live milestone status with root-cause
context for any blocked milestone.

**Acceptance Scenarios**:

1. **Given** an approved redesign, **When** the operator requests an
   implementation plan, **Then** the plan presents phased milestones each with
   owner, dependencies, readiness gate, and rollback condition.
2. **Given** an active implementation, **When** a milestone is blocked, **Then**
   the system surfaces it with explicit root-cause context.
3. **Given** an active implementation, **When** the operator views progress,
   **Then** milestone status reflects current execution state against the plan.

---

### User Story 9 — Operational Monitoring & Outcome Metrics (Priority: P9, Tier B — Deferred)

> **Scope: Tier B (Phase 6/7).** Seed requirement captured here for forward
> planning. Not implemented in the Phase 5 build.

Once a redesigned process is live, the operator needs to know whether it is
actually working. They want operational monitoring of the AI-enabled process
(throughput, decision latency, error/rework rates, override and intervention
frequency) and a before/after KPI comparison against the pinned baseline — and,
when results drift, concrete optimisation recommendations.

**Why this priority**: Proving impact closes the loop on the whole objective.
Without measurable outcomes, re-architecture is unaccountable. It depends on the
baseline (US6) and a live rollout (US8).

**Independent Test**: For a transformed process, the operator can view live
operational metrics, a before/after KPI comparison with auditable measurement
windows, and at least one optimisation recommendation when KPI drift exceeds
the configured tolerance.

**Acceptance Scenarios**:

1. **Given** a live transformed process, **When** the operator opens monitoring,
   **Then** they see throughput, decision latency, error/rework rate, override
   rate, and intervention frequency.
2. **Given** a baseline and a post-change window, **When** the operator compares,
   **Then** the system shows KPI deltas (cycle time, latency, rework, override,
   cost per outcome) with auditable baseline and post-change windows.
3. **Given** sustained KPI drift beyond configured tolerance, **When** the
   threshold is crossed, **Then** the system generates a targeted optimisation
   recommendation the operator can accept or reject.

---

### Edge Cases

- What happens when a user clears their browser storage? Orientation messages should
  reappear on next visit — preferably with a shorter or condensed version (not identical
  to the first-time message, since the user has seen it before at some level).
- How does the Inbox badge handle a count that grows while the user is viewing Inbox?
  The count should update in real time without disruptive visual changes.
- What if a user dismisses an orientation message within 1 second (accidental dismiss)?
  The message should be dismissible, but ideally it persists long enough (≥3 seconds)
  to have been read before any action triggers automatic dismissal.
- What if the help documentation link is not yet live? The link should not be shown
  at all, or should clearly indicate "coming soon" without leaving the product.
- What if an overlay colour conflicts with a node-type colour in the legend? The legend
  must update to show the active overlay's colouring system, not the base system, when
  an overlay is applied.

---

## Requirements

### Functional Requirements

#### Tier A — Operator-Comprehension Layer (Phase 5, this build)

- **FR-001**: The system MUST display a one-time, dismissible orientation message when
  a user first visits Galaxy, Topology, Decisions, or Inbox after activation.

- **FR-002**: Each orientation message MUST include: the view's primary purpose, the
  main object type being visualised, and the single most valuable action available.

- **FR-003**: Orientation message dismissal MUST be persistent — once dismissed for a
  given view, the message MUST NOT reappear in subsequent sessions for that user.

- **FR-004**: The system MUST display a text tooltip for each Galaxy overlay control
  (Load, Risk, Autonomy, Ownership) that appears on hover and describes what the
  overlay reveals and what high/low values indicate.

- **FR-005**: The Galaxy view MUST include a visible legend that maps node-type colours
  (Goal, Project, Signal, Artifact) and status indicators (Active, At-risk, Paused,
  Complete) to their meanings in plain language.

- **FR-006**: The Galaxy legend MUST be collapsible and MUST persist its
  collapsed/expanded state across sessions for that user.

- **FR-007**: Each Inbox card type badge (briefing draft, proposed dependency, proposed risk)
  MUST include an accessible explanation of what that item type means and what the
  user's approval/rejection action does to it.

- **FR-008**: Inbox cards with failure flags MUST display contextual explanation text
  clarifying that failure flags are AI self-assessment signals, not blocking errors,
  and specifying what each flag found uncertain.

- **FR-009**: The main navigation MUST display a live count indicator on the Inbox
  item when one or more unreviewed Inbox items exist, and MUST remove that indicator
  when all items have been acted upon.

- **FR-010**: The main navigation MUST include a persistent help/documentation link
  that opens documentation in a new context without disrupting the user's current view.

- **FR-011**: The Galaxy empty state MUST accurately describe why the view is empty
  and set correct expectations (e.g., processing vs. no data); any call-to-action
  MUST link to a functional destination.

- **FR-012**: The Decisions empty state MUST accurately describe how decisions enter
  the graph (via briefing-review approvals) and MUST NOT include a call-to-action
  that links to a non-existent form or page.

- **FR-013**: All guidance copy MUST use operator language (briefing, initiative,
  dependency, risk, workflow) — not product-marketing language (unlock, empower,
  intelligent, seamless).

- **FR-014**: All new guidance elements MUST meet WCAG AA colour contrast requirements
  for text and interactive controls.

#### Tier B — Process Re-Architecture Layers (Deferred — Phase 6/7)

> These requirements engage NON-NEGOTIABLE constitution principles (I, II, III,
> V, VI, VII) and MUST be implemented only under a dedicated Phase 6/7 spec that
> passes its own Constitution Check, ships agent/workflow evaluation suites
> (Principle V), and emits conforming telemetry (Principle VI).

- **FR-015** (US6): The system MUST provide a current-state process baseline for each
  selected workflow, including stages, owners, handoffs, cycle-time distribution,
  queue/wait-time hotspots, and failure/rework points, with provenance traceable to
  source signals (Principle II).

- **FR-016** (US7): The system MUST generate AI-native process redesign proposals that
  explicitly define: human responsibilities, agent responsibilities, per-step autonomy
  level (0–5), escalation boundaries, and governance checkpoints (Principles III).

- **FR-017** (US7): Each redesign proposal MUST include expected benefit hypotheses
  (cycle-time, quality, cost, SLA reliability) and explicit risk assumptions.

- **FR-018** (US8): The system MUST provide an implementation plan per approved redesign
  with phased rollout, dependencies, owners, readiness gates, and rollback conditions.

- **FR-019** (US8): The system MUST track implementation progress against plan milestones
  and surface blocked milestones with root-cause context.

- **FR-020** (US9): The system MUST expose operational monitoring for AI-enabled processes,
  including throughput, decision latency, error/rework rates, override rates, and
  intervention frequency, emitted as OpenTelemetry-conformant traces (Principle VI).

- **FR-021** (US9): The system MUST support before/after KPI comparison for each transformed
  process, with auditable baseline windows and post-change measurement windows.

- **FR-022** (US9): The system MUST recommend optimisation actions when KPI drift, failure
  clusters, or governance exceptions exceed configured thresholds.

---

### Key Entities

- **Orientation Message**: A one-time contextual explanation associated with a specific
  view. Has a view identifier, display copy, and a dismissed/not-dismissed state per user.
  State is persisted locally to avoid requiring a server round-trip on every page load.

- **Overlay Control**: A toggle in the Galaxy view that applies a colouring system to
  the initiative graph. Each control has a name, a description of what it reveals, and
  an indication of what high vs. low values mean in operational terms.

- **Inbox Item**: An AI-generated draft awaiting human review. Has a type (briefing draft,
  proposed dependency, proposed risk), content, creation timestamp, failure flags (zero
  or more), and a status (pending, approved, rejected).

- **Failure Flag**: A quality signal generated by the AI during its own draft process.
  Has a type code and a plain-language description of what the AI found uncertain.
  Not a blocking error — a signal for informed human review.

- **Pending Count**: The real-time count of Inbox items in "pending" status for the
  current user's organisation. Drives the navigation badge display.

#### Tier B entities (Deferred — Phase 6/7; MUST be modelled as graph nodes/edges per Principle II)

- **Process Baseline**: Structured model of the current process state, including
  stages, actors, handoffs, latency segments, and quality failure points.

- **Process Blueprint**: Proposed AI-native design for a process, including
  human-agent role allocation, control points, fallback paths, and policy constraints.

- **Implementation Plan**: Phased execution plan mapping blueprint changes into
  milestones with owner, dependency, rollout stage, and rollback readiness.

- **KPI Snapshot**: Time-bound measurement record used for baseline/post-change
  comparisons across operational metrics and quality metrics.

---

## Success Criteria

### Measurable Outcomes

#### Tier A — Operator-Comprehension Layer (Phase 5, this build)

- **SC-001**: ≥80% of first-time view visitors can correctly state the view's primary
  purpose and primary action within 60 seconds of arrival, without external help.

- **SC-002**: Galaxy overlay usage rate among activated users increases to ≥60% within
  the first session (baseline: estimated <20% currently, as controls are undiscovered).

- **SC-003**: Inbox approval rate (proportion of items acted on within 48 hours of
  appearance) increases to ≥75%, measured across the beta cohort.

- **SC-004**: Zero broken CTA destinations — every call-to-action in every view state
  (empty, activating, activated) leads to a functional destination.

- **SC-005**: Time from "user arrives at view" to "user takes their first meaningful
  action" decreases by ≥30% compared to pre-Phase-5 baseline, across Galaxy, Topology,
  and Decisions (measured via activation telemetry).

- **SC-006**: Orientation messages are dismissed (indicating they were read) by ≥85%
  of users within the first 5 minutes of a view visit — not ignored or left on screen.

- **SC-007**: Day-7 retention of beta operators (returning to the product at least
  once in week 2) reaches ≥70%, attributable in part to the navigation badge drawing
  users back to pending approvals.

- **SC-008**: User-initiated support contacts related to "I don't know what to do"
  or "the button doesn't work" decrease to zero within the beta cohort.

#### Tier B — Process Re-Architecture Layers (Deferred — Phase 6/7)

- **SC-009**: For transformed workflows, median end-to-end cycle time decreases by
  ≥25% versus pre-transformation baseline.

- **SC-010**: Decision latency for in-scope approval flows decreases by ≥30% while
  maintaining governance policy compliance.

- **SC-011**: Rework/defect rate in transformed workflows decreases by ≥20% compared
  with baseline window.

- **SC-012**: Cost per completed process outcome decreases by ≥15% for targeted
  workflows within two release cycles after rollout.

- **SC-013**: ≥90% of redesign proposals include explicit owner assignment, rollout
  gate definitions, and rollback conditions prior to activation.

- **SC-014**: ≥80% of transformed processes maintain KPI telemetry completeness
  (no missing critical metrics for more than one reporting interval).

- **SC-015**: Override and exception events are visible within 5 minutes of occurrence
  for ≥95% of monitored processes.

- **SC-016**: At least one optimisation recommendation is generated for every process
  exhibiting sustained KPI drift beyond configured tolerance for 7 days.

---

## Assumptions

- Users have completed activation (Phase 4 onboarding + first briefing approval) before
  encountering these guidance elements. Guidance is not shown during onboarding itself —
  that flow has its own progressive disclosure.
- Orientation message persistence is implemented via browser-local storage, keyed
  per-view. This is a deliberate choice: it avoids a server round-trip and keeps the
  guidance layer stateless from the backend's perspective. The trade-off (messages reappear
  on new devices/browsers) is acceptable for beta.
- The product documentation does not need to be live on day 1 of Phase 5. The help link
  can link to a "coming soon" page or be replaced with a visible placeholder — but it
  must exist in the navigation as a signal that help exists.
- The Inbox pending count is derived from the existing Inbox data fetch — no new API
  endpoint is required; the count is computed from the already-loaded item list.
- Orientation messages are a one-time communication, not a persistent tips system.
  Phase 5 does not build a full guided-tour or spotlight system. That is explicitly
  out of scope; the PRD's position is that the product teaches through its own surfaces.
- Tier B (US6–US9, FR-015–022, SC-009–016) is captured as a validated seed only.
  The Phase 5 build ships Tier A exclusively. Tier B will not be implemented until a
  dedicated Phase 6/7 spec is authored and passes its own Constitution Check with
  committed evaluation suites and conforming telemetry. Tier B success criteria
  (SC-009–016) are therefore measured only after that follow-on work ships, not in
  the Phase 5 beta cohort.

---

## Out of Scope

- Step-by-step product tours with spotlight overlays (see PRD §8.3.9)
- In-app chat or help widget
- Full autonomous process execution without human governance checkpoints
- Settings/source management page
- Density mode switcher
- Keyboard shortcut cheat sheet
- Multi-device orientation message sync
