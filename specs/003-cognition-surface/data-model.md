# Data Model: Phase 3 — Cognition Surface

**Feature**: 003-cognition-surface  
**Date**: 2026-05-19  
**Depends on**: Phase 1 graph/vector/relational stores, Phase 2 approval_items + briefing_runs

---

## Overview

Phase 3 is a read-only frontend. It does not introduce new backend tables or graph mutations.
All data originates from the Phase 1/2 backend API and is transformed at the frontend layer
into view-specific shapes. This document defines those frontend view models — the TypeScript
types that mediate between raw API responses and each view renderer.

---

## Core Ontology Mapping

The three views consume different projections of the same underlying graph:

| Backend Entity | Frontend View | View Model |
|---|---|---|
| `Node {type: 'Initiative'}` | Galaxy | `InitiativeNode` |
| `DEPENDS_ON / SHARED_ACTOR / SHARED_WORK` edges | Galaxy | `InitiativeEdge` |
| `Node {type: 'Workflow'}` + `WorkflowStep` | Topology | `WorkflowNode` + `WorkflowEdge` |
| `Node {type: 'Decision'}` + decision edges | Decision Graph | `DecisionNode` + `DecisionEdge` |
| `ApprovalItem {item_type: 'briefing_draft'}` | Inbox (Phase 2 surface) | `ApprovalItem` |

---

## View Models

### Initiative Galaxy

#### `InitiativeNode`

The atomic unit of the Galaxy view. Maps to a Graphology node entry and a Sigma renderer node.

```typescript
interface InitiativeNode {
  id: string;                    // AGE node UUID
  label: string;                 // initiative name
  type: InitiativeType;          // 'goal' | 'project' | 'signal' | 'artifact'
  status: InitiativeStatus;      // 'active' | 'paused' | 'complete' | 'at_risk'
  ownerTeam: string | null;      // team identifier
  actorCount: number;            // number of associated actors (for load overlay)
  riskScore: number | null;      // 0.0–1.0 (for risk overlay); null if not scored
  autonomyLevel: number | null;  // 0–5 (for autonomy overlay)
  edgeCount: number;             // number of connections (for layout weight)
  // Graphology / Sigma layout attributes (mutable by ForceAtlas2)
  x: number;
  y: number;
  size: number;                  // derived from edgeCount for visual weight
  // View state
  viewState: NodeViewState;      // 'activated' | 'activating' | 'placeholder'
}

type InitiativeType = 'goal' | 'project' | 'signal' | 'artifact';
type InitiativeStatus = 'active' | 'paused' | 'complete' | 'at_risk';
type NodeViewState = 'activated' | 'activating' | 'placeholder';
```

#### `InitiativeEdge`

Maps to a Graphology edge entry. Edge type determines visual encoding.

```typescript
interface InitiativeEdge {
  id: string;                    // composite: `${sourceId}-${targetId}-${type}`
  source: string;                // InitiativeNode.id
  target: string;                // InitiativeNode.id
  type: EdgeType;                // drives visual encoding in reducers
  weight: number;                // 1.0 default; higher = thicker edge
}

type EdgeType = 'depends_on' | 'shared_actor' | 'shared_work' | 'placeholder';
```

#### `GalaxySnapshot`

A point-in-time export of the full graph, used for time-travel scrubbing.
Produced by `graphology.export()` and stored as JSON in Zustand time-travel state.

```typescript
interface GalaxySnapshot {
  timestamp: string;             // ISO-8601
  nodes: InitiativeNode[];
  edges: InitiativeEdge[];
  layoutSeed: number;            // ForceAtlas2 seed for deterministic replay
}
```

#### `OverlayConfig`

Describes which overlay is active and its threshold settings.

```typescript
interface OverlayConfig {
  type: OverlayType | null;      // null = no overlay
  thresholds: {
    low: number;
    high: number;
  };
}

type OverlayType = 'load' | 'risk' | 'autonomy' | 'ownership';
```

#### `SelectionSet`

The set of currently lasso-selected node IDs. Stored in Zustand; passed to Sigma
reducers via `sigma.setSetting('nodeReducer', fn)` to highlight/dim nodes.

```typescript
interface SelectionSet {
  nodeIds: Set<string>;
  source: 'lasso' | 'click' | 'filter';
}
```

---

### Workflow Topology

#### `WorkflowNode`

A step within a workflow. Rendered as a React Flow custom node component.
Status, ownership, and autonomy markers are rendered within the node.

```typescript
interface WorkflowNode {
  id: string;                    // AGE node UUID
  workflowId: string;            // parent workflow identifier
  label: string;                 // step name
  stepIndex: number;             // position in workflow (0-based)
  status: StepStatus;            // drives status badge color
  ownerTeam: string | null;
  ownerActor: string | null;
  autonomyLevel: number;         // 0–5; drives autonomy marker icon
  latencyP50Ms: number | null;   // median latency; drives bottleneck overlay
  latencyP95Ms: number | null;   // p95 latency; for overlay threshold display
  isBottleneck: boolean;         // pre-computed: latency > overlay threshold
  viewState: StepViewState;      // 'activated' | 'activating' | 'placeholder'
}

type StepStatus = 'active' | 'blocked' | 'complete' | 'pending';
type StepViewState = 'activated' | 'activating' | 'placeholder';
```

#### `WorkflowEdge`

A flow connection between workflow steps. Bottleneck edges are rendered with
animated `stroke-dashoffset` via custom React Flow edge component.

```typescript
interface WorkflowEdge {
  id: string;
  source: string;                // WorkflowNode.id
  target: string;                // WorkflowNode.id
  label: string | null;          // optional edge label
  isBottleneck: boolean;         // drives animated dashed stroke
}
```

#### `WorkflowSummary`

