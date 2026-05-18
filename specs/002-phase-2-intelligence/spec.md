# Feature Specification: Phase 2 — Intelligence

**Feature Branch**: `2-phase-2-intelligence`
**Created**: 2026-05-18
**Status**: Draft
**Source**: docs/prd.md §7.2.1, §7.3, §8.3.3, §10 Phase 2 scope

---

## User Scenarios & Testing

### User Story 1 — Receive a useful weekly briefing (Priority: P1)

The author asks the platform to generate their weekly Executive Briefing. The
platform retrieves seven days of activity across Jira, GitHub, and Slack,
synthesizes it into a structured briefing draft (progress, risks, decisions
awaiting action, dependencies that moved, escalations), and presents it for
review. The author reads the draft, makes minor edits or approves it as-is,
and the final briefing is delivered to their Slack or saved for reference.

**Why this priority**: This is the primary Phase 2 exit criterion — receiving
a useful briefing for four consecutive weeks. It is the first end-to-end
workflow and the primary test of whether the Operational Synthesizer agent
produces useful output from real data.

**Independent Test**: With one week of real ingested data available, trigger a
briefing generation, verify a structured draft appears within five minutes, and
confirm the draft contains at least one item per section (progress, risks,
decisions) grounded in source data.

**Acceptance Scenarios**:

1. **Given** seven days of ingested data (Jira, GitHub, Slack) is available
   for the tenant, **When** the operator triggers a briefing, **Then** a
   structured Markdown draft appears within five minutes containing: progress
   summary, risk items, decisions awaiting operator action, and dependency
   movements.

2. **Given** a briefing draft is presented, **When** the operator approves it
   without edits, **Then** the briefing is saved as an `Artifact` record in
   the memory graph and (if configured) delivered via Slack or email; the
   accept-as-is rate is recorded for tracking against the ≥ 40% target.

3. **Given** a briefing draft is presented, **When** the operator edits
   sections and then approves, **Then** the final edited version is saved and
   the edit distance between draft and final is recorded for tracking against
   the < 60% manual-edit-rate target.

4. **Given** a briefing draft contains a flagged risk, **When** the operator
   confirms the risk, **Then** a `Risk` node is created in the memory graph
   with the operator's confirmation as provenance; if the operator dismisses
   the risk, no graph state is written.

5. **Given** a scheduled briefing time is configured, **When** that time
   arrives, **Then** briefing generation is triggered automatically without
   operator intervention and the draft appears in the approval inbox.

6. **Given** source data is sparse (fewer than five signals in the window),
   **When** the briefing is generated, **Then** the draft acknowledges the
   low-signal condition rather than fabricating content; the operator sees a
   labeled low-confidence briefing.

---

### User Story 2 — Review and act on the approval inbox (Priority: P2)

The operator has a single inbox surface where all AI-generated drafts await
action: briefing drafts, proposed risk entries, and proposed dependency edge
updates. They can approve, reject, or edit each item. Approved items become
canonical graph state; rejected items are discarded with the rejection
recorded as provenance; edited items record the delta.

**Why this priority**: The approval surface is the governance layer that makes
every AI action reversible and auditable, as required by the constitution
(Principle III). Without it, the Synthesizer agent cannot write anything to
the graph — all outputs are provisional until a human acts.

**Independent Test**: Create three pending items (one briefing draft, one
proposed risk, one proposed dependency edge) via the agent. Open the inbox,
approve one, reject one, and edit-then-approve one. Verify graph state reflects
only the approved/edited items; the rejected item is absent from graph state
but present in the rejection log.

**Acceptance Scenarios**:

1. **Given** the Synthesizer agent has produced a briefing draft, **When**
   the operator opens the inbox, **Then** the draft appears with status
   "pending approval", creation timestamp, and a preview of the first 200
   characters.

2. **Given** a pending item is in the inbox, **When** the operator approves
   it, **Then** the item transitions to "approved", its content is committed
   to the memory graph as canonical state, and the approval timestamp and
   operator identity are recorded as provenance.

