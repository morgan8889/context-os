# Decision Graph View — Design Review Package

**View**: Decision Graph (US3)  
**Renderer**: React Flow v12 (`@xyflow/react`) + Dagre TB layout + custom DecisionNode/DecisionEdge  
**Review Date**: 2026-05-20  
**Status**: Ready for design review

---

## 1. Screenshot Guide

### 1.1 Empty State
**Setup**: No decisions in store (empty API response).  
**Expected**: `DecisionEmpty` with Framer Motion entrance fade, StateCTA "Log your first architectural decision".  
**Acceptance (FR-003)**: Empty state must communicate actionability.

### 1.2 Placeholder State
**Setup**: `decisionViewState === 'placeholder'`.  
**Expected**: Greyed-out nodes at `--color-placeholder-grey` rendered in Dagre layout.

### 1.3 Activated — Full Graph
**Setup**: Decision data loaded, Dagre TB layout applied.  
**Expected**:
- Hierarchical top-to-bottom layout (predecessors above, dependents below)
- Nodes sized consistently (200px × 88px default)
- Decision title in 2-line CSS clamp (`-webkit-line-clamp: 2`)
- Relative date below title (e.g., "3d ago")
- Impacted-system chips (max 3 shown + "+N more" if overflow)
- NodeTooltip on hover showing full title

### 1.4 Edge Types — Predecessor (Solid)
**Setup**: Decision A was made before Decision B and B depends on A.  
**Expected**: Solid line (`stroke-dasharray: none`), default React Flow stroke color.

### 1.5 Edge Types — Alternative (Dashed 6/3)
**Setup**: Decision A and Decision B are alternatives.  
**Expected**: `stroke-dasharray: "6 3"` — longer dashes.

### 1.6 Edge Types — Dependent (Dotted 2/3)
**Setup**: Decision B is blocked by/dependent on Decision A.  
**Expected**: `stroke-dasharray: "2 3"` — tight dots.

### 1.7 Search — Active
**Setup**: Type "API" in the search box.  
**Expected**:
- 300ms debounce before Zustand dispatch
- SearchSpinner appears during fetch
- Result count badge appears: "N decisions match"
- Graph filters to matching nodes only

### 1.8 Search — Clear
**Setup**: Search query active.  
**Expected**: Clear button (`×`) appears at right of input; clicking clears query and returns full graph.

### 1.9 Cluster Collapse
**Setup**: Graph with clustered nodes (shared impacted system).  
**Expected**: Cluster toggled via `collapseCluster` action — child nodes hidden, cluster representative shows `+N` badge.

### 1.10 Decision Detail Panel
**Setup**: Click a decision node.  
**Expected**: `DecisionDetailPanel` (via `OverlayPanel`) slides in from right; shows full title, date, status badge, impacted systems list, rationale text.

---

## 2. Edge Type Visual Reference

| Type | `data.type` | `stroke-dasharray` | Visual appearance |
|------|------------|---------------------|-------------------|
| Predecessor | `"predecessor"` | `none` | Solid line |
| Alternative | `"alternative"` | `"6 3"` | Long dashes |
| Dependent | `"dependent"` | `"2 3"` | Tight dots |
| Default | other/undefined | `none` | Solid (fallback) |

---

## 3. Search Interaction Test Script

```
SCENARIO: Search with results
GIVEN: Decision Graph activated with 20 decisions
WHEN: User types "auth" in search box
THEN:
  - 300ms passes (debounce)
  - setDecisionFilters({ query: 'auth' }) dispatched to Zustand
  - SearchSpinner appears during API fetch (isSearching=true)
  - After fetch: spinner replaced by result count badge
  - Graph re-renders with only matching decisions

SCENARIO: Instant local feedback
GIVEN: User is typing in search box
WHEN: Each keypress occurs
THEN:
  - localValue updates immediately (no 300ms delay for input display)
  - Zustand store updates ONLY after 300ms debounce
  - Spinner shows ONLY after debounce fires and API call starts

SCENARIO: Clear search
GIVEN: Query "auth" active, 3 results shown
WHEN: User clicks × clear button
THEN:
  - localValue reset to ''
  - setDecisionFilters({ query: '' }) dispatched immediately
  - Full graph restored
  - Clear button disappears
  - Result badge disappears
```

---

## 4. Cluster Collapse Test Script

```
SCENARIO: Collapse a cluster
GIVEN: Cluster of 5 decisions sharing impacted system "payments"
WHEN: User activates cluster toggle
THEN:
  - 4 child nodes hidden
  - Representative node shows "+4 more" badge
  - collapseCluster(clusterId) dispatched to Zustand
  - Dagre re-layout runs on collapsed graph

SCENARIO: Expand a cluster
GIVEN: Cluster is collapsed
WHEN: User clicks representative node
THEN:
  - All child nodes restored
  - Full cluster re-renders
  - Dagre re-layout runs
```

---

## 5. Acceptance Criteria

| Criterion | Spec Ref | Pass Condition |
|-----------|----------|----------------|
| Dagre TB layout ≤ 1000 decisions | SC-006 | Layout completes in <500ms |
| Search debounce = 300ms | FR-022 | Zustand dispatch delayed 300ms from last keystroke |
| Edge types visually distinct | FR-019 | Three distinct dash patterns (solid/6-3/2-3) |
| Cluster collapse reduces node count | FR-021 | Hidden nodes removed from React Flow `nodes` array |
| Empty state has actionable CTA | FR-003 | CTA present and navigable |
| DecisionViewState union includes 'activating' | QC-008 | `tsc --noEmit` exits 0 with `placeholder\|activating\|activated` union |
| Colors only via CSS tokens | FR-025 | `npm run test` passes design-system.test.ts |
| TypeScript strict | FR-040 | `npm run typecheck` exits 0 |
