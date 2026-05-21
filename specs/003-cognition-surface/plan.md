# Implementation Plan: Phase 3 — Cognition Surface

**Branch**: `3-cognition-surface` | **Date**: 2026-05-19 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/003-cognition-surface/spec.md`

---

## Summary

Phase 3 is a greenfield frontend: a Vite 6 + React 19 SPA that renders three
interconnected graph views (Initiative Galaxy, Workflow Topology, Decision Graph)
against the existing Phase 1/2 backend API. No backend tables or graph mutations
are introduced. The entire phase is read-only from the backend's perspective.

The Galaxy view is the primary deliverable — a WebGL-rendered force-layout graph
(Sigma.js v3 via @react-sigma/core) capable of ≥30fps at 10k nodes / 30k edges.
Topology and Decision Graph use React Flow v12 for structured layout. All three
share a design system (shadcn/ui with Radix + Tailwind) and a two-tier motion
language (GSAP v3.12 for set-pieces, Framer Motion v11 for everyday interactions).
Zustand v5 manages graph interaction state; TanStack Query v5 manages API data.

---

## Technical Context

| Dimension | Value |
|---|---|
| Language / Version | TypeScript 5.x strict |
| Package manager | npm (workspace: `web/`) |
| Build framework | Vite 6 + `@vitejs/plugin-react` |
| Runtime | React 19 |
| Galaxy renderer | Sigma.js v3 via `@react-sigma/core`; Graphology for graph data model |
| Layout engine | `@react-sigma/layout-forceatlas2` (Web Worker via LayoutSupervisor) |
| Topology + Decision renderer | React Flow v12 (`@xyflow/react`) |
| Decision layout | `@dagrejs/dagre` + `graphology-layout-dagre` |
| Design system | shadcn/ui (Radix UI primitives + Tailwind CSS 4); tokens in `tokens.css` |
| Motion (set-piece) | GSAP v3.12 + `@gsap/react`; `useGSAP()` for cleanup |
| Motion (everyday) | Framer Motion v11 |
| State (interaction) | Zustand v5 |
| State (API data) | TanStack Query v5 (`@tanstack/react-query`) |
| Auth | Clerk React SDK (`@clerk/react`); JWT from Phase 1/2 |
| Unit tests | Vitest + `@testing-library/react` |
| Visual regression | `@playwright/test` with `toHaveScreenshot()`; 27 fixtures |
| Linting + formatting | ESLint + Prettier |
| Target platform | Evergreen browsers (Chrome, Firefox, Safari); WebGL required |
| Performance target | ≥30fps at 10k/30k Galaxy; sub-1s Topology interactions at 500 nodes |
| Viewports | mobile-landscape (1024×768), laptop (1440×900), large display (2560×1440) |

---

## Constitution Check

*GATE: evaluated before Phase 0 research, re-evaluated after Phase 1 design.*

| Principle | Status | Evidence |
|---|---|---|
| I. Intent Over Tasks | ✅ PASS | All three views surface initiative/workflow/decision nodes that trace to Goal/Initiative/Signal ontology primitives from Phase 1. The Galaxy renders the intent graph directly. No orphan task records are introduced. |
| II. Persistent Semantic Memory | ✅ PASS | The frontend is read-only. No state is persisted except Zustand graph interaction state (selection, overlays, time-travel cursor), which is ephemeral and intentionally non-authoritative. All authoritative data lives in the Phase 1/2 backend. |
| III. Human Governance, AI Execution | ✅ N/A | Phase 3 adds no AI agents. The approval inbox UI (§8.3.8) surfaces the Phase 2 approval API; no new AI actions are added. Human approval actions use the existing POST /inbox/{id}/approve|reject endpoints. |
| IV. Visualization as Cognition | ✅ PASS | This phase IS the visualization layer. All three views are topology-first: Initiative Galaxy is a force-layout graph, Workflow Topology is a structured DAG, Decision Graph is a hierarchical DAG. No CRUD tables are introduced as primary surfaces. |
| V. Evaluation-First | ✅ PASS | 27 visual regression fixtures committed to CI before beta. Performance benchmark suite committed for Galaxy (FR-009). Both gates must pass before Phase 4 promotion. |
| VI. Observable Autonomy | ✅ N/A | No new AI agents in Phase 3. Existing OTEL traces from Phase 2 agents surface in the view as autonomy level markers on nodes (rendered, not generated). |
| VII. Domain-Adapter Extensibility | ✅ PASS | Frontend consumes normalized Phase 1 API responses. No raw vendor schemas (Jira, Slack, GitHub) are rendered directly. Transform functions in `src/lib/transforms/` enforce the boundary. |
| Durable workflow | ✅ N/A | No new durable workflows. |
| Telemetry stack | ✅ PASS | Frontend emits OpenTelemetry Web SDK spans for user interactions (lasso selection, overlay change, time-travel scrub) via `src/lib/telemetry/`. No Langfuse integration at frontend level. |
| Integration normalization | ✅ PASS | API responses are transformed to view models at the TanStack Query layer; no raw API shapes reach renderer code (enforced by TypeScript strict mode). |

**Post-Phase 1 design re-check**: All gates remain PASS. The data-model.md confirms
the clean API→ViewModelransformation boundary. contracts/api.yaml confirms read-only
consumption of Phase 1/2 endpoints. No new backend mutations are required.

---

## Project Structure

### Documentation (this feature)

```text
specs/003-cognition-surface/
├── plan.md              ← this file
├── spec.md              ← feature spec
├── research.md          ← Phase 0 decisions (9 research decisions)
├── data-model.md        ← frontend view models (TypeScript types)
├── quickstart.md        ← test scenarios + seed data guide
├── contracts/
│   └── api.yaml         ← API endpoints consumed by the frontend
├── checklists/
│   └── requirements.md  ← spec quality checklist (all passed)
└── tasks.md             ← generated by /speckit.tasks (not yet)
```

### Source Code (repository root)

Phase 3 adds a `web/` workspace alongside the existing Python backend.
The backend (`src/`) is not modified.

```text
web/                              ← NEW: Vite 6 SPA workspace
├── index.html
├── vite.config.ts
├── tsconfig.json                 ← strict mode
├── tsconfig.node.json
├── tailwind.config.ts
├── postcss.config.ts
├── package.json
├── .eslintrc.json
├── .prettierrc
│
├── src/
│   ├── main.tsx                  ← Vite entry; ClerkProvider, QueryClientProvider
│   ├── App.tsx                   ← router; protected routes
│   ├── router.tsx                ← React Router 6: /galaxy, /topology, /decisions, /inbox
│   │
│   ├── design-system/            ← shadcn/ui: tokens + copied Radix components
│   │   ├── tokens.css            ← CSS custom properties (single source of truth)
│   │   ├── globals.css           ← Tailwind base + token imports
│   │   ├── components/           ← copied shadcn components
│   │   │   ├── Button.tsx
│   │   │   ├── Tooltip.tsx
│   │   │   └── ...
│   │   └── primitives/           ← shared view primitives (used across all 3 views)
│   │       ├── OverlayPanel.tsx
│   │       ├── FilterBar.tsx
│   │       ├── NodeTooltip.tsx
│   │       └── StateCTA.tsx
│   │
│   ├── views/
│   │   ├── galaxy/               ← Initiative Galaxy (US1)
│   │   │   ├── GalaxyView.tsx    ← SigmaContainer wrapper; loads graph from query
│   │   │   ├── GalaxyEmpty.tsx   ← empty state (0 nodes)
│   │   │   ├── GalaxyActivating.tsx  ← activating state (1-9 nodes)
│   │   │   ├── ForceLayout.tsx   ← LayoutSupervisor lifecycle hook
│   │   │   ├── LassoSelect.tsx   ← screen-space lasso via sigma.getNodeDisplayData
│   │   │   ├── OverlayControls.tsx   ← overlay picker; nodeReducer/edgeReducer
│   │   │   ├── TimeTravelBar.tsx ← GSAP timeline scrubber
│   │   │   ├── NodeDetailPane.tsx   ← initiative detail on click
│   │   │   └── hooks/
│   │   │       ├── useGalaxyGraph.ts   ← TanStack Query: load nodes+edges into Graphology
│   │   │       ├── useTimeTravelScrub.ts  ← GSAP timeline + snapshot import
│   │   │       └── useLasso.ts         ← lasso geometry + point-in-polygon
│   │   │
│   │   ├── topology/             ← Workflow Topology (US2)
│   │   │   ├── TopologyView.tsx  ← ReactFlow wrapper
│   │   │   ├── TopologyEmpty.tsx
│   │   │   ├── TopologyActivating.tsx
│   │   │   ├── WorkflowNode.tsx  ← custom React Flow node (status/owner/autonomy)
│   │   │   ├── BottleneckEdge.tsx   ← animated stroke-dashoffset custom edge
│   │   │   ├── TopologyFilters.tsx  ← team/initiative/status filter bar
│   │   │   └── hooks/
│   │   │       ├── useTopologyData.ts  ← TanStack Query: load workflows
│   │   │       └── useTopologyFilters.ts  ← Zustand filter state
│   │   │
│   │   └── decisions/            ← Decision Graph (US3)
│   │       ├── DecisionView.tsx  ← ReactFlow wrapper + dagre layout
│   │       ├── DecisionEmpty.tsx
│   │       ├── DecisionActivating.tsx
│   │       ├── DecisionNode.tsx  ← custom React Flow node (title/author/status)
│   │       ├── DecisionEdge.tsx  ← typed edge styles (solid/dashed/dotted)
│   │       ├── DecisionSearch.tsx   ← search bar with debounce
│   │       ├── DecisionFilters.tsx  ← date range, author, system filters
│   │       └── hooks/
│   │           ├── useDecisionGraph.ts  ← TanStack Query: load decisions
│   │           └── useDecisionLayout.ts ← graphology-layout-dagre application
│   │
│   ├── inbox/                    ← Approval inbox UI (Phase 2 surface)
│   │   ├── InboxView.tsx
│   │   ├── InboxItem.tsx
│   │   └── hooks/
│   │       └── useInbox.ts
│   │
│   ├── lib/
│   │   ├── api/                  ← axios instance + TanStack Query keys
│   │   │   ├── client.ts         ← axios with Clerk JWT header injection
│   │   │   └── queryKeys.ts
│   │   ├── transforms/           ← API response → view model transforms
│   │   │   ├── initiative.ts     ← toInitiativeNode, toInitiativeEdge
│   │   │   ├── workflow.ts       ← toWorkflowNode, toWorkflowEdge
│   │   │   └── decision.ts       ← toDecisionNode, toDecisionEdge
│   │   ├── stores/               ← Zustand stores
│   │   │   └── graphInteraction.ts
│   │   └── telemetry/            ← OpenTelemetry Web SDK
│   │       └── tracer.ts
│   │
│   └── types/                    ← view model types (from data-model.md)
│       ├── galaxy.ts
│       ├── topology.ts
│       ├── decisions.ts
│       └── tokens.ts
│
├── tests/
│   ├── unit/                     ← Vitest unit tests
│   │   ├── transforms/
│   │   ├── stores/
│   │   └── design-system/
│   └── visual/                   ← Playwright visual regression
│       ├── galaxy.spec.ts
│       ├── topology.spec.ts
│       ├── decisions.spec.ts
│       └── snapshots/            ← committed PNG fixtures (27 total)
│
├── benchmarks/                   ← performance benchmark outputs (committed)
│   └── .gitkeep
│
└── scripts/                      ← seed + benchmark scripts
    ├── seed-graph.ts
    ├── seed-workflows.ts
    ├── seed-decisions.ts
    ├── seed-snapshots.ts
    └── trigger-ingest-batch.ts