3. **Given** a pending item is in the inbox, **When** the operator rejects
   it, **Then** the item transitions to "rejected", nothing is written to the
   memory graph, and the rejection (with optional reason) is recorded for
   telemetry.

4. **Given** a pending item is in the inbox, **When** the operator edits the
   content and then approves, **Then** the edited version is committed to
   the graph with the operator as author, and the edit delta between
   AI-generated and final is recorded.

5. **Given** an item has been pending for more than 24 hours, **When** the
   operator opens the inbox, **Then** the item is visually flagged as stale
   and an optional notification has been sent (if notification preferences
   are configured).

6. **Given** the inbox is empty, **When** the operator views it, **Then** a
   clear empty-state message appears with guidance on when the next briefing
   is expected.

---

### User Story 3 — Dependency surface discovers hidden relationships (Priority: P3)

The Dependency Mapper agent scans the memory graph and ingest signals to
identify dependency relationships that are not yet explicitly recorded — for
example, a Slack thread discussing a cross-team blocker, or a series of PR
reviews between two initiatives that implies coupling. Proposed dependency edges
are surfaced in the approval inbox for the operator to confirm before they
enter the canonical graph.

**Why this priority**: The Dependency Mapper operates at autonomy level 1
(surfaces, does not modify) in the briefing workflow, and escalates to level 2
(proposes graph mutations) in the portfolio intelligence context. This story
validates the mapper's ability to discover real relationships and propose them
accurately — which becomes critical input for Phase 3 visualization.

**Independent Test**: With at least two active initiatives in the graph and
cross-initiative signals in Slack ingest, trigger a dependency scan, verify at
least one proposed dependency edge appears in the approval inbox, and confirm
that approving the edge creates a canonical `Dependency` record in the graph.

**Acceptance Scenarios**:

1. **Given** two initiatives with cross-team Slack discussion exist in the
   graph, **When** the Dependency Mapper runs a scan, **Then** at least one
   `Dependency` edge candidate is proposed, citing the Slack signals as
   evidence.

2. **Given** a proposed dependency edge is in the approval inbox, **When**
   the operator approves it, **Then** a canonical `Dependency` edge is
   written to the memory graph with the agent as originator and the operator
   as approver.

3. **Given** a proposed dependency edge is in the approval inbox, **When**
   the operator rejects it, **Then** no edge is written; the rejection
   contributes to the false-positive rate metric tracked for the mapper.

4. **Given** a dependency edge was approved in a prior cycle, **When** the
   Dependency Mapper runs again and finds no supporting evidence for the edge,
   **Then** it surfaces a "dependency may no longer be active" signal in the
   briefing for operator review; it does not autonomously remove the edge.

---

### User Story 4 — Eval suite confirms agent quality (Priority: P4)

The author designs and runs evaluation suites for both agents that measure
acceptance rate, edit distance, false-positive rate, and failure-mode
detection. Eval runs execute against golden datasets built from the first
four weeks of real briefings. Results are logged per run and trended over
time, with CI enforcing regression gates.

**Why this priority**: Constitution Principle V requires evaluation before any
agent is enabled outside development. The eval suite is a prerequisite for
Phase 3 and closed beta, not an optional quality step.

**Independent Test**: Build a golden dataset of five known briefings (author's
actual approved outputs). Run the Synthesizer eval against this dataset. Verify
the eval run produces a structured report showing per-briefing accept-rate
simulation, edit-distance score, and false-positive count — all logged to the
observability platform.

**Acceptance Scenarios**:

1. **Given** a golden dataset of five or more reference briefings exists,
   **When** the eval suite runs, **Then** a structured report is produced
   showing: simulated accept-as-is rate, median edit distance, false-positive
   risk rate, and comparison to the prior run's results.

2. **Given** the eval suite is configured in continuous integration, **When**
   a code change degrades the simulated accept-as-is rate below 40%, **Then**
   the CI check fails and the regression is surfaced before merge.