Metadata for a workflow, shown in the topology sidebar and filter bar.

```typescript
interface WorkflowSummary {
  id: string;
  name: string;
  ownerTeam: string | null;
  nodeCount: number;
  status: WorkflowStatus;
  viewState: WorkflowViewState;  // 'activated' | 'activating' | 'placeholder'
}

type WorkflowStatus = 'healthy' | 'degraded' | 'blocked';
type WorkflowViewState = 'activated' | 'activating' | 'placeholder';
```

---

### Decision Graph

#### `DecisionNode`

A captured organizational decision. Rendered as a React Flow custom node.
Rationale and alternatives are revealed in a hover tooltip or side pane.

```typescript
interface DecisionNode {
  id: string;                    // AGE node UUID
  title: string;
  rationale: string;             // shown in tooltip / detail pane
  alternatives: DecisionAlternative[];
  authorId: string | null;       // Clerk user ID
  authorName: string | null;
  capturedAt: string;            // ISO-8601
  impactedSystems: string[];
  status: DecisionStatus;
  viewState: DecisionViewState;  // 'activated' | 'placeholder'
}

interface DecisionAlternative {
  label: string;
  reason: string;                // why this was not chosen
}

type DecisionStatus = 'active' | 'superseded' | 'retracted';
type DecisionViewState = 'activated' | 'activating' | 'placeholder';
```

#### `DecisionEdge`

A typed relationship between two decisions. Edge type determines visual
encoding (solid, dashed, or dotted) in the React Flow custom edge component.

```typescript
interface DecisionEdge {
  id: string;
  source: string;                // DecisionNode.id
  target: string;                // DecisionNode.id
  type: DecisionEdgeType;        // drives visual style
}

type DecisionEdgeType = 'predecessor' | 'alternative' | 'dependent';
```

---

### Design Tokens

#### `DesignToken`

Named values consumed by both Tailwind config and CSS custom properties.
Stored in `src/design-system/tokens.css` and referenced in `tailwind.config.ts`.

```typescript
interface DesignToken {
  name: string;                  // CSS custom property key, e.g. '--color-placeholder-grey'
  value: string;                 // CSS value, e.g. 'oklch(91% 0 0)'
  tailwindAlias: string | null;  // Tailwind class alias, e.g. 'placeholder-grey'
  category: TokenCategory;
}

type TokenCategory = 'color' | 'spacing' | 'motion-duration' | 'motion-easing' | 'shadow' | 'typography';
```

Key token definitions (informative, authoritative in `tokens.css`):

| Token | Value | Purpose |
|---|---|---|
| `--color-placeholder-grey` | `oklch(91% 0 0)` | Empty/activating state neutral (≈ Tailwind neutral-200) |
| `--motion-duration-set-piece` | `500ms` | GSAP time-travel scrub, state transitions |
| `--motion-duration-everyday` | `150ms` | Framer Motion hover, selection, panel |
| `--motion-easing-set-piece` | `cubic-bezier(0.4, 0, 0.2, 1)` | Set-piece easing |
| `--motion-easing-everyday` | `cubic-bezier(0.0, 0, 0.2, 1)` | Everyday easing |

---

### View State

#### `ViewStateContext`

Global state per view, managed in Zustand. Determines which content variant
is rendered and which CTA is surfaced.

```typescript
interface ViewStateContext {
  galaxy: GalaxyViewState;
  topology: TopologyViewState;
  decisionGraph: DecisionGraphViewState;
}

interface GalaxyViewState {
  state: 'empty' | 'activating' | 'activated';
  initiativeCount: number;
  ingestProgress: IngestProgress | null;    // null when state = 'activated'
}

interface TopologyViewState {
  state: 'empty' | 'activating' | 'activated';
  workflowCount: number;
  discoveredCount: number;
}

interface DecisionGraphViewState {
  state: 'empty' | 'activating' | 'activated';
  decisionCount: number;
}

interface IngestProgress {
  discoveredCount: number;
  estimatedTotal: number | null;
  estimatedCompletionAt: string | null;  // ISO-8601
}
```

---

## Zustand Store Shape

Two stores manage frontend state. A third (TanStack Query) manages API cache.

### `graphInteractionStore` (Zustand)

```typescript
interface GraphInteractionStore {
  // Galaxy
  galaxySelection: SelectionSet;
  galaxyOverlay: OverlayConfig;
  galaxyTimeCursor: string | null;        // ISO-8601 snapshot timestamp
  galaxySnapshots: GalaxySnapshot[];      // loaded snapshots for time-travel
  focusedNodeId: string | null;           // node detail pane

  // Topology
  topologyFilters: TopologyFilters;

  // Decision Graph
  decisionFilters: DecisionFilters;
  focusedDecisionId: string | null;

  // Cross-view
  viewStates: ViewStateContext;
}

interface TopologyFilters {
  teamId: string | null;
  initiativeId: string | null;
  status: StepStatus | null;
}

interface DecisionFilters {
  query: string;
  fromDate: string | null;
  toDate: string | null;
  authorId: string | null;
  impactedSystem: string | null;
}
```

---

## API ↔ Frontend Transformation

Raw API responses are transformed into view models at the TanStack Query layer
(`queryFn` in each view's query definitions). No raw API shapes leak into view
renderer code.

```
API Response (snake_case JSON)
  └─ TanStack Query queryFn
      └─ transform() → View Model (camelCase TypeScript)
          └─ passed to Graphology / React Flow
```

Transformation functions live in `src/lib/transforms/`:
- `toInitiativeNode(raw: ApiNode): InitiativeNode`
- `toInitiativeEdge(raw: ApiEdge): InitiativeEdge`
- `toWorkflowNode(raw: ApiWorkflowStep): WorkflowNode`
- `toDecisionNode(raw: ApiDecision): DecisionNode`
