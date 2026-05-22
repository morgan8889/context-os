# Spec Review — 7bb129caede7

**Commit**: fix(phase5): pgvector codec crash, Clerk JWT hang, ForceAtlas2 settings, Sigma headless, dark canvas backgrounds
**Branch**: 5-goal-driven-ux
**Spec**: specs/005-goal-driven-ux/spec.md
**Overall**: PASS — all 14 Phase 5 FRs covered; two minor deviations from component contracts

---

## FR Coverage

| FR | Requirement | Status |
|----|-------------|--------|
| FR-001 | One-time dismissible orientation callout on Galaxy, Topology, Decisions, Inbox | PASS |
| FR-002 | Each message includes view purpose, object type, primary action | PASS |
| FR-003 | Dismissal persistent via localStorage | PASS |
| FR-004 | Overlay tooltips for Load, Risk, Autonomy, Ownership | PASS |
| FR-005 | Galaxy legend — node type and status colors | PASS |
| FR-006 | Legend collapsible + state persisted | PASS |
| FR-007 | Inbox type badge tooltips | PASS |
| FR-008 | Failure flags contextual explanation | PASS |
| FR-009 | Live Inbox badge in navigation | PASS |
| FR-010 | Help/docs link in navigation | PASS |
| FR-011 | Galaxy empty state — accurate copy + functional CTA | PASS |
| FR-012 | Decisions empty state — no broken CTA | PASS |
| FR-013 | Operator language throughout | PASS |
| FR-014 | WCAG AA contrast | UNVERIFIED — visual gate not confirmed in this commit |

---

## User Story Coverage

All five user stories are implemented. The activated-state gating for `FirstVisitCallout`
in Galaxy, Topology, and Decisions ensures the callout only appears after data is loaded,
satisfying "when the view fully loads" in acceptance scenarios US1.1–US1.4.

US5 empty state fixes: Galaxy points to `/onboarding` (functional). Decisions has no CTA
(broken link removed entirely). Both match the plan's modifications.

---

## Deviations from Component Contracts

### Deviation 1: AppShell props interface mismatch (minor)

The component contract specifies `interface AppShellProps { children: ReactNode }`.
The implementation has no props and uses `<Outlet />` internally — the correct React Router
v6 layout route pattern. Functionally correct; the contract predated the layout route
decision. No user impact.

File: `web/src/components/AppShell.tsx`

### Deviation 2: FirstVisitCallout `bottom-center` position not centered (minor)

The contract says `bottom-center` should render "inside content flow, centered".
The implementation maps it to `{ position: 'relative', zIndex: 30 }` without centering.
When rendered inside InboxView's flex-column scroll container, the 280px card aligns left.

Only `ctx_os_inbox_hint` ("Your first approval") uses `bottom-center`; the four view-level
callouts all use `bottom-left` (fixed) and render correctly.

File: `web/src/design-system/primitives/FirstVisitCallout.tsx` line 40
File: `web/src/inbox/InboxView.tsx` line 536

---

## Bug Fix Compatibility

All four infrastructure fixes are within Phase 5 scope and compatible with the spec:
- `engine.py` pgvector: backend-only, no spec impact
- `client.ts` / `main.tsx` JWT guard: enables frontend views to load correctly in dev
- `ForceLayout.tsx` / `GalaxyActivating.tsx` ForceAtlas2: Galaxy view renders without crash
- `GalaxyView.tsx` `allowInvalidContainer`: Sigma mounts correctly in headless/test environments
