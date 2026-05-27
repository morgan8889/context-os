# Implementation Plan: Phase 5 — Goal-Driven UX & In-Context Guidance

**Branch**: `5-goal-driven-ux` | **Date**: 2026-05-21 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/005-goal-driven-ux/spec.md`

---

## Summary

Beta users arrive post-activation and find the four canvas views (Galaxy,
Topology, Decisions, Inbox) unintuitive: nodes render but users cannot answer
"what am I looking at?" or "what should I do here?" Phase 5 resolves this
through five targeted interventions: per-view first-visit callouts (dismissed
to localStorage), Galaxy overlay explanations and a node-type legend, Inbox
item-type clarity with HintTooltips, an AppShell sidebar with a live pending
badge, and repair of two broken empty-state CTAs. No backend changes; all
work is in `web/`.

---

## Strategic Amendment (2026-05-22)

This plan is amended to align with the product objective:
re-architect existing processes for AI, implement safely, and measure impact.

Phase 5 remains the UX comprehension layer. Additional implementation planning
must account for cross-layer work that extends beyond frontend copy/interaction:

1. Process Baseline Layer: ingest and model current-state workflows.
2. Re-Architecture Layer: generate AI-native process blueprints.
3. Implementation Control Layer: milestone planning, ownership, risk gates.
4. Monitoring + Metrics Layer: KPI baseline/post-change instrumentation.
5. Optimisation Layer: drift detection and adjustment recommendations.

Impact on planning:
- Prior "no backend changes" constraint applies only to the existing Phase 5 UX scope.
- New transformation capabilities require backend/API/data model work in follow-on phases.
- This spec pack should be treated as the seed for Phase 6/7 planning.

---

## Technical Context

**Language/Version**: TypeScript 5.x strict  
**Primary Dependencies**: React 19, Vite 6, Framer Motion 11, TanStack Query v5,
Zustand v5, Radix UI (via shadcn/ui), React Router v6  
**Storage**: Browser `localStorage` (orientation dismissal, legend state)  
**Testing**: Vitest + `@testing-library/react`; Playwright visual regression  
**Target Platform**: SPA served by Vite dev server (:5173); production Vite build  
**Project Type**: Frontend web application — `web/` workspace  
**Performance Goals**: All animations ≤ 200ms (Framer Motion everyday tier);
tooltip open delay 300–500ms (Radix default); localStorage reads synchronous on
mount (no visible flash)  
**Constraints**: No backend API changes; no new routes; no new dependencies unless
strictly necessary; WCAG AA 4.5:1 contrast for all new text  
**Scale/Scope (Tier A only)**: 11 files modified/created; 5 user stories
(US1–US5); ≤3 new primitives. Tier B (US6–US9) is deferred and out of this
plan's implementation scope.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Scope of this gate**: This plan implements **Tier A only** (operator-comprehension
UX, US1–US5). Tier A is assessed below and passes cleanly. **Tier B** (process
re-architecture, US6–US9) is explicitly **out of this plan's implementation scope**;
its Constitution Check is **DEFERRED** to a dedicated Phase 6/7 plan. The Tier B
principle engagements are enumerated so the deferral is explicit and auditable —
not silently ignored.

### Tier A assessment (this plan's implementation scope)

**Principle I — Intent Over Tasks**: ✅ Not applicable (UI teaching surface,
not goal/task modelling).

**Principle II — Persistent Semantic Memory (NON-NEGOTIABLE)**: ✅ Compliant.
No new backend entities. localStorage is explicitly documented as a deliberate
scope choice, not a violation of server-side persistence — orientation messages
are transient UI state, not organisational memory.

**Principle III — Human Governance, AI Execution (NON-NEGOTIABLE)**: ✅ Not
applicable. No new AI agents or autonomy declarations.

**Principle IV — Visualization as Cognition**: ✅ **Directly served.** The
entire phase improves the usability of the topology-first surfaces. No CRUD
forms introduced as primary interfaces. Empty states remain topology-adjacent
surfaces, not table/form replacements.

**Principle V — Evaluation-First (NON-NEGOTIABLE)**: ✅ Not applicable. No
new AI agent roles or workflow orchestration.

**Principle VI — Observable Autonomy (NON-NEGOTIABLE)**: ✅ Not applicable.
No new agent actions or telemetry changes.

**Principle VII — Domain-Adapter Extensibility**: ✅ Not applicable. Frontend
primitives do not modify core ontology.

**Architectural Constraints**: ✅ No persistence layer changes; no workflow
orchestration changes; no telemetry schema changes; no integration ingestion
changes.

**Tier A Verdict**: No violations. No Complexity Tracking entries required.

### Tier B engagements (DEFERRED — must be cleared by the Phase 6/7 plan)

The strategic objective (US6–US9, FR-015–022) is **not buildable under this plan**
because it touches every NON-NEGOTIABLE principle. The Phase 6/7 plan MUST resolve
each before any Tier B implementation:

| Principle | How Tier B engages it | Required before Tier B build |
|-----------|----------------------|------------------------------|
| I. Intent Over Tasks | Processes/blueprints/milestones must trace to Goals/Initiatives | Map Tier B entities onto the intent graph; no orphan process records |
| II. Persistent Semantic Memory | ProcessBaseline, Blueprint, Milestone, KpiSnapshot are organisational memory | Model as typed graph nodes/edges with provenance (not client-side state) |
| III. Human Governance, AI Execution | Redesign agents declare per-step autonomy (0–5); approval-gated at ≤3 | Declare autonomy levels; gate execution; publish escalation criteria for 4–5 |
| V. Evaluation-First | New baseline/redesign/optimisation agents + workflows | Commit eval suites (golden inputs, failure modes, governance edge cases) before any non-dev deploy |
| VI. Observable Autonomy | Monitoring (FR-020) emits override/intervention/latency telemetry | OTEL-conformant traces with agent identity, autonomy level, governance markers |
| VII. Domain-Adapter Extensibility | "Process", "blueprint", "KPI" are domain concepts | Express as adapters onto core ontology, not core-schema forks |
| Arch: Durable orchestration | Implementation tracking is a long-running workflow | Use Temporal/LangGraph (durable), not in-memory |

**Tier B Verdict**: GATE DEFERRED. This plan does not authorise Tier B work. The
Phase 6/7 plan is the gate of record for the table above.

---

## Project Structure

### Documentation (this feature)

```text
specs/005-goal-driven-ux/
├── plan.md              ← This file
├── spec.md              ← Feature specification (Tier A + Tier B seed)
├── research.md          ← Technical decisions (8 Tier A + 4 Tier B seed)
├── data-model.md        ← Tier A client-side entities (6) + Tier B target entities (4)
├── quickstart.md        ← Integration scenarios (8 Tier A + 5 Tier B target)
├── contracts/
│   ├── ui-components.md          ← Tier A component interface contracts (5)
│   └── process-transformation.md ← Tier B contract surface (DEFERRED stub)
└── tasks.md             ← Tier A executable tasks + Tier B deferred planning track
```

### Source Code

```text
web/src/
├── components/
│   └── AppShell.tsx                           ← CREATE (US4)
├── design-system/
│   └── primitives/
│       ├── FirstVisitCallout.tsx              ← CREATE (US1)
│       ├── HintTooltip.tsx                    ← CREATE (US3)
│       └── index.ts                           ← MODIFY (re-export new primitives)
├── views/
│   ├── galaxy/
│   │   ├── GalaxyView.tsx                     ← MODIFY (mount FirstVisitCallout + GalaxyLegend)
│   │   ├── GalaxyLegend.tsx                   ← CREATE (US2)
│   │   ├── GalaxyEmpty.tsx                    ← MODIFY (fix CTA copy + link) (US5)
│   │   └── OverlayControls.tsx                ← MODIFY (add Tooltip per button) (US2)
│   ├── topology/
│   │   └── TopologyView.tsx                   ← MODIFY (mount FirstVisitCallout) (US1)
│   └── decisions/
│       ├── DecisionView.tsx                   ← MODIFY (mount FirstVisitCallout) (US1)
│       └── DecisionEmpty.tsx                  ← MODIFY (fix CTA copy, remove broken link) (US5)
├── inbox/
│   └── InboxView.tsx                          ← MODIFY (type tooltips, failure hint, first-approval callout) (US3)
└── router.tsx                                 ← MODIFY (add AppShell layout route) (US4)
```

---

## Phase 0: Research Findings Summary

All technical decisions documented in `research.md`. Key resolved questions:

1. **localStorage vs backend** → localStorage (no backend round-trip at beta
   scale; acceptable cross-device inconsistency).
2. **FirstVisitCallout state** → Self-contained `useState` + `useEffect`; no
   Zustand integration.
3. **HintTooltip** → Wraps existing `Tooltip` component; no Radix provider
   duplication.
4. **AppShell** → New component; router restructured with layout route pattern.
5. **Inbox badge data** → Same `['inbox']` query key as InboxView; TanStack Query
   deduplicates.
6. **Empty state CTAs** → Copy-only fix; Galaxy → `/onboarding`; Decisions →
   remove CTA.

---

## Phase 1: Component Design

### New Primitives

#### `FirstVisitCallout` — `web/src/design-system/primitives/FirstVisitCallout.tsx`

```tsx
interface FirstVisitCalloutProps {
  storageKey: string;
  title: string;
  description: string;
  dismissLabel?: string;      // default: "Got it"
  position?: 'bottom-left' | 'bottom-center'; // default: 'bottom-left'
}
```

- Reads localStorage on mount; returns `null` if key already set
- Framer Motion `AnimatePresence` + `motion.div` for enter/exit
- Dismiss on button click or Escape key
- Fixed position: `bottom: 24px; left: calc(56px + 24px)` (clears AppShell)
- z-index: 30 (below AppShell z-40, above canvas content)
- 280px wide, white card, `var(--shadow-panel)`

#### `HintTooltip` — `web/src/design-system/primitives/HintTooltip.tsx`

```tsx
interface HintTooltipProps {
  content: string;
  side?: 'top' | 'right' | 'bottom' | 'left'; // default: 'top'
}
```

- Wraps existing `Tooltip` from `web/src/design-system/components/Tooltip.tsx`
- Renders `<button type="button" aria-label="More information">` with 12px `?` circle
- Hover-only (300ms delay via `delayDuration` prop on Tooltip)
- Returns `null` if `content` is empty

### New View Components

#### `GalaxyLegend` — `web/src/views/galaxy/GalaxyLegend.tsx`

- Fixed bottom-right, z-20; collapsed to pill `"◈ Legend"` by default
- localStorage key `ctx_os_legend_galaxy` for expand state
- Color swatches from `getComputedStyle(document.documentElement).getPropertyValue(tokenName)`
- Reads `--color-node-{goal,project,signal,artifact}` and `--color-status-{active,at_risk,paused,complete}`

#### `AppShell` — `web/src/components/AppShell.tsx`

- 56px fixed left sidebar, z-40, `oklch(10% 0 0)` background
- 4 nav icons using React Router `NavLink` with `aria-current="page"` on active
- Inbox badge: `useQuery(['inbox'], fetchInboxItems)` with `refetchInterval: 30_000`
  - Badge shown when `count > 0` and active route ≠ `/inbox`
  - Badge displays count; `"9+"` when count > 9
- Docs help link: `<a href="#" target="_blank" rel="noopener noreferrer">`
  with `Tooltip content="Docs coming soon"`
- Content area: `<div className="ml-14 h-screen overflow-hidden"><Outlet /></div>`

### Modified Components

#### `OverlayControls` modifications
- Import `Tooltip` from `@/design-system/components/Tooltip`
- Wrap each button's outer `div` in `<Tooltip content={TOOLTIP_COPY[type]} side="right">`
- Add `OVERLAY_TOOLTIPS` const with copy for all 4 types

#### `GalaxyView` modifications
- Import `FirstVisitCallout` and `GalaxyLegend`
- Mount `<FirstVisitCallout storageKey="ctx_os_visited_galaxy" ... />` inside
  the `activated` branch
- Mount `<GalaxyLegend />` inside the `activated` branch

#### `TopologyView` and `DecisionView` modifications
- Import `FirstVisitCallout`
- Mount inside respective `activated` branch with view-specific copy

#### `InboxView` modifications
- Import `HintTooltip` and `FirstVisitCallout`
- Add trailing `<HintTooltip>` after each type badge label
- Add trailing `<HintTooltip>` after failure-flags section header
- Add `<FirstVisitCallout storageKey="ctx_os_inbox_hint" position="bottom-center" ...>`
  above first card when items exist

#### `GalaxyEmpty` modifications
- Heading: "Your galaxy is taking shape"
- Body: "Context-OS is reading your connected sources. Initiatives will appear here as they're discovered — this usually takes a few minutes after your first ingest completes."
- CTA label: "Review onboarding", `onClick={() => navigate('/onboarding')}`

#### `DecisionEmpty` modifications
- Add heading: "Decisions accumulate over time"
- Body: "Context-OS proposes decisions from briefing reviews — each approval becomes a node here. After your first briefing cycle, decisions will appear automatically."
- Remove `<StateCTA>` entirely (broken link removed, no replacement CTA)

#### `router.tsx` modifications
- Import `AppShell` and `Outlet`
- Add parent layout route wrapping the 4 view routes

---

## Callout Copy Reference

| View | Storage Key | Title | Description |
|------|------------|-------|-------------|
| Galaxy | `ctx_os_visited_galaxy` | "Your Initiative Galaxy" | "Each node is an initiative — a coordinated effort. Click any node to open its detail. Use the overlay controls (top-right) to colour the galaxy by Load, Risk, Autonomy, or Ownership." |
| Topology | `ctx_os_visited_topology` | "Workflow Topology" | "Shows how work moves across your team. Each row in the sidebar is a workflow; click it to navigate the canvas to that workflow. Status colours show where things are flowing or blocked." |
| Decisions | `ctx_os_visited_decisions` | "Decision Graph" | "Every architectural decision is captured here with rationale and alternatives. Search by keyword; click any node to read the full context. Edges show predecessor and dependent relationships." |
| Inbox | `ctx_os_visited_inbox` | "Your Approval Queue" | "Context-OS drafts briefings, proposes dependencies, and flags risks for your review. Approve to add to the knowledge graph; reject with a reason to send back to the AI." |
| Inbox first approval | `ctx_os_inbox_hint` | "Your first approval" | "Read the summary, check for failure flags, then approve or reject with a reason." |

---

## Complexity Tracking

> No Constitution violations — table not required.

---

## Verification

```bash
# Dev server
cd web && VITE_DEV_BYPASS_AUTH=true npm run dev

# US1 — First-visit callouts
# 1. localStorage.clear() in DevTools
# 2. /galaxy → callout appears → "Got it" → gone → refresh → not shown

# US2 — Galaxy overlay tooltips + legend
# 1. Hover Load/Risk/Autonomy/Ownership buttons → tooltip appears right side
# 2. Click "◈ Legend" → legend expands → refresh → persists

# US3 — Inbox type clarity
# 1. /inbox → ? icon after each type badge → hover → tooltip
# 2. ? after "Failure flags" header → hover → tooltip

# US4 — AppShell badge + help link
# 1. /galaxy → badge on Inbox icon if pending items
# 2. /inbox → badge gone
# 3. ? icon at sidebar bottom → tooltip "Docs coming soon"

# US5 — Empty state CTAs
# 1. Empty galaxy → new copy, "Review onboarding" → /onboarding
# 2. Empty decisions → new copy, no broken CTA button

# TypeScript
cd web && npm run typecheck

# Visual + brand gates
/verify-brand
```
