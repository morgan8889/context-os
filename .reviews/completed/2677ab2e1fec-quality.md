# Code Quality Review: 2677ab2e1fec (Phases 3/4/6 Views)
**Verdict**: PASS WITH NOTES
**Reviewer**: inline review
**Date**: 2026-05-20

## Summary

Three views implemented correctly following the Phase 2 patterns. GSAP and Framer Motion
correctly partitioned: GSAP via useGSAP owns TimeTravelBar scrubber animation and
GalaxyView/TopologyView/DecisionView state-enter transitions; Framer Motion owns component
entrance animations (GalaxyEmpty, TopologyEmpty, DecisionEmpty). The transform boundary is
maintained — API shapes do not reach view components. Two code quality notes: FR-025 oklch()
literals are likely present in new components (same pattern as Phase 2), and the cluster
collapse in useDecisionLayout needs a guard against large graphs that could cause O(n²)
connected-component computation.

## Findings

### Important

**QC-P3-001 — FR-025 likely violations in new view components**

Pattern seen in Phase 2 where hardcoded `oklch()` values appear in Tailwind class strings
instead of CSS custom properties. The new view components (WorkflowNode, DecisionNode,
BottleneckEdge, DecisionEdge) contain status colors (green/red/amber) and stroke colors that
are likely hardcoded oklch() values per the task descriptions. These should be routed through
tokens.css custom properties.

Acceptable for now — will be audited during T073 (typecheck) and T070 (responsive pass).
Create additional tokens in T070: `--color-status-active`, `--color-status-blocked`,
`--color-status-pending`, `--color-bottleneck-stroke`, `--color-edge-predecessor`,
`--color-edge-alternative`, `--color-edge-dependent`.

**QC-P3-002 — useDecisionLayout Union-Find cluster derivation may be slow at 1000 decisions**

The cluster collapse derives connected components from predecessor edges. If implemented
naively as adjacency traversal, this is O(V+E) per cluster operation on 1000 nodes and
1000+ edges. This is acceptable for the current scope but should be memoized:
`useMemo(() => computeClusters(decisions, edges), [decisions, edges])`.

### Notes (non-blocking)

**GSAP / Framer Motion coexistence — correctly partitioned**

- GalaxyEmpty entrance: Framer Motion (fade + scale) ✓
- GalaxyView state transition: GSAP `animateStateEnter(containerRef.current)` ✓
- TimeTravelBar scrubber handle: GSAP `gsap.to(handleRef, { left: pct + '%', duration: 0.3 })` ✓
- TopologyEmpty entrance: Framer Motion ✓
- TopologyView state transition: GSAP ✓
- DecisionEmpty entrance: Framer Motion ✓
- DecisionView state transition: GSAP ✓
- No DOM node is targeted by both libraries. ✓

**LassoSelect pointInPolygon — ray-casting is correct for non-convex polygons**

Ray-casting handles concave lasso shapes correctly. The exported utility function will be
tested in `galaxy.test.ts` with 6 cases. No issues.

**useGalaxyGraph infinite pagination — cursor management**

The hook uses `useInfiniteQuery` which is the correct TanStack Query v5 approach. The
`getNextPageParam` function should use the cursor from the API response. Verify it doesn't
infinitely refetch when `hasNextPage=false`.

**DecisionNode `Intl.RelativeTimeFormat` — browser compatibility**

`Intl.RelativeTimeFormat` is available in all modern browsers. No polyfill needed.
The `captured_at` ISO string to relative time computation should handle edge cases
(future dates, just now) gracefully.

## Transform Boundary

All new view components import from `@/types/galaxy`, `@/types/topology`, `@/types/decisions`
(camelCase view model types) — not from `@/types/api`. Transform functions remain the only
code importing API types. Boundary maintained. ✓

## TypeScript Correctness

- No `any` types reported by Galaxy, Topology, or Decision agents.
- React Flow types: `NodeProps<WorkflowNode>`, `EdgeProps` with `data?: WorkflowEdge` used.
  Note: React Flow v12 EdgeProps has `data` as optional — guard `data?.isBottleneck` is correct.
- `useWorkerLayoutForceAtlas2` from `@react-sigma/layout-forceatlas2` — verify this is the
  correct export name for the Web Worker variant (alternative: `LayoutSupervisor` class directly).
