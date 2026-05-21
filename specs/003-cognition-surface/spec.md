# Feature Specification: Cognition Surface

**Feature Branch**: `3-cognition-surface`
**Created**: 2026-05-18
**Status**: Draft
**Input**: Phase 3 — Cognition Surface: Initiative Galaxy, Workflow Topology, Decision Graph, shared design system, motion language. Full frontend app greenfield. Source: docs/prd.md §8.3.4, §8.3.5, §8.3.6, §8.3.7, §8.3.8, §8.3.10, §10 Phase 3 scope.

---

## Overview

The Cognition Surface is the visual layer of Context-OS: three interconnected views that let Strategic Operators see, navigate, and reason about their organization's initiatives, workflows, and decisions. Together these surfaces are what makes Context-OS tangible — they carry the demo, anchor the product promise, and surface the intelligence produced by Phase 2.

**Primary user**: Strategic Operator (EM, VP, or operational lead accountable for cross-team coordination).

---

## User Scenarios & Testing

### User Story 1 — Initiative Galaxy: Spatial Map of the Organization (Priority: P1)

A Strategic Operator opens Context-OS and immediately sees their organization's initiatives arranged as an interactive spatial map. Nodes represent initiatives; connections represent shared work, dependencies, and shared actors. The operator can zoom into a cluster, lasso a group of related initiatives, apply overlays to highlight risk or load, and scrub backward in time to see how the map looked last quarter. At no point does the operator need a tutorial or explanation — the view communicates intent without narration.