3. **Given** the Dependency Mapper eval runs against a held-out dependency
   set, **When** the results are computed, **Then** precision and recall
   against the held-out set are reported; any run below 50% recall is flagged
   as a regression.

4. **Given** a failure mode (hallucinated stakeholder, stale dependency claim,
   missed escalation, citation error) is injected into the eval dataset,
   **When** the eval runs, **Then** the failure-mode detection test correctly
   identifies the injected error for each of the four failure types.

---

### Edge Cases

- What happens when the ingestion pipeline has not run in the past 7 days?
  Briefing generation proceeds but the draft is labeled "data may be stale —
  last ingest was N days ago"; the operator can proceed or wait for a fresh
  ingest.

- What happens when the Synthesizer agent exceeds its cost budget on a single
  briefing run? The run halts mid-generation, the partial draft is discarded,
  the operator is notified with the reason; a structured error is recorded in
  the observability platform.

- What happens when both agents produce conflicting assessments of the same
  risk? Both assessments are surfaced in the approval inbox as separate items
  with their respective sources; the operator resolves the conflict by
  approving, rejecting, or merging the two items.

- What happens when an operator rejects a briefing draft and a new briefing
  is automatically generated the next scheduled day? The prior rejection is
  visible in the operator's history but does not block the new draft.

- What happens when a proposed dependency edge conflicts with an existing
  canonical edge (same from/to nodes)? The proposal is rejected automatically
  with a note that the relationship already exists; no duplicate edges are
  written.

- What happens when the Synthesizer references a stakeholder name not in
  the Actor graph? The reference is flagged with a hallucination warning; the
  operator sees a callout in the draft indicating the name could not be
  verified against the memory graph.

- What happens when the operator clears the approval inbox faster than
  the agent produces new items? The inbox shows an empty state; no
  auto-generation is triggered.

---

## Requirements

### Functional Requirements

**Operational Synthesizer agent**

- **FR-001**: The system MUST provide an Operational Synthesizer agent that
  operates at autonomy level 2 (drafts content; a human approves before
  anything is committed to canonical graph state).
- **FR-002**: The Synthesizer MUST have read access to all graph entities
  and retrieval indices; it MUST NOT write to the canonical graph without
  an operator approval gate.
- **FR-003**: The Synthesizer MUST produce a structured Executive Briefing
  draft containing: progress summary, risk items, decisions awaiting operator
  action, dependency movements, and escalations — each section grounded in
  cited source signals.
- **FR-004**: The Synthesizer MUST detect and flag each of the four defined
  failure modes: hallucinated stakeholder (name not in Actor graph), stale
  dependency claim (edge older than threshold), missed escalation (risk
  crossing threshold not flagged), and citation error (claim attributed to
  wrong artifact).
- **FR-005**: When the Synthesizer proposes Risk entries or Artifact records,
  they MUST be created in a "pending" state and MUST NOT become canonical
  graph state without operator approval.

**Dependency Mapper agent**

- **FR-006**: The system MUST provide a Dependency Mapper agent that operates
  at autonomy level 1 in the briefing workflow (surfaces relationships,
  does not propose graph mutations) and at level 2 in the portfolio
  intelligence workflow (proposes dependency edges pending human approval).
- **FR-007**: The Dependency Mapper MUST have read access to the full graph
  and telemetry (latency, flow health); it MUST NOT create canonical
  `Dependency` edges without operator approval.
- **FR-008**: When a dependency relationship is discovered, the Dependency
  Mapper MUST cite the evidence signals (Slack threads, PR patterns, ticket
  references) that support the proposed edge.
- **FR-009**: The Dependency Mapper MUST NOT autonomously remove existing
  canonical dependency edges; it MUST surface "may no longer be active"
  signals for operator review.

**Executive Briefing workflow**

- **FR-010**: The system MUST support on-demand briefing generation triggered
  by the operator.
