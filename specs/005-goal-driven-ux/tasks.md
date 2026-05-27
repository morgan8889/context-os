# Tasks: Phase 5 — Goal-Driven UX & In-Context Guidance

**Input**: Design documents from `/specs/005-goal-driven-ux/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: No new unit/integration test tasks are generated — the spec did not
request TDD. Acceptance is verified via the `quickstart.md` scenarios plus the
Phase 5 CI gates (`tsc --noEmit`, `/verify-visual`, `/verify-brand`). These are
captured in the Polish phase.

**Organization**: Tasks are grouped by user story for independent implementation
and testing. **Only Tier A (US1–US5) is in scope for this build.** Tier B
(US6–US9) is a deferred planning track — see the final section.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- All paths are relative to the repository root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the `web/` workspace is ready; no new dependencies required.

- [ ] T001 Verify `web/` dev server runs with auth bypass: `cd web && VITE_DEV_BYPASS_AUTH=true npm run dev`; confirm `/galaxy`, `/topology`, `/decisions`, `/inbox` routes load against seed data
- [ ] T002 Confirm existing `Tooltip` primitive API in `web/src/design-system/components/Tooltip.tsx` (`{ children, content, side?, delayDuration? }`) and that `TooltipProvider` is mounted at App root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared primitives consumed by more than one user story.

**⚠️ CRITICAL**: US1 and US3 both depend on `FirstVisitCallout`. Complete this phase before starting those stories.

- [ ] T003 Create `FirstVisitCallout` primitive in `web/src/design-system/primitives/FirstVisitCallout.tsx` per `contracts/ui-components.md` Contract 1 (localStorage read on mount, Framer Motion enter/exit, Escape-to-dismiss, `position` prop)
- [ ] T004 Re-export `FirstVisitCallout` from `web/src/design-system/primitives/index.ts`

**Checkpoint**: Shared callout primitive available — US1 and US3 can begin.

---

## Phase 3: User Story 1 — First Encounter: Understanding Each View's Purpose (Priority: P1) 🎯 MVP

**Goal**: A one-time, dismissible orientation callout on first visit to each main view (FR-001–FR-003).

**Independent Test**: Clear localStorage, visit `/galaxy` → callout appears → dismiss → refresh → not shown; repeat for `/topology`, `/decisions`. (quickstart Scenario 1)

- [ ] T005 [US1] Mount `FirstVisitCallout` (key `ctx_os_visited_galaxy`) in the activated branch of `web/src/views/galaxy/GalaxyView.tsx` using the Galaxy copy from plan.md "Callout Copy Reference"
- [ ] T006 [P] [US1] Mount `FirstVisitCallout` (key `ctx_os_visited_topology`) in the activated branch of `web/src/views/topology/TopologyView.tsx`
- [ ] T007 [P] [US1] Mount `FirstVisitCallout` (key `ctx_os_visited_decisions`) in the activated branch of `web/src/views/decisions/DecisionView.tsx`

**Checkpoint**: First-visit orientation works on all three canvas views.

---

## Phase 4: User Story 2 — Feature Discoverability: The Galaxy Overlay System (Priority: P2)

**Goal**: Overlay-control tooltips + collapsible node-type/status legend (FR-004–FR-006).

**Independent Test**: Hover each overlay button → distinct tooltip; expand legend → persists across refresh. (quickstart Scenarios 2–3)

- [ ] T008 [US2] Add `OVERLAY_TOOLTIPS` copy and wrap each overlay button `div` in `<Tooltip side="right">` in `web/src/views/galaxy/OverlayControls.tsx` (copy from data-model Entity 4)
- [ ] T009 [US2] Create `GalaxyLegend` in `web/src/views/galaxy/GalaxyLegend.tsx` per Contract 3 (collapsed pill default, `ctx_os_legend_galaxy` persistence, swatches from `getComputedStyle` of `--color-node-*` / `--color-status-*` tokens)
- [ ] T010 [US2] Mount `<GalaxyLegend />` in the activated branch of `web/src/views/galaxy/GalaxyView.tsx`

**Checkpoint**: Galaxy overlays are discoverable and the legend explains the colour systems.

---

## Phase 5: User Story 3 — Approval Workflow Clarity: The Inbox (Priority: P3)

**Goal**: Per-type badge explanations, failure-flag help, first-approval callout (FR-007, FR-008).

**Independent Test**: `/inbox` shows a `?` after each type badge and the failure-flags header with explanatory tooltips; first-approval callout appears once. (quickstart Scenarios 4–5)

- [ ] T011 [US3] Create `HintTooltip` primitive in `web/src/design-system/primitives/HintTooltip.tsx` per Contract 2 (wraps `Tooltip`; `<button aria-label="More information">`; returns null on empty content) and re-export from `web/src/design-system/primitives/index.ts`
- [ ] T012 [US3] Add `INBOX_ITEM_TYPE_META` (label + tooltip from data-model Entity 5) and render a trailing `HintTooltip` after each type badge in `web/src/inbox/InboxView.tsx`
- [ ] T013 [US3] Add a trailing `HintTooltip` on the failure-flags section header in `web/src/inbox/InboxView.tsx` explaining failure flags are non-blocking AI self-checks
- [ ] T014 [US3] Mount `FirstVisitCallout` (key `ctx_os_inbox_hint`, `position="bottom-center"`) above the first card when items exist in `web/src/inbox/InboxView.tsx`

**Checkpoint**: Inbox item types and failure flags are self-explanatory.

---

## Phase 6: User Story 4 — Navigation Signals: Knowing When Attention Is Needed (Priority: P4)

**Goal**: Persistent AppShell sidebar with live Inbox pending badge and a help link (FR-009, FR-010).

**Independent Test**: With pending items, the Inbox icon shows a count on `/galaxy`; navigating to `/inbox` clears it; help link shows "Docs coming soon". (quickstart Scenario 6)

- [ ] T015 [US4] Create `AppShell` in `web/src/components/AppShell.tsx` per Contract 4 (56px sidebar, 4 `NavLink` icons, Inbox badge via `useQuery(['inbox'], …, { refetchInterval: 30_000 })` hidden on `/inbox`, `9+` cap, help link with "Docs coming soon" tooltip, `<Outlet />` content area)
- [ ] T016 [US4] Restructure `web/src/router.tsx` to wrap the four view routes in an `AppShell` parent layout route with `<Outlet />`

**Checkpoint**: Operators see pending-approval signals from any view and have a help affordance.

---

## Phase 7: User Story 5 — Honest Empty States: Accurate Expectations (Priority: P5)

**Goal**: Repair both broken empty-state CTAs and set accurate expectations (FR-011, FR-012).

**Independent Test**: Empty Galaxy shows honest copy + working "Review onboarding" → `/onboarding`; empty Decisions shows honest copy and no broken CTA. (quickstart Scenarios 7–8)

- [ ] T017 [P] [US5] Update `web/src/views/galaxy/GalaxyEmpty.tsx` copy (heading/body per plan) and point the CTA to `/onboarding`
- [ ] T018 [P] [US5] Update `web/src/views/decisions/DecisionEmpty.tsx` copy (briefing-cycle explanation) and remove the broken `StateCTA`

**Checkpoint**: No broken CTAs; empty states distinguish processing vs. no-data.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Validation against CI gates and accessibility.

- [ ] T019 Verify WCAG AA 4.5:1 contrast for all new guidance text (FR-013 operator language, FR-014 contrast) across callouts, tooltips, legend, badge
- [ ] T020 Run `cd web && npm run typecheck` — zero TypeScript errors in strict mode
- [ ] T021 Walk all 8 Tier A scenarios in `quickstart.md` against the running dev server
- [ ] T022 Run `/verify-brand` and `/verify-visual`; achieve a `pass` verdict before PR

---

## Dependencies & Execution Order

- **Setup (Phase 1)** → no dependencies.
- **Foundational (Phase 2)** → blocks US1 and US3 (shared `FirstVisitCallout`).
- **US1 (P1)** → after Phase 2. MVP.
- **US2 (P2)** → after Phase 1 (no dependency on US1).
- **US3 (P3)** → after Phase 2.
- **US4 (P4)** → after Phase 1; `AppShell` is independent but its left sidebar (56px) is assumed by `FirstVisitCallout` bottom-left offset — cosmetic only, not a hard dependency.
- **US5 (P5)** → after Phase 1; fully independent.
- **Polish (Phase 8)** → after all desired stories complete.

### Parallel Opportunities

- T006, T007 (US1 topology/decisions mounts) run in parallel.
- T017, T018 (US5 empty states) run in parallel.
- US2 and US5 can be developed in parallel with US1/US3 once Phase 1 is done.

---

## Implementation Strategy

1. Phase 1 (Setup) → Phase 2 (Foundational).
2. US1 → validate independently → MVP.
3. Add US2, US3, US4, US5 in priority order (or in parallel if staffed), validating each.
4. Phase 8 polish → CI gates → PR.

---

# Tier B — Process Re-Architecture (DEFERRED — Phase 6/7 planning track)

> **NOT in this build.** US6–US9 / FR-015–022 engage all six NON-NEGOTIABLE
> constitution principles and cannot be implemented from this spec pack. The
> tasks below are **planning/governance tasks**, not implementation tasks. They
> produce the dedicated Phase 6/7 spec, not running code.

- [ ] D001 Author a dedicated Phase 6/7 spec (`/speckit.specify`) for process re-architecture, promoting US6–US9 and FR-015–022 from seed to first-class requirements
- [ ] D002 Run `/speckit.plan` for the Phase 6/7 spec and **clear the Tier B Constitution Check table** in `plan.md` (Principles I, II, III, V, VI, VII + durable orchestration)
- [ ] D003 Define autonomy-level declarations (0–5) for the baseline, redesign, and optimisation agents (Principle III); confirm recommend-only / approval-gated posture
- [ ] D004 Map Tier B entities (ProcessBaseline, ProcessBlueprint, ImplementationMilestone, KpiSnapshot) onto the core ontology as graph nodes/edges with provenance (Principles II, VII)
- [ ] D005 Commit evaluation suites for each new agent/workflow before any non-dev deploy (Principle V); set CI gate thresholds
- [ ] D006 Specify OTEL-conformant telemetry attributes for monitoring/KPI capture (Principle VI) and a durable orchestrator (Temporal/LangGraph) for implementation tracking
