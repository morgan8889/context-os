# Topology View — Design Review Package

**View**: Workflow Topology (US2)  
**Renderer**: React Flow v12 (`@xyflow/react`) + custom WorkflowNode + BottleneckEdge  
**Review Date**: 2026-05-20  
**Status**: Ready for design review

---

## 1. Screenshot Guide

### 1.1 Empty State
**Setup**: No workflows synced (empty API response from `/api/v1/topology/workflows`).  
**Expected**: `TopologyEmpty` renders with Framer Motion entrance fade, StateCTA "Connect your CI/CD pipeline".  
**Acceptance (FR-003)**: Empty state must communicate actionability.

### 1.2 Activating / Loading State
**Setup**: `topologyViewState === 'activating'` while `isLoading === true`.  
**Expected**: `LoadingState` spinner — 32px circular border spinner, "Loading workflows…" text.

### 1.3 Activating — Partial Data
**Setup**: `topologyViewState === 'activating'`, data available.  
**Expected**: `TopologyActivating` with partial node list rendered.

### 1.4 Activated — Full Canvas
**Setup**: Complete workflow data loaded.  
**Expected**:
- React Flow canvas fills available space (flex-1)
- MiniMap in bottom-right with status-colored nodes
- Controls panel (no interactive toggle)
- Workflow sidebar on the right (240px, border-left)
- Dagre LR layout applied (nodes positioned left-to-right by workflow stage)

### 1.5 Bottleneck Overlay
**Setup**: Workflow with a step where `latency_p95_ms > 500`.  
**Expected**:
- `WorkflowNode` with `isBottleneck=true` shows animated pulse ring (`@keyframes bottleneckPulse`)
- `BottleneckEdge` renders animated dashed stroke (`@keyframes dashOffset`)
- MiniMap: bottleneck nodes appear at `oklch(70% 0.22 55)` (amber)

### 1.6 Filter — By Team
**Setup**: Click a team filter chip in `TopologyFilters`.  
**Expected**: Canvas re-renders showing only nodes belonging to that team's workflows; sidebar reflects filtered workflow count.  
**Acceptance (SC-007)**: Filter operation client-side only, <100ms.

### 1.7 Filter — By Status
**Setup**: Click a status filter chip (healthy/degraded/blocked).  
**Expected**: Only workflows with at least one matching-status step remain visible.

### 1.8 Filter — Combined
**Setup**: Select both team and status filters.  
**Expected**: Intersection applied — only workflows matching both team AND status remain.

### 1.9 Responsive — Tablet (768–1024px)
**Setup**: Resize viewport to 900px.  
**Expected**: Sidebar narrows to 180px (via `@media (min-width: 768px) and (max-width: 1024px)`), canvas fills remaining width.

### 1.10 Responsive — Mobile (≤767px)
**Setup**: Resize viewport to 375px.  
**Expected**: Layout switches to column (`flex-direction: column`); sidebar appears below canvas at 100% width, max-height 200px, border-top instead of border-left.

### 1.11 Workflow Focus (Sidebar Click)
**Setup**: Click a workflow row in the sidebar.  
**Expected**: `fitView({ nodes: workflowNodeIds, duration: 400, padding: 0.3 })` animates camera to that workflow's nodes.

---

## 2. WorkflowNode Anatomy

Each node renders:
- **Header**: step name (truncated), workflow badge
- **Status indicator**: colored dot — healthy (`--color-status-healthy`), degraded (`--color-status-degraded`), blocked (`--color-status-blocked`)
- **Autonomy shield**: badge showing autonomy level 0–5
- **Bottleneck indicator**: amber pulse animation when `isBottleneck=true`
- **Latency**: p95 latency displayed in ms

---

## 3. BottleneckEdge Anatomy

- Normal edge: default React Flow styling
- Bottleneck edge (`data.isBottleneck=true`): animated dashed stroke using `@keyframes dashOffset`, stroke color `--color-bottleneck`

---

## 4. Filter Interaction Test Script

```
SCENARIO: Team filter isolation
GIVEN: Topology activated with workflows from teams A, B, C
WHEN: User clicks team A filter chip
THEN:
  - Only workflow nodes where workflowId ∈ team A's workflows are visible
  - visibleEdges only connects visible nodes
  - Sidebar shows filtered workflow count

SCENARIO: Clear filters
GIVEN: Team A filter active
WHEN: User clicks team A chip again (deselect) OR clicks "Clear" if present
THEN:
  - filteredWorkflowIds becomes empty Set
  - All nodes return to visible
  - Full node/edge list restored

SCENARIO: No matches
GIVEN: Both team and status filters produce no matching workflows
THEN:
  - Canvas is empty
  - Sidebar shows "No workflows match the current filters."
```

---

## 5. Acceptance Criteria

| Criterion | Spec Ref | Pass Condition |
|-----------|----------|----------------|
| Pan/zoom/filter p95 ≤ 1000ms at 500-node seed | SC-007 | Measured with React DevTools profiler |
| Filter is client-side only (no re-fetch) | FR-015 | Network tab shows no requests on filter change |
| Empty state has actionable CTA | FR-003 | CTA present and navigable |
| Responsive layout at 768px | FR-018 | Sidebar narrows to 180px |
| Responsive layout at 375px | FR-018 | Sidebar stacks below canvas |
| Colors only via CSS tokens | FR-025 | `npm run test` passes design-system.test.ts |
| TypeScript strict | FR-040 | `npm run typecheck` exits 0 |