This is the primary demo-facing surface and the highest-risk qualitative deliverable. It must reach a "world-class" bar: if placed side-by-side with the best-in-class graph product (Linear's graph view), internal reviewers cannot tell which is the production product.

**Why this priority**: Initiative Galaxy is the visual centerpiece of Context-OS and the make-or-break deliverable for the phase. Everything else supports or follows from it.

**Independent Test**: Can be tested independently by loading a representative seed graph (10k+ nodes, 30k+ edges) and running: (a) the performance benchmark suite, (b) a 60-second no-narration demo walk, and (c) a side-by-side internal design review against the reference set. Passes if all three gates clear.

**Acceptance Scenarios**:

1. **Given** a populated organization graph (≥10,000 initiatives, ≥30,000 connections), **When** the operator opens the Galaxy view, **Then** the full graph renders at ≥30 frames per second with no layout jank on both M-series Mac and a 2-year-old Windows laptop.

2. **Given** a populated graph, **When** the layout engine runs, **Then** the force layout converges and stabilizes within 5 seconds.

3. **Given** the galaxy is displayed, **When** the operator uses mouse, keyboard, or touch lasso to select a region, **Then** the nodes within the lasso are selected with a single gesture — no multi-step workflow.

4. **Given** two historical graph snapshots (e.g., 30 days apart), **When** the operator moves the time-travel scrubber between them, **Then** the transition animation completes in under 500ms.

5. **Given** the operator selects an overlay (risk, load, autonomy, or ownership), **When** the overlay is applied, **Then** the visual encoding updates without triggering a re-layout of the graph.

6. **Given** the operator clicks a node, **When** the node detail pane opens, **Then** all key properties of that initiative are visible without leaving the Galaxy view.

7. **Given** a 60-second unscripted demo session, **When** an internal reviewer watches without explanation, **Then** the reviewer can correctly describe what the view shows and what the operator can do with it.

8. **Given** the Galaxy is shown side-by-side with the reference product at an internal design review, **When** reviewers are asked which is the production product, **Then** no reviewer can correctly distinguish them.

9. **Given** zero initiatives exist (empty state), **When** the operator opens Galaxy, **Then** a placeholder constellation surface renders with explanatory copy and a single "Adjust source scope" action — not a blank canvas.

10. **Given** 1–9 initiatives exist (activating state, ingest in progress), **When** the operator opens Galaxy, **Then** discovered initiatives render as real nodes while placeholder constellations fill remaining space; copy communicates progress with a count and estimated time remaining; a "Notify me when done" action is available.

---

### User Story 2 — Workflow Topology: Team Coordination Pattern Map (Priority: P2)

A Strategic Operator needs to understand how their team's recurring workflows are structured: who owns each step, what the current status is, and where bottlenecks form. The Workflow Topology view renders workflows as structured diagrams — each node is a step, edges represent flow — with overlays for latency, status, and team ownership. Operators can filter by team, initiative, or status to focus on what matters.

This view must reach a "very good" bar: defensible against Linear's project views and Notion's database views in a side-by-side comparison, with no data fidelity gaps.

**Why this priority**: Workflow Topology surfaces coordination intelligence from Phase 2 and is the default view shown after onboarding. It is lower risk than Galaxy (structured layout vs. force layout) but load-bearing for first-run value.

**Independent Test**: Load representative workflow data (up to 500 nodes across multiple workflows), apply bottleneck overlay, filter by team, and run visual regression tests at three viewports (mobile-landscape, laptop, large display). Passes if sub-second interaction is maintained and no regressions from reference snapshots.

**Acceptance Scenarios**:

1. **Given** up to 500 workflow nodes across multiple workflows, **When** the operator navigates the view, **Then** all interactions (pan, zoom, filter) respond in under 1 second.

2. **Given** a workflow is rendered, **When** the operator enables the bottleneck overlay, **Then** steps with latency above threshold are visually distinguished and the overlay does not disrupt the underlying layout.

3. **Given** multiple teams own different workflows, **When** the operator applies a team filter, **Then** only workflows owned by the selected team are shown within 500ms.

4. **Given** zero workflows exist (empty state), **When** the operator opens Workflow Topology, **Then** the Executive Briefing workflow renders as a dimmed seed node with copy *"Workflows derive from your team's coordination patterns. Executive Briefing is active by default; others appear as patterns emerge."* and a "View Executive Briefing" primary action.

5. **Given** 1–9 workflows exist (activating state), **When** the operator opens Workflow Topology, **Then** mapped workflows render at full fidelity; faint anticipated workflows hint at what is being discovered; copy communicates how many have been mapped and invites exploration.

6. **Given** the view at laptop viewport, **When** compared side-by-side with Linear's project view in an internal review, **Then** reviewers note no data fidelity gaps and the topology is defensible.

---

### User Story 3 — Decision Graph: Organization Decision History (Priority: P3)

A Strategic Operator needs to browse the accumulating history of decisions captured in the system, understand each decision's rationale and alternatives, and trace how decisions depend on or invalidate earlier ones. The Decision Graph renders decisions as a navigable hierarchy: each node is a decision, edges show predecessor/alternative/dependent relationships, and the layout makes temporal and dependency relationships legible. Operators can search by date range, author, or impacted system, and hover or open a pane to read full rationale.

This view must reach a "very good" bar: the surfacing of rationale and alternatives is the key differentiator against Confluence pages and manual ADR lists.

**Why this priority**: Decision Graph is lower usage frequency than Galaxy or Topology, and its qualitative bar is achievable with known layout patterns. It is P3 because it can be cut (per PRD kill trigger) if Topology runs over schedule.

**Independent Test**: Load up to 1000 decision records, verify dagre layout is legible, search for a known decision, and confirm result in under 2 seconds. Visual regression at three viewports. Passes if all three checks clear.

**Acceptance Scenarios**:

1. **Given** up to 1000 decisions, **When** the operator opens the Decision Graph, **Then** the layout is legible — dense clusters collapse with an expand control; no decision is obscured without a way to reveal it.

2. **Given** the operator searches for a decision by name or system, **When** results appear, **Then** the matching decision is highlighted within 2 seconds of query submission.

3. **Given** the operator hovers over a decision node, **When** the hover is held, **Then** rationale and alternatives are visible in a tooltip or side pane without leaving the graph.

4. **Given** the operator applies a date-range filter, **When** the filter is set, **Then** only decisions within the range are shown; predecessor edges outside the range are dimmed rather than hidden.

5. **Given** zero decisions exist (empty state), **When** the operator opens Decision Graph, **Then** two example decision nodes render in placeholder-grey with copy *"Decisions accumulate as your team captures them. Context-OS proposes decisions from briefing reviews — each approval becomes a decision in your graph."* and a "Capture a decision manually" primary action.

6. **Given** 1–19 decisions exist (activating state), **When** the operator opens Decision Graph, **Then** the full dagre layout renders without cluster collapse; copy communicates how many decisions have been captured so far.

---

### User Story 4 — Shared Design System and Motion Language (Priority: P1, prerequisite)

All three views and the approval surface feel like a single coherent product, not three stitched components. A shared visual language — consistent color tokens, spacing, typography, component primitives, and motion patterns — is established before any view-specific work begins. Motion follows two tiers: everyday micro-interactions (hover, selection, panel open/close) and set-piece transitions (time-travel scrub, state-change animations). The design system supports empty, activating, and activated states via placeholder-grey tokens.

**Why this priority**: P1 because the design system is a prerequisite for all three views — without consistent tokens and components, cross-surface coherence is not achievable in parallel development. Its absence is the main risk for the "feels like one product" qualitative bar.

**Independent Test**: A standalone design-system storybook or reference page demonstrates all tokens (color, spacing, motion timing, placeholder-grey level), all shared component primitives, and both motion tiers without loading any real graph data.

**Acceptance Scenarios**:

1. **Given** a shared color token set is defined, **When** any view renders, **Then** all colors derive from the token set — no hardcoded color values exist in view-specific code.

2. **Given** a placeholder-grey level is defined in the token set, **When** an empty or activating state renders in any view, **Then** placeholder content uses that exact neutral lightness level — structurally identical to live content but visually distinct.

3. **Given** a set-piece transition is triggered (e.g., time-travel scrub, state change), **When** the animation plays, **Then** it uses the GSAP-tier motion specification from the shared motion language — not arbitrary timing values.

4. **Given** a set of shared component primitives (overlay panel, filter bar, node tooltip, state CTA), **When** inspected across all three views, **Then** the same primitives are used — no per-view reimplementations of shared patterns.

5. **Given** the three views are rendered in sequence, **When** an internal reviewer evaluates them, **Then** the reviewer identifies them as belonging to the same product without prompting.

---

### User Story 5 — Empty and Activating States: Cross-View (Priority: P2, cross-cutting)

Before the operator's organization has accumulated data — during sign-up, initial ingestion, or early usage — every view must communicate what will be there and why it is not there yet. The three states (empty, activating, activated) are defined per view in User Stories 1–3 above. This story captures the cross-cutting contract: every state must have exactly one CTA, placeholder content must be structurally identical to live content (not blank), transitions between states must be animated gracefully, and copy must be honest and specific.

**Why this priority**: P2 because these states appear in every first-run session (Phase 4) and are the primary driver of whether empty intermediate states feel like progress or failure. They share an implementation contract across three views.

**Independent Test**: For each of the three views, at each of three viewports, load test fixtures that force the empty and activating states. Confirm: (a) one and only one CTA is present, (b) copy is view-specific and honest, (c) placeholder-grey treatment is present, (d) state-transition animation plays when switching from empty to activating. Visual regression tests lock these states.

**Acceptance Scenarios**:

1. **Given** any view is in empty or activating state, **When** the operator looks at the state, **Then** exactly one primary action is surfaced — never zero, never two.

2. **Given** any view is in empty or activating state, **When** the copy is read, **Then** it names the specific reason for the state (e.g., "ingest still discovering" vs "your team hasn't captured decisions yet") — no generic placeholder copy.

3. **Given** new data arrives (ingest completes a batch), **When** the state transitions from activating → activated, **Then** the transition is animated without a flash of blank content.

4. **Given** the empty and activating states are shown at internal review side-by-side with Linear and Notion empty states, **When** reviewers evaluate them, **Then** the Context-OS states communicate more about *what will be here* and *what the operator can do* than the reference states.

5. **Given** visual regression tests are committed for all three views × three viewports × two pre-activated states, **When** any state changes in a future deploy, **Then** the CI regression suite catches the change before merge.

---

### Edge Cases

- What happens when the graph has zero nodes (brand-new tenant, never ingested)? → Each view renders its empty state; no blank canvas is acceptable.
- What happens when ingest stalls mid-run and the graph is partially populated? → Activating state persists with honest copy; the CTA offers a recovery path.
- What happens when a node has no edges (orphan initiative)? → The node renders in the galaxy; layout places it at the periphery.
- What happens when 10k+ nodes cause layout computation to exceed 5s? → A progress indicator shows layout convergence; the view does not block interaction while the layout runs.
- What happens at mobile-landscape viewport where space is constrained? → All three views render at mobile-landscape with functional (not degraded) UI; overlays and filters collapse to accessible controls.
- What happens when a design review fails the qualitative bar? → The PRD kill trigger activates: contract designer engaged (Galaxy) or Decision Graph cut from MVP (Topology/Graph overrun).
- What happens when an operator applies multiple filters simultaneously? → Filter combination is AND logic; the view updates with each filter change; no filter combination produces a blank state without explanation.

---

## Requirements

### Functional Requirements

**Initiative Galaxy**

- **FR-001**: The system MUST render an organization's full initiative graph (≥10,000 nodes, ≥30,000 edges) at ≥30 frames per second on both M-series Mac and a 2-year-old Windows laptop.
- **FR-002**: The force-layout engine MUST converge and stabilize the Galaxy layout within 5 seconds of graph load.
- **FR-003**: The operator MUST be able to select groups of nodes using lasso selection via mouse, touch, and keyboard without a multi-step workflow.
- **FR-004**: The operator MUST be able to scrub between two historical graph snapshots; the transition animation MUST complete in under 500ms.
- **FR-005**: The operator MUST be able to apply overlays (load, risk, autonomy, ownership) that compose without triggering re-layout.
- **FR-006**: Clicking a node MUST open a detail pane with that initiative's properties without leaving the Galaxy view.
- **FR-007**: Galaxy MUST render an empty state (0 initiatives) with a placeholder-grey constellation, specific explanatory copy, and a single "Adjust source scope" CTA.
- **FR-008**: Galaxy MUST render an activating state (1–9 initiatives) with discovered initiatives as real nodes, placeholder constellations for the remainder, ingest-progress copy with count and estimated time, and a "Notify me when done" CTA.
- **FR-009**: A performance benchmark suite MUST be committed to CI and run on a representative test graph; a frame-rate regression test MUST run in CI on a fixed graph.
- **FR-010**: Three internal design reviews of Galaxy MUST be completed before closed beta and documented in `docs/design-reviews/`.

**Workflow Topology**

- **FR-011**: The system MUST render up to 500 workflow nodes with sub-second interaction (pan, zoom, filter all < 1s).
- **FR-012**: The operator MUST be able to apply bottleneck and latency overlays that visually distinguish steps above threshold without disrupting layout.
- **FR-013**: The operator MUST be able to filter by team, initiative, and status; filter results MUST apply within 500ms.
- **FR-014**: Each workflow node MUST display status, ownership, and autonomy level markers.
- **FR-015**: Workflow Topology MUST render an empty state with the Executive Briefing workflow as a dimmed seed node, specific explanatory copy, and a "View Executive Briefing" CTA.
- **FR-016**: Workflow Topology MUST render an activating state showing mapped workflows at full fidelity with faint anticipated workflows and discovery-progress copy.
- **FR-017**: Visual regression tests MUST be committed at three viewports (mobile-landscape, laptop, large display).

**Decision Graph**

- **FR-018**: The system MUST render up to 1,000 decisions in a legible hierarchical layout; clusters MUST collapse/expand when density exceeds threshold.
- **FR-019**: The operator MUST be able to search decisions by date range, author, and impacted system; a known decision MUST be locatable in under 2 seconds.
- **FR-020**: Rationale and alternatives for a decision MUST be visible on hover or in a pane without navigating away from the graph.
- **FR-021**: Predecessor, alternative, and dependent edges MUST be rendered and visually distinguishable.
- **FR-022**: Decision Graph MUST render an empty state with two placeholder-grey example decision nodes, specific explanatory copy, and a "Capture a decision manually" CTA.
- **FR-023**: Decision Graph MUST render an activating state (1–19 decisions) with full dagre layout and copy communicating how many decisions have been captured.
- **FR-024**: Visual regression tests MUST be committed at three viewports.

**Shared Design System and Motion Language**

- **FR-025**: A shared color token set MUST be defined; all view-specific colors MUST derive from it with no hardcoded values.
- **FR-026**: A placeholder-grey token MUST be defined at a specific neutral lightness level and applied consistently across all empty/activating states in all three views.
- **FR-027**: A motion language with two tiers (set-piece: time-travel scrub, state transitions; everyday: hover, selection, panel) MUST be defined and applied consistently.
- **FR-028**: Shared component primitives (overlay panel, filter bar, node tooltip, state CTA) MUST be implemented once and reused across all three views.
- **FR-029**: All three views MUST pass a cross-surface coherence review where an internal reviewer identifies them as belonging to the same product.

**Empty / Activating States (cross-cutting)**

- **FR-030**: Every view in every pre-activated state MUST surface exactly one primary CTA — never zero, never two.
- **FR-031**: State copy MUST name the specific reason for the state; generic placeholder copy is not acceptable.
- **FR-032**: State transitions (empty → activating → activated) MUST be animated without flash-of-blank-content.
- **FR-033**: Visual regression tests for empty and activating states MUST be committed for all three views at all three viewports (9 test fixtures total for empty states, 9 for activating states).

### Key Entities

- **Initiative**: An organizational workstream or project represented as a node in the Galaxy. Has type, status, owning team, associated actors, and connections to other initiatives.
- **Connection**: A relationship between two initiatives (dependency, shared actor, shared work). Has edge type and direction.
- **Workflow**: A recurring coordination pattern composed of ordered steps. Each step has an owner, status, and autonomy level.
- **Decision**: A captured organizational decision with rationale, alternatives, predecessor decisions, and dependent decisions. Has author, date, and impacted systems.
- **Overlay**: A visual encoding layer applied over a view (risk, load, autonomy, ownership) that augments the base layout without changing it.
- **View State**: One of three states per view (empty, activating, activated). Transitions are data-driven (as ingest progresses) and animated.
- **Design Token**: A named, shared value (color, spacing, motion timing) that all view implementations reference rather than hardcode.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: Initiative Galaxy renders a 10k-node, 30k-edge graph at ≥30fps on both M-series Mac and a 2-year-old Windows laptop — confirmed by the CI benchmark suite.
- **SC-002**: Initiative Galaxy force layout converges within 5 seconds on a full org-scale graph — confirmed by the CI benchmark suite.
- **SC-003**: Initiative Galaxy passes three internal design reviews against the reference set; review notes are archived in `docs/design-reviews/`; the "world-class" bar is confirmed when internal reviewers cannot distinguish Galaxy from the reference product in a side-by-side.
- **SC-004**: Initiative Galaxy is demo-able for 60 seconds with zero narration — confirmed by a recorded internal demo session.
- **SC-005**: Workflow Topology renders 500 nodes with sub-second interaction at all three target viewports — confirmed by automated performance measurements.
- **SC-006**: Decision Graph surfaces a known decision via search in under 2 seconds — confirmed by automated timing tests.
- **SC-007**: All three views pass visual regression tests at three viewports for each of three states (empty, activating, activated) — 27 test fixtures committed to CI.
- **SC-008**: All three views are defensible at internal design review against their respective reference sets (Linear/Cosmograph for Galaxy, Linear project view for Topology, Confluence ADR pages for Decision Graph) — documented in design review notes.
- **SC-009**: An internal reviewer shown all three views in sequence identifies them as belonging to the same product without prompting — confirmed in cross-surface design review.
- **SC-010**: Empty and activating states are rated superior to Linear and Notion equivalents in an internal review for communicating *what will be here* and *what the operator can do* — documented in design review notes.

---

## Assumptions

- The Cognition Surface connects to the existing Context-OS backend API (Phase 1/2) via the established REST API contracts; no new backend endpoints are introduced in Phase 3.
- Authentication uses the existing Clerk JWT flow; the frontend inherits the same auth model without changes.
- The target viewport range is mobile-landscape through large display (three breakpoints: mobile-landscape ~1024×768, laptop ~1440×900, large display ~2560×1440).
- Internal design reviewers are drawn from the existing team; a contract designer is engaged only if the Galaxy qualitative kill trigger fires (not at world-class bar by week 26 of Phase 3).
- Seed graph data for development and CI benchmarks is generated synthetically at representative scale (10k+ nodes); real org data is not required until the Phase 4 dogfood test.
- "Edit" actions (node properties, decision drafting) are out of scope for all three views; read-only interaction with detail panes is the only write-adjacent surface (approval happens in the inbox, not in the views).
- The approval/inbox surface (§8.3.8) is already implemented in Phase 2 as a functional API; Phase 3 adds a UI skin over the existing API, not new approval logic.

---

## Dependencies

- **Phase 1/2 API**: Graph query endpoints (node lists, edge lists, snapshot diffs), workflow endpoints, decision endpoints — all must be live and stable before view-specific development.
- **Phase 2 Approval API**: Inbox endpoints for the UI layer of the approval surface (§8.3.8).
- **Design reviews**: Three Galaxy design reviews must be scheduled and completed before closed beta; blocking on reviewer availability.
- **Performance test graph**: Synthetic 10k-node, 30k-edge fixture must be generated before Galaxy CI benchmarks can run.

---

## Out of Scope

- 3D mode for Initiative Galaxy.
- Real-time multi-user cursors.
- Inline editing of node or decision properties within any view.
- Recurring briefing scheduling beyond weekly (delivery for §8.3.7 scheduling UI).
- Workflow editing within Workflow Topology.
- ML-driven bottleneck attribution.
- Decision drafting UI within Decision Graph.
- State copy customization by operators.
- A/B testing of state copy or CTAs.
- SSO/SAML authentication.
- Team invitations beyond a single operator (Phase 4).
- Custom integration adapters (Phase 4).