```

**Structure decision**: Single `web/` workspace alongside the Python `src/` root.
Not a monorepo (`packages/`) because there is only one frontend app. The backend
remains entirely in `src/context_os/` — no cross-directory imports.

---

## Implementation Strategy

### Phase Sequence

1. **Foundations** (prerequisite for all views):
   - Vite project scaffold + TypeScript strict config
   - Design system: `tokens.css`, Tailwind config, shared primitives (OverlayPanel, FilterBar, NodeTooltip, StateCTA)
   - API client (axios + Clerk JWT injection) + TanStack Query setup
   - Zustand store shell + view model types

2. **Initiative Galaxy (US1, P1)** — the blocking deliverable:
   - Empty and activating states first (static, no data dependency)
   - Graph data loading via TanStack Query + Graphology population
   - Sigma rendering + ForceAtlas2 worker lifecycle
   - Overlay reducers (load, risk, autonomy, ownership)
   - Lasso selection (screen-space point-in-polygon)
   - Node detail pane
   - Time-travel scrubber (GSAP timeline + snapshot import)
   - Performance benchmark suite
   - Visual regression snapshots (9 Galaxy fixtures)

3. **Workflow Topology (US2, P2)** — can begin in parallel with Galaxy overlay work:
   - Empty and activating states
   - React Flow wrapper + Dagre layout for workflow steps
   - Custom WorkflowNode (status/owner/autonomy markers)
   - Bottleneck overlay + animated edge
   - Team/status filter (client-side Zustand)
   - Visual regression snapshots (9 Topology fixtures)

4. **Decision Graph (US3, P3)**:
   - Empty and activating states
   - React Flow wrapper + Dagre hierarchical layout
   - Custom DecisionNode + DecisionEdge (typed styles)
   - Search + date/author/system filters
   - Hover rationale tooltip / side pane
   - Visual regression snapshots (9 Decision fixtures)

5. **Polish + cross-cutting** (final):
   - Cross-surface coherence review
   - Mobile-landscape responsive pass for all three views
   - OpenTelemetry Web SDK instrumentation
   - Inbox UI skin over Phase 2 API
   - Internal design review preparation (seed data, demo script)

### Critical Path

```
Foundations (1w)
  └─ Galaxy empty/activating state (2d)
      └─ Galaxy core rendering + ForceAtlas2 (1w)
          ├─ Galaxy overlays + lasso (3d)  ──── parallel with:
          └─ Topology start (US2)         ──── Topology (2w) ─── Decisions start (US3)
              └─ Time-travel scrub (2d)
                  └─ Performance benchmarks
                      └─ Visual regression (all 27 fixtures)
                          └─ Design review gate
