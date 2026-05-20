# Galaxy View — Design Review Package

**View**: Initiative Galaxy (US1)  
**Renderer**: Sigma.js v3 (WebGL) + Graphology + ForceAtlas2 Web Worker  
**Review Date**: 2026-05-20  
**Status**: Ready for design review

---

## 1. Screenshot Guide

### 1.1 Empty State
**Setup**: Navigate to Galaxy view with no initiatives synced (clear `sync_checkpoints`).  
**Expected**: Dark canvas (`--color-galaxy-bg`), faint SVG spiral silhouette at 15% opacity, StateCTA button "Adjust source scope" centered.  
**Acceptance (FR-003)**: Empty state must communicate actionability — CTA must be present.

### 1.2 Activating State
**Setup**: Trigger a partial data load (`/api/v1/galaxy/nodes?page=1`).  
**Expected**: Sigma canvas with greyed-out stub nodes pulsing at `--color-placeholder-grey`, ForceAtlas2 running, `GalaxyActivating` overlay showing initiative count.  
**Acceptance (SC-003)**: Activating state appears within 100ms of data arriving.

### 1.3 Activated — Default (No Overlay)
**Setup**: Full dataset loaded, ForceAtlas2 converged.  
**Expected**: Colorized nodes by type (`--color-node-goal`, `--color-node-project`, `--color-node-signal`, `--color-node-artifact`), edges at `oklch(35% 0 0)`, labels at 11px weight-500.  
**Acceptance (SC-001)**: Frame paint p95 ≤ 33ms at 1000-node seed.

### 1.4 Activated — Risk Overlay
**Setup**: Click Overlay Controls → "Risk".  
**Expected**: High-risk nodes (`riskScore ≥ thresholds.high`) turn `--color-status-at-risk`; medium-risk nodes turn `--color-status-paused`; low-risk unchanged.  
**Acceptance (SC-008)**: Overlay switch re-renders within 1 frame cycle (<16ms).

### 1.5 Activated — Load Overlay
**Setup**: Click Overlay Controls → "Load".  
**Expected**: Bottleneck nodes (`edgeCount ≥ 10`) turn `--color-bottleneck`; others unchanged.

### 1.6 Activated — Autonomy Overlay
**Setup**: Click Overlay Controls → "Autonomy".  
**Expected**: High-autonomy nodes (`autonomyLevel ≥ 4`) turn `--color-status-at-risk`; lower autonomy nodes turn `--color-node-signal`.

### 1.7 Activated — Ownership Overlay
**Setup**: Click Overlay Controls → "Ownership".  
**Expected**: Nodes colored by initiative status using `STATUS_COLOR_MAP` (active/paused/at_risk/complete).

### 1.8 Lasso Selection (Multi-select)
**Setup**: Click-drag on canvas (no ctrl/shift required).  
**Expected**: SVG lasso path in `--color-lasso-stroke` dashed, selected nodes highlighted, unselected nodes dim with empty labels.  
**Acceptance (SC-009)**: Lasso selection completes point-in-polygon test in <16ms for 1000 nodes.

### 1.9 Node Detail Pane — Desktop
**Setup**: Click a node.  
**Expected**: Right-side `NodeDetailPane` slides in (Framer Motion x: 320→0), shows node label, type badge, status, owner team, actor count, risk score, autonomy level, edge count.

### 1.10 Node Detail Pane — Mobile (≤430px)
**Setup**: Resize to 430px wide, click a node.  
**Expected**: `NodeDetailPane` repositions to bottom-sheet via CSS override (bottom: 0, width: 100%, border-radius: 16px 16px 0 0, max-height: 60vh).

---

## 2. Time-Travel Animation Recording Instructions

**Prerequisites**: At least 2 galaxy snapshots in store (`galaxySnapshots.length ≥ 2`).

**Recording script**:
```
1. Open Galaxy view with historical dataset (use seeded multi-snapshot fixture)
2. Confirm TimeTravelBar is visible at the bottom (hidden at ≤430px landscape)
3. Start screen recording (QuickTime or OBS)
4. Slowly drag the TimeTravelBar scrubber from left to right
   — Observe: ForceAtlas2 pauses, graph transitions to snapshot via graphology.import()
   — Observe: Sigma camera animates to new positions over 500ms
5. Drag back to present
6. Stop recording
```

**Expected behavior per FR-042**: Scrubber position (GSAP `useGSAP` handle) updates synchronously with drag; graph snapshot import triggers `sigma.refresh()`.

---

## 3. Lasso Interaction Test Script

```
SCENARIO: Multi-select via lasso
GIVEN: Galaxy activated with ≥5 visible nodes
WHEN: User clicks and drags diagonally across canvas
THEN:
  - SVG lasso path renders with stroke: var(--color-lasso-stroke), fill: var(--color-lasso-fill)
  - Path is dashed (stroke-dasharray="4 4")
  - On mouseup: pointInPolygon test selects enclosed nodes
  - Zustand galaxySelection.nodeIds updated
  - Selected nodes: highlighted=true, non-selected: label='', zIndex=0
  - All edges hidden when hasSelection=true

SCENARIO: Click-stage clears selection
GIVEN: Nodes are selected via lasso
WHEN: User clicks empty canvas
THEN:
  - clearGalaxySelection() called
  - setFocusedNodeId(null) called
  - All nodes return to normal rendering

SCENARIO: Single node click (no drag)
GIVEN: Lasso is inactive
WHEN: User clicks a node
THEN:
  - setFocusedNodeId(nodeId) called
  - NodeDetailPane slides in
  - No lasso path renders
```

---

## 4. Acceptance Criteria

| Criterion | Spec Ref | Pass Condition |
|-----------|----------|----------------|
| Frame paint p95 ≤ 33ms (≥30fps) | SC-001 | Benchmark at 1000-node seed |
| Galaxy layout converges ≤ 5s | SC-002 | ForceAtlas2 supervisor stops within 5s on CI GPU |
| Activating state appears ≤ 100ms | SC-003 | Measured from first API response to first Sigma render |
| Overlays switch in <16ms | SC-008 | nodeReducer recomputed in 1 frame |
| Lasso selection <16ms for 1000 nodes | SC-009 | pointInPolygon benchmark |
| Time-travel scrub smooth | SC-010 | 60fps during scrub, no frame drops >33ms |
| Empty state has actionable CTA | FR-003 | "Adjust source scope" button present and linked |
| Colors only via CSS tokens | FR-025 | `npm run test` passes design-system.test.ts |
