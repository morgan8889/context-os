# Spec Review — 2d959d6e3d5b

**Commit**: feat(phase5): UI clarity & in-context guidance — first-visit callouts, overlays, inbox hints  
**Plan**: .claude/plans/temporal-brewing-cat.md  
**Overall**: PASS WITH NOTES

## FR Coverage

| FR | Story | Requirement | Status |
|----|-------|-------------|--------|
| FR-001 | US1 | Galaxy first-visit callout (ctx_os_visited_galaxy) | ✅ GalaxyView.tsx:240 |
| FR-002 | US1 | Topology first-visit callout (ctx_os_visited_topology) | ✅ TopologyView.tsx |
| FR-003 | US1 | Decisions first-visit callout (ctx_os_visited_decisions) | ✅ DecisionView.tsx |
| FR-004 | US1 | Inbox first-visit callout (ctx_os_visited_inbox) | ✅ InboxView.tsx |
| FR-005 | US2 | Overlay button tooltips — Load, Risk, Autonomy, Ownership | ✅ OverlayControls.tsx |
| FR-006 | US2 | GalaxyLegend panel — node type + status swatches | ✅ GalaxyLegend.tsx |
| FR-007 | US2 | Legend collapsed/expanded persisted to localStorage | ⚠️ See NOTE-1 |
| FR-008 | US3 | Inbox type badge HintTooltips per item type | ✅ InboxView.tsx |
| FR-009 | US3 | Failure-flag HintTooltip | ✅ InboxView.tsx |
| FR-010 | US3 | ctx_os_inbox_hint first-approval callout | ✅ InboxView.tsx (outside `<ul>`) |
| FR-011 | US4 | AppShell Inbox badge (live count from TanStack Query) | ✅ AppShell.tsx |
| FR-012 | US4 | Badge clears when on /inbox route | ✅ AppShell.tsx:134 |
| FR-013 | US4 | Help link at sidebar bottom | ✅ AppShell.tsx |
| FR-014 | US5 | Galaxy empty-state CTA fixed (→ /onboarding) | ✅ GalaxyEmpty.tsx |
| FR-015 | US5 | Decisions empty-state broken CTA removed | ✅ DecisionEmpty.tsx |

## Notes

**NOTE-1** (GalaxyLegend localStorage init):  
`expanded` initializes to `false`, then `useEffect` reads localStorage — same async-read pattern fixed in `FirstVisitCallout` in prior commit. Users who previously expanded the legend will see a collapsed-then-expanded flash on first render. Not blocking — functionality correct after mount; state does persist correctly across page loads.

**NOTE-2** (router.tsx `Protected` helper):  
Commit message states "router.tsx: dead Protected helper removed" but the `Protected` function at router.tsx:27 is still present in the file. Usage correctly migrated to `ProtectedRoute` from App.tsx, but the unused function remains. Low severity — TypeScript won't complain, no runtime impact.

## Verdict: PASS WITH NOTES

All 15 FRs satisfied. Two minor notes; neither blocks shipping.