```

### Design Review Gate

Three internal Galaxy design reviews (FR-010, SC-003) are required before
closed beta. The first review should be scheduled after Galaxy core rendering
is complete (milestone: activated state with ForceAtlas2 running). Review notes
are archived in `docs/design-reviews/`.

### Performance Benchmark Gate

Galaxy benchmark (`npm run benchmark:galaxy`) must confirm:
- Layout convergence ≤ 5 seconds on 10k/30k seed
- Frame paint p95 ≤ 33ms (≥30fps) on CI GPU runner

Topology benchmark must confirm:
- Pan/zoom/filter p95 ≤ 1000ms on 500-node seed

Both gates are enforced in CI before Phase 4 promotion.

---

## Key Implementation Decisions

*All decisions documented with rationale in `research.md`.*

| Decision | Choice | Rationale summary |
|---|---|---|
| Build framework | Vite 6 SPA | SSR incompatibility: Sigma.js, React Flow, forceatlas2-worker all access `window`/WebGL. Next.js RSC + Web Worker is unnecessarily complex. Vite CI build: 0.5–2s vs 15–30s for Next.js. |
| Galaxy renderer | Sigma.js v3 via @react-sigma/core | WebGL (≥30fps at 10k nodes), forceatlas2-worker runs in Web Worker without blocking main thread, overlay composition via node/edge reducers. |
| Topology + Decision renderer | React Flow v12 | Best DX for structured/declarative graphs; custom React node components are native React — status/owner/autonomy trivially rendered. |
| Decision layout engine | dagre via graphology-layout-dagre | Hierarchical layout for predecessor/alternative/dependent relationships; dagre sufficient for ≤1000 decisions at MVP scale. |
| Design system | shadcn/ui (copied) | Single-source-of-truth CSS custom properties consumed by both Tailwind and Radix overrides. Copying (not installing) gives full token control. |
| Motion | GSAP (set-piece) + Framer Motion (everyday) | No conflicts; different abstraction layers. Critical rule: never animate the same DOM node with both simultaneously. GSAP free for commercial SaaS since April 2025. |
| State | Zustand v5 + TanStack Query v5 | Zustand: flat atom model for large selection sets (10k nodes). TanStack Query: API cache, background refetch, loading/error states. |
| Visual regression | Playwright + tolerance | `toHaveScreenshot()` captures WebGL Canvas correctly in headless Chrome. `maxDiffPixelRatio: 0.02` accounts for GPU anti-aliasing variance. |
| Unit tests | Vitest | Vite-native; 5–10× faster than Jest in CI; shares Vite transform pipeline. |

---

## Environment Variables (web/)

```bash
VITE_API_BASE_URL=http://localhost:8000   # Backend base URL
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...    # Clerk publishable key
VITE_OTEL_ENDPOINT=http://localhost:4318  # OTLP HTTP endpoint (optional)
```

---

## Dev Commands (web/)

```bash
npm install              # install dependencies
npm run dev              # Vite dev server on :5173
npm run build            # production build to dist/
npm run typecheck        # tsc --noEmit
npm run lint             # ESLint
npm run test             # Vitest unit tests
npm run test:visual      # Playwright visual regression
npm run benchmark:galaxy # Galaxy performance benchmark (requires seed)
npm run benchmark:topology  # Topology performance benchmark
npm run benchmark:decisions # Decision search benchmark
```