- **FR-011**: The system MUST support scheduled briefing generation on a
  configurable cadence (default: weekly).
- **FR-012**: Briefing generation MUST complete (draft available in the inbox)
  within 5 minutes of trigger for a standard 7-day data window.
- **FR-013**: If source data is sparse (fewer than five signals in the window),
  the draft MUST include a visible low-signal label rather than fabricating
  content.
- **FR-014**: If the last ingestion run is more than 7 days old, the draft
  MUST include a data-staleness warning.

**Human approval surface**

- **FR-015**: The system MUST provide an approval inbox listing all pending
  agent-generated items with: item type, creation timestamp, status (pending /
  approved / rejected), and content preview.
- **FR-016**: The inbox MUST support three actions on each item: approve (no
  changes), reject (with optional reason), and edit-then-approve (operator
  edits content, then approves the edited version).
- **FR-017**: Approved items MUST be committed to the canonical memory graph
  with the operator identity and approval timestamp as provenance.
- **FR-018**: Rejected items MUST NOT write any state to the canonical graph;
  the rejection MUST be recorded for telemetry.
- **FR-019**: Items pending for more than 24 hours MUST be visually flagged
  as stale in the inbox.
- **FR-020**: The inbox MUST be clearable in under 3 minutes when content is
  high quality (measured by the operator's own assessment during dogfooding).

**Evaluation suites**

- **FR-021**: An eval suite MUST exist for the Operational Synthesizer, measuring:
  simulated accept-as-is rate, median edit distance, false-positive risk rate,
  and failure-mode detection coverage.
- **FR-022**: An eval suite MUST exist for the Dependency Mapper, measuring:
  dependency detection precision, dependency detection recall, and
  false-positive rate (operator rejection rate of proposed edges).
- **FR-023**: Both eval suites MUST run in continuous integration and MUST
  block promotion when: Synthesizer simulated accept-as-is rate < 40%, or
  Dependency Mapper recall < 50%.
- **FR-024**: Both eval suites MUST produce structured, machine-readable
  output that can be trended over time and compared between runs.
- **FR-025**: Each eval run MUST include tests for all four Synthesizer
  failure modes using injected synthetic errors.

**Observability**

- **FR-026**: Every agent action MUST emit an observability trace containing:
  agent identity, autonomy level, input summary, output summary, latency,
  cost (token count), and governance markers — per the telemetry schema
  committed in Phase 1.
- **FR-027**: Briefing-specific telemetry MUST include: input-signal count
  per source, retrieval hit-rate, agent token cost total, edit distance
  post-approval, downstream action count.
- **FR-028**: Dependency Mapper telemetry MUST include: graph-walk depth,
  inference confidence scores for each proposed edge, and operator decision
  outcome per proposal.

### Key Entities

- **BriefingDraft**: A pending Artifact produced by the Synthesizer; contains
  structured sections (progress, risks, decisions, dependencies, escalations);
  transitions from pending → approved or rejected; edit delta recorded on
  approve.

- **ApprovalItem**: A wrapper around any agent-generated pending output
  (BriefingDraft, proposed Risk, proposed Dependency edge); holds item type,
  status, creation timestamp, and provenance; lives in the approval inbox.

- **ProposedDependency**: A candidate `Dependency` edge proposed by the
  Mapper; includes from-node, to-node, dependency type, evidence citations,
  and confidence score; becomes canonical only on operator approval.

- **ProposedRisk**: A candidate `Risk` entry proposed by the Synthesizer;
  includes description, severity, source signals, and the Synthesizer's
  rationale; becomes canonical only on operator approval.

- **EvalRun**: A structured record of a single evaluation suite execution;
  includes dataset version, per-metric scores, pass/fail per gate, timestamp,
  and comparison delta from prior run.

- **GoldenDataset**: A curated set of reference briefings or dependency sets
  used as ground truth for evaluation; versioned; built from real operator-
  approved outputs.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: The author receives a useful Executive Briefing for four
  consecutive weeks without abandoning the workflow — the primary Phase 2
  exit criterion.

- **SC-002**: The Synthesizer's briefing accept-as-is rate reaches ≥ 40%
  within the four-week evaluation window (i.e., the operator approves at
  least 2 out of 5 briefings without any edits).

- **SC-003**: The median edit distance between the Synthesizer's draft and
  the operator's final approved version is < 60% of draft tokens across the
  four-week window (operator does not have to rewrite the majority of each
  draft).

- **SC-004**: The false-positive risk rate is < 20% (fewer than 1 in 5
  Synthesizer-flagged risks are dismissed by the operator as not real).

- **SC-005**: The median time from briefing trigger to draft available in the
  approval inbox is < 5 minutes.

- **SC-006**: The approval inbox can be cleared by the operator in under
  3 minutes when the content quality is high (operator's own assessment
  during dogfooding sessions).

- **SC-007**: Both eval suites pass on their golden datasets before the end of
  Phase 2, with CI gates enforcing regression prevention.

- **SC-008**: The Dependency Mapper achieves ≥ 50% recall and ≥ 70%
  precision on the held-out dependency validation set within Phase 2.

- **SC-009**: Every agent action is observable in the platform's telemetry
  view within 30 seconds of completion, with all required governance fields
  populated.

- **SC-010**: All four Synthesizer failure-mode tests pass in the eval suite
  (hallucinated stakeholder, stale dependency, missed escalation, citation
  error are each reliably detected).

---

## Assumptions

- **A-001**: Phase 1 Foundation is complete and the memory graph contains
  real ingested data from at least one source (Jira or GitHub) before Phase 2
  begins.
- **A-002**: The author has at least four weeks of real org data available to
  build the golden dataset; the first briefing is produced from live data,
  not synthetic data.
- **A-003**: The LLM used for agent synthesis is Claude (Anthropic); the
  specific model version is chosen at implementation time based on capability
  and cost. No model version is locked in the spec.
- **A-004**: The approval inbox is a local web UI accessible at localhost for
  Phase 2; cloud-hosted UI is a Phase 3/4 concern.
- **A-005**: Briefing delivery channels (Slack, email) are optional in Phase 2;
  the primary delivery mechanism is the approval inbox UI.
- **A-006**: Eval golden datasets are built from real operator-approved
  briefings produced during the first 2–3 weeks of Phase 2 operation;
  synthetic golden data is only used for failure-mode injection tests.
- **A-007**: The Dependency Mapper's held-out validation set is a subset of
  the ingested dependency graph where the ground truth is known; this requires
  at least 20 verified dependency relationships to compute meaningful
  precision/recall.
- **A-008**: Autonomy level declarations and tool permission scopes are
  enforced at the platform layer, not by the LLM's own discretion; the LLM
  cannot escalate its own permissions.

---

## Dependencies and Out of Scope

### Dependencies

- Phase 1 Foundation (memory graph, ingestion pipeline, Clerk auth, OTEL
  observability) — must be complete and running before Phase 2 begins.
- LLM API access (Anthropic Claude) with sufficient rate limits for
  briefing generation.
- At least one week of real ingested data in the memory graph.
- A golden dataset (built during Phase 2 operation) for eval suite validation.

### Out of Scope for Phase 2

- Architecture Analyst and Governance Coordinator agents — Phase 3+ only.
- Architecture Review workflow (§7.2.2) — post-beta.
- Portfolio Dependency Intelligence workflow (§7.2.3) — post-beta (Dependency
  Mapper participates at level 1 in briefing only for now).
- Cloud-hosted approval inbox UI — Phase 3/4.
- Multi-user approval workflows (more than one approver per item) — Phase 4.
- Real-time webhook ingestion (polling-based sync only) — Phase 2+.
- Briefing generation for more than one org (single dogfood tenant only in
  Phase 2).
- Public eval dashboard — Phase 4.
- Galaxy visualization or any Phase 3 surface — Phase 3 only.
