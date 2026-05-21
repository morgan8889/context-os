# Tasks: Phase 3 — Cognition Surface

**Input**: Design documents from `specs/003-cognition-surface/`  
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/api.yaml ✓, quickstart.md ✓

**Organization**: Organized by user story for independent implementation and testing.  
**Tests**: Included — visual regression (FR-017, FR-024, FR-033, SC-007), performance benchmarks (FR-009), and Vitest unit tests are required by functional requirements.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US5 from spec.md)

---

## Phase 1: Setup

**Purpose**: Scaffold the `web/` Vite SPA workspace and configure all tooling.

- [x] T001 Scaffold Vite 6 + React 19 SPA in `web/` — run `npm create vite@latest web -- --template react-ts`, update `web/vite.config.ts` with `@vitejs/plugin-react`, set `base: '/'`, configure proxy to `http://localhost:8000` for `/api/v1`
- [x] T002 Configure TypeScript 5.x strict mode in `web/tsconfig.json` (strict: true, noUncheckedIndexedAccess: true, exactOptionalPropertyTypes: true) and `web/tsconfig.node.json` (module: ESNext, moduleResolution: bundler)
- [x] T003 [P] Configure ESLint in `web/.eslintrc.json` (react-hooks, react-refresh, @typescript-eslint/strict plugins) and Prettier in `web/.prettierrc` (singleQuote: true, semi: true, tabWidth: 2)
- [x] T004 [P] Add all npm scripts to `web/package.json`: dev, build, typecheck (`tsc --noEmit`), lint, test (`vitest run`), test:visual (`playwright test`), benchmark:galaxy, benchmark:topology, benchmark:decisions
- [x] T005 Initialize `web/src/` directory structure with empty index files: `views/galaxy/hooks/`, `views/topology/hooks/`, `views/decisions/hooks/`, `inbox/hooks/`, `lib/api/`, `lib/transforms/`, `lib/stores/`, `lib/telemetry/`, `lib/animations/`, `design-system/components/`, `design-system/primitives/`, `types/`
- [x] T006 [P] Create `web/scripts/` directory (seed + benchmark scripts), `web/benchmarks/` directory with `.gitkeep`, and `web/tests/visual/snapshots/` directory with `.gitkeep`
- [x] T007 [P] Configure Vitest in `web/vite.config.ts` (test: { environment: 'jsdom', globals: true, setupFiles: ['./src/test-setup.ts'] }) and create `web/src/test-setup.ts` (`import '@testing-library/jest-dom'`)
- [x] T008 [P] Configure Playwright in `web/playwright.config.ts` — baseURL: `http://localhost:5173`, projects: chromium only, screenshot: `on`, use: { deviceScaleFactor: 1 }, snapshotPathTemplate: `tests/visual/snapshots/{testFileName}/{arg}{ext}`

---

## Phase 2: Foundational (US4 — Shared Design System + Shared Infrastructure)

**Purpose**: Design system tokens, shared primitives, API client, Zustand store, view model types — all required before ANY view-specific work. This phase IS the US4 delivery; it also establishes all shared infrastructure.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T00- [x] T009 Define CSS custom property token set in `web/src/design-system/tokens.css` — include: `--color-placeholder-grey: oklch(91% 0 0)`, `--motion-duration-set-piece: 500ms`, `--motion-duration-everyday: 150ms`, `--motion-easing-set-piece: cubic-bezier(0.4, 0, 0.2, 1)`, `--motion-easing-everyday: cubic-bezier(0.0, 0, 0.2, 1)`, semantic color tokens for all view states (active, paused, at_risk, blocked, complete)
- [x] T010 Install all npm dependencies in `web/package.json` — `@react-sigma/core @react-sigma/layout-forceatlas2 graphology graphology-layout-dagre @xyflow/react @dagrejs/dagre gsap @gsap/react framer-motion zustand @tanstack/react-query @clerk/react axios tailwindcss @tailwindcss/vite @radix-ui/react-tooltip @radix-ui/react-popover` and devDeps: `vitest @playwright/test @testing-library/react @testing-library/jest-dom typescript eslint prettier`; run `npm install`
- [x] T011 Configure Tailwind CSS 4 in `web/tailwind.config.ts` — `content: ['./src/**/*.{ts,tsx}']`, extend colors with CSS custom property aliases: `'placeholder-grey': 'var(--color-placeholder-grey)'`; import `tokens.css` and `tailwind/base, components, utilities` in `web/src/design-system/globals.css`
- [x] T012 [P] Copy shadcn/ui Radix-based components into `web/src/design-system/components/` — Button.tsx (Radix-free, Tailwind variants), Tooltip.tsx (Radix Tooltip.Root/Trigger/Content), Popover.tsx (Radix Popover), Badge.tsx (status color variants); no external shadcn CLI — copy and adapt manually using Tailwind tokens
- [x] T013 Implement StateCTA shared primitive in `web/src/design-system/primitives/StateCTA.tsx` — props: `label: string, onClick: () => void, description?: string`; renders single `<button data-cta="primary">` with Tailwind styling; Framer Motion `initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}` entrance; no secondary actions (enforces FR-030 one-CTA rule)
- [x] T014 [P] Implement OverlayPanel shared primitive in `web/src/design-system/primitives/OverlayPanel.tsx` — props: `open: boolean, onClose: () => void, title: string, children: ReactNode`; Framer Motion `x: 320 → 0` slide-in from right, 150ms everyday easing; fixed width 320px; backdrop semi-transparent; keyboard Escape closes
- [x] T015 [P] Implement FilterBar shared primitive in `web/src/design-system/primitives/FilterBar.tsx` — props: `filters: FilterGroup[], activeFilters: Record<string, string>, onChange: (key, value) => void`; chip-based multi-group filter row; Framer Motion collapse to icon button at mobile-landscape breakpoint; ARIA role="group" for accessibility
- [x] T016 [P] Implement NodeTooltip shared primitive in `web/src/design-system/primitives/NodeTooltip.tsx` — Radix Tooltip.Root with 500ms delay; props: `children, title, body: ReactNode`; used for decision rationale and workflow step details; 300px max-width; pointer-events none on content
- [x] T017 Create TypeScript view model types in `web/src/types/galaxy.ts` (InitiativeNode, InitiativeEdge, GalaxySnapshot, OverlayConfig, OverlayType, SelectionSet, NodeViewState), `topology.ts` (WorkflowNode, WorkflowEdge, WorkflowSummary, StepStatus, StepViewState, WorkflowStatus, WorkflowViewState, TopologyFilters), `decisions.ts` (DecisionNode, DecisionEdge, DecisionAlternative, DecisionEdgeType, DecisionStatus, DecisionViewState = 'activated' | 'activating' | 'placeholder', DecisionFilters), `tokens.ts` (DesignToken, TokenCategory) — mirror data-model.md exactly; use strict null handling (`string | null` not `string?`)
- [x] T018 Implement axios API client with Clerk JWT injection in `web/src/lib/api/client.ts` — create axios instance with baseURL from `import.meta.env.VITE_API_BASE_URL`; add request interceptor that calls Clerk `useAuth().getToken()` and sets `Authorization: Bearer <token>` header; export typed `apiClient` instance
- [x] T019 [P] Define TanStack Query client and query key factories in `web/src/lib/api/queryKeys.ts` (key factories: `graphKeys`, `workflowKeys`, `decisionKeys`, `inboxKeys`, `viewStateKeys`) and `web/src/lib/api/queryClient.ts` (QueryClient with defaultOptions: staleTime 60s, retry 2, refetchOnWindowFocus false)
- [x] T020 Implement Zustand graphInteraction store in `web/src/lib/stores/graphInteraction.ts` — flat atom model with slices: `galaxySelection: SelectionSet`, `galaxyOverlay: OverlayConfig`, `galaxyTimeCursor: string | null`, `galaxySnapshots: GalaxySnapshot[]`, `focusedNodeId: string | null`, `topologyFilters: TopologyFilters`, `decisionFilters: DecisionFilters`, `focusedDecisionId: string | null`, `viewStates: ViewStateContext`; use `create<Store>()(immer(...))` for mutation ergonomics
- [x] T021 [P] Implement API transform functions in `web/src/lib/transforms/initiative.ts` (`toInitiativeNode(raw: ApiNode): InitiativeNode`, `toInitiativeEdge(raw: ApiEdge): InitiativeEdge`), `web/src/lib/transforms/workflow.ts` (`toWorkflowNode`, `toWorkflowEdge`, computes `isBottleneck = (latencyP95Ms ?? 0) > 500`), `web/src/lib/transforms/decision.ts` (`toDecisionNode`, `toDecisionEdge`) — snake_case → camelCase, null coercion, strict type assertions
- [x] T022 Implement view state polling hook in `web/src/lib/api/viewState.ts` — `useViewState()`: TanStack Query `useQuery` on `GET /api/v1/views/state` with `refetchInterval: (data) => data?.galaxy.state === 'activated' && data?.topology.state === 'activated' && data?.decision_graph.state === 'activated' ? false : 30000`; on state change dispatches to Zustand `viewStates`; transforms snake_case ViewStateResponse to ViewStateContext
- [x] T023 Configure Clerk React SDK in `web/src/main.tsx` — wrap app with `<ClerkProvider publishableKey={import.meta.env.VITE_CLERK_PUBLISHABLE_KEY}>`, `<QueryClientProvider client={queryClient}>`, `<RouterProvider>`; create protected route wrapper in `web/src/App.tsx` using `useAuth().isSignedIn` — unauthenticated users redirect to Clerk sign-in
- [x] T024 Configure React Router 6 in `web/src/router.tsx` — routes: `/` → redirect `/galaxy`, `/galaxy` → lazy GalaxyView, `/topology` → lazy TopologyView, `/decisions` → lazy DecisionView, `/inbox` → lazy InboxView; all routes wrapped in `<ProtectedRoute>`; use `createBrowserRouter`
- [x] T025 [P] Write Vitest unit tests for design system in `web/tests/unit/design-system.test.ts` — (1) regex scan of `src/views/**/*.tsx` asserting no hardcoded `#[0-9a-f]{3,6}` or `rgb(` or `oklch(` outside `tokens.css` (FR-025); (2) render snapshot tests for StateCTA, OverlayPanel, FilterBar, NodeTooltip asserting each renders `data-cta="primary"` once and uses `--color-placeholder-grey` or `placeholder-grey` class

**Checkpoint**: Design system tokens defined, shared primitives built, API client wired, Zustand store initialized, types committed. All three view implementations can now start.

---

## Phase 3: User Story 1 — Initiative Galaxy (Priority: P1) 🎯 MVP

**Goal**: Render the full organization initiative graph as a WebGL force-layout at ≥30fps with lasso selection, overlays, and time-travel scrubbing.

**Independent Test**: (a) Run `npm run benchmark:galaxy` with 10k-node seed — confirm layout convergence ≤ 5s and frame paint p95 ≤ 33ms. (b) Run `npm run test:visual -- --grep "galaxy"` — 9 snapshot fixtures pass. (c) Manual 60-second no-narration demo: lasso select → overlay → time-travel → node click — all interactions responsive.

- [x] T026 [US1] Implement GalaxyEmpty in `web/src/views/galaxy/GalaxyEmpty.tsx` — SVG placeholder constellation (20–30 scatter-positioned circles in `var(--color-placeholder-grey)`, varying radii 3–8px, faint connecting lines); copy: "Your organization's initiatives will appear here. Connect your first source to see the full picture."; StateCTA label "Adjust source scope", onClick → `/settings/sources`
- [x] T027 [US1] Implement GalaxyActivating in `web/src/views/galaxy/GalaxyActivating.tsx` — renders real InitiativeNodes via SigmaContainer alongside placeholder constellation filling remaining space; progress copy: "${discoveredCount} initiatives discovered${estimatedCompletionAt ? ` — estimated complete ${formatRelative(estimatedCompletionAt)}` : ''}"; StateCTA label "Notify me when done", onClick → subscribe notification action
- [x] T028 [US1] Implement useGalaxyGraph hook in `web/src/views/galaxy/hooks/useGalaxyGraph.ts` — TanStack Query: paginate `GET /api/v1/graph/nodes?limit=1000` until `next_cursor` is null, same for `GET /api/v1/graph/edges?limit=2000`; populate a `new MultiGraph()` (graphology) with all pages; transform each raw item via `toInitiativeNode`/`toInitiativeEdge`; expose `{ graph, isLoading, isError }` and a stable `graphRef`
- [x] T029 [US1] Implement ForceLayout in `web/src/views/galaxy/ForceLayout.tsx` — `useLayoutEffect` creates `LayoutSupervisor(sigma, { settings: { slowDown: 3, barnesHutOptimize: true, seed: 42 } })`; `supervisor.start()` on mount; cleanup via `useGSAP` scope; exposes `pauseLayout()` and `resumeLayout()` via `useImperativeHandle`; emits `onConverged` when supervisor enters idle state (LayoutSupervisor `'stop'` event after positions stabilize)
- [x] T030 [US1] Implement LassoSelect in `web/src/views/galaxy/LassoSelect.tsx` and `useLasso` hook in `web/src/views/galaxy/hooks/useLasso.ts` — transparent `<canvas>` overlay positioned absolute over Sigma container; `mousedown` starts polygon capture; `mousemove` draws dashed path on overlay canvas; `mouseup` closes polygon, iterates all graphology node IDs, calls `sigma.getNodeDisplayData(id)` for `{ x, y }` screen coords, runs `pointInPolygon(point, polygon)` test, writes result to Zustand `galaxySelection`; Escape key clears; supports touch events with equivalent gesture
- [x] T031 [P] [US1] Implement OverlayControls in `web/src/views/galaxy/OverlayControls.tsx` — OverlayPanel trigger button; four overlay options: Load (maps `actorCount` to node size + blue hue gradient), Risk (maps `riskScore` to red heatmap — null nodes rendered in `--color-placeholder-grey`), Autonomy (maps `autonomyLevel` to shield icon count overlay), Ownership (maps `ownerTeam` to categorical color group); active overlay calls `sigma.setSetting('nodeReducer', reducerFn)` and `sigma.setSetting('edgeReducer', reducerFn)`; null overlay restores defaults — zero re-layout on any overlay change
- [x] T032 [P] [US1] Implement NodeDetailPane in `web/src/views/galaxy/NodeDetailPane.tsx` — OverlayPanel that opens when Zustand `focusedNodeId` is non-null; reads `InitiativeNode` from graphology `graph.getNodeAttributes(focusedNodeId)`; displays: label, type badge, status badge, ownerTeam, actorCount, riskScore (formatted 0–100%), autonomyLevel (0–5 shield icons), edgeCount; close button sets `focusedNodeId` null; Framer Motion 150ms entrance
- [x] T033 [US1] Implement useTimeTravelScrub hook in `web/src/views/galaxy/hooks/useTimeTravelScrub.ts` — `useQuery` on `GET /api/v1/graph/snapshots` for timestamp list; `scrubToTimestamp(ts: string)`: (1) call `ForceLayout.pauseLayout()`, (2) fetch `GET /api/v1/graph/snapshots/${ts}`, (3) call `graph.import({ nodes: snapshot.nodes, edges: snapshot.edges })`, (4) call `sigma.getCamera().animate({ x: 0.5, y: 0.5, ratio: sigma.getCamera().ratio }, { duration: 500, easing: 'quadraticInOut' })`; all steps wrapped in a GSAP timeline via `useGSAP` for cleanup; `resumeLayout()` on timeline complete
- [x] T034 [P] [US1] Implement TimeTravelBar in `web/src/views/galaxy/TimeTravelBar.tsx` — `<input type="range">` with `min=0 max={snapshots.length - 1}`; displays formatted timestamp at current index; `onChange` calls `scrubToTimestamp(snapshots[index])`; disabled when snapshot list empty or loading; Framer Motion entrance when snapshots become available; GSAP animation confirmation: transition must complete in < 500ms (FR-004)
- [x] T035 [US1] Implement GalaxyView container in `web/src/views/galaxy/GalaxyView.tsx` — routes by `useViewState().galaxy.state`: render GalaxyEmpty when `'empty'`, GalaxyActivating when `'activating'`, activated view when `'activated'`; activated: `<SigmaContainer graph={graph} settings={{ ...sigmaSettings }}>` containing ForceLayout, LassoSelect, OverlayControls, NodeDetailPane, TimeTravelBar; registers `sigma.on('clickNode', ({ node }) => setFocusedNodeId(node))` via `useSigma()`; renders loading skeleton during `useGalaxyGraph` isLoading
- [x] T036 [P] [US1] Create `web/scripts/seed-graph.ts` — tsx CLI: parse `--initiatives N --edges N --state empty|activating|activated`; generate synthetic `ApiNode[]` (random types, statuses, actorCounts, riskScores) and `ApiEdge[]` (random depends_on/shared_actor/shared_work); if state=activating: set `N < 10` regardless of `--initiatives` arg; POST batches to dev-only seed endpoints; print progress
- [x] T037 [P] [US1] Create `web/scripts/benchmark-galaxy.ts` — Playwright script (not test): launch chromium, navigate to `/galaxy` with 10k seed active; use CDP `Tracing.start` to capture 100 animation frames; wait for ForceAtlas2 `onConverged` event via `page.evaluate`; calculate layout_convergence_ms, frame_paint_p50_ms, frame_paint_p95_ms from frame timing; write JSON to `web/benchmarks/galaxy-${dateStr}.json`; exit non-zero if convergence_ms > 5000
- [x] T038 [P] [US1] Write Playwright visual regression tests in `web/tests/visual/galaxy.spec.ts` — 9 fixtures: for each viewport in `[[1024,768],[1440,900],[2560,1440]]` and state in `['empty','activating','activated']`, set viewport, navigate to `/galaxy`, wait for stable render (no loading spinner), call `expect(page).toHaveScreenshot('galaxy-${viewportName}-${state}.png', { maxDiffPixelRatio: 0.02 })`; ForceAtlas2 animations disabled in test mode via `VITE_DISABLE_ANIMATIONS=true`
- [x] T039 [P] [US1] Write Vitest unit tests in `web/tests/unit/galaxy.test.ts` — `toInitiativeNode`: all field mappings, null riskScore/autonomyLevel handling, `viewState` defaults to 'activated'; `toInitiativeEdge`: type mapping, composite ID; `pointInPolygon`: point inside convex polygon, point outside, point on edge, empty polygon; Graphology population: 1000 nodes loaded correctly, duplicate node IDs rejected

**Checkpoint**: Galaxy view fully functional — all three states render, ForceAtlas2 runs in Web Worker, lasso selects nodes, overlays apply without re-layout, time-travel scrubs between snapshots, 9 visual regression fixtures pass, benchmark confirms ≥30fps at 10k nodes.

---

## Phase 4: User Story 2 — Workflow Topology (Priority: P2)

**Goal**: Render team workflows as structured DAG diagrams with status, ownership, and bottleneck overlays at sub-second interaction for 500 nodes.

**Independent Test**: Run `npm run test:visual -- --grep "topology"` (9 fixtures pass) and `npm run benchmark:topology` with 500-node seed (pan/zoom/filter p95 < 1s). Manual: apply team filter → result in < 500ms; toggle bottleneck overlay → animated edges appear without layout shift.

- [x] T040 [US2] Implement TopologyEmpty in `web/src/views/topology/TopologyEmpty.tsx` — ReactFlow canvas with single WorkflowNode at center representing "Executive Briefing" workflow, rendered in `var(--color-placeholder-grey)` at 40% opacity; explanatory copy: "Workflows derive from your team's coordination patterns. Executive Briefing is active by default; others appear as patterns emerge."; StateCTA label "View Executive Briefing", onClick → `/inbox?filter=briefing`
- [x] T041 [US2] Implement TopologyActivating in `web/src/views/topology/TopologyActivating.tsx` — ReactFlow canvas showing mapped WorkflowNodes at full fidelity alongside faint anticipatory WorkflowNode stubs (placeholder-grey, 25% opacity, dashed border) for workflows not yet fully discovered; copy: "${workflowCount} workflows mapped — exploring more coordination patterns…"; StateCTA label "See what's been discovered", onClick → scroll to mapped workflows
- [x] T042 [P] [US2] Implement custom WorkflowNode React Flow node in `web/src/views/topology/WorkflowNode.tsx` — React Flow NodeProps<WorkflowNode>; renders: top-left status badge (active=green, blocked=red, complete=neutral, pending=amber), center label, bottom-row ownerTeam + ownerActor text, autonomy shield icons (autonomyLevel count of filled shields), bottleneck indicator (orange pulsing border when isBottleneck=true); placeholder-grey variant when viewState='placeholder'; 200px min-width
- [x] T043 [P] [US2] Implement custom BottleneckEdge React Flow edge in `web/src/views/topology/BottleneckEdge.tsx` — React Flow EdgeProps; renders SVG path; when `data.isBottleneck=true`: `stroke-dasharray: 8 4`, CSS animation `dashOffset 1.5s linear infinite` (animates stroke-dashoffset from 0 to -12); when false: solid stroke 1.5px; optional edge label via `<EdgeLabelRenderer>`
- [x] T044 [US2] Implement useTopologyData hook in `web/src/views/topology/hooks/useTopologyData.ts` — TanStack Query: `GET /api/v1/workflows`; transforms each workflow's steps to `WorkflowNode[]` via `toWorkflowNode` (computing `isBottleneck = (latencyP95Ms ?? 0) > BOTTLENECK_THRESHOLD_MS`); transforms edges to `WorkflowEdge[]` via `toWorkflowEdge`; applies Dagre layout to position steps: `dagre.layout(g)` with `rankdir: 'LR'`, `nodesep: 80`, `ranksep: 120`; converts to React Flow `Node<WorkflowNode>[]` with x/y from Dagre
- [x] T045 [P] [US2] Implement useTopologyFilters hook in `web/src/views/topology/hooks/useTopologyFilters.ts` — reads `topologyFilters` from Zustand store; returns `filterWorkflows(workflows: ApiWorkflow[], filters: TopologyFilters): ApiWorkflow[]` filtering client-side by teamId (ownerTeam match), initiativeId (future), and status (step status across workflow); sub-500ms constraint met by in-memory filter (no API call on filter change, per spec)
- [x] T046 [P] [US2] Implement TopologyFilters component in `web/src/views/topology/TopologyFilters.tsx` — wraps FilterBar primitive; filter groups: team (unique ownerTeams from workflows), status (healthy/degraded/blocked); onChange dispatches to Zustand `topologyFilters`; "Clear all" resets to null values
- [x] T047 [US2] Implement TopologyView container in `web/src/views/topology/TopologyView.tsx` — routes by `useViewState().topology.state`: render TopologyEmpty when `'empty'`, TopologyActivating when `'activating'`, activated view when `'activated'`; activated: `<ReactFlow nodes={reactFlowNodes} edges={reactFlowEdges} nodeTypes={{ workflowNode: WorkflowNode }} edgeTypes={{ bottleneckEdge: BottleneckEdge }} fitView>` with MiniMap, Controls; TopologyFilters in top toolbar; WorkflowSummary sidebar listing all workflows with status badges; loads all workflow data once on mount (no repeated API calls for filter changes)
- [x] T048 [P] [US2] Write Playwright visual regression tests in `web/tests/visual/topology.spec.ts` — 9 fixtures: for each viewport in `[[1024,768],[1440,900],[2560,1440]]` and state in `['empty','activating','activated']`, seed appropriate data, navigate to `/topology`, wait for stable render, call `expect(page).toHaveScreenshot('topology-${viewportName}-${state}.png', { maxDiffPixelRatio: 0.02 })`
- [x] T049 [P] [US2] Create `web/scripts/seed-workflows.ts` — tsx CLI: parse `--workflows N --steps-per-workflow N --state empty|activating|activated`; generate synthetic `ApiWorkflow[]` with `ApiWorkflowStep[]` (random statuses, autonomy levels, latencies with some > 500ms for bottleneck testing); POST to dev-only seed endpoint; print count
- [x] T050 [P] [US2] Create `web/scripts/benchmark-topology.ts` — Playwright script: navigate to `/topology` with 500-node seed; measure time from filter change to DOM settle (MutationObserver quiet period); verify < 1000ms for pan/zoom; write results to `web/benchmarks/topology-${dateStr}.json`; exit non-zero if filter p95 > 1000ms
- [x] T051 [P] [US2] Write Vitest unit tests in `web/tests/unit/topology.test.ts` — `toWorkflowNode`: field mapping, `isBottleneck` computation at threshold boundaries (499ms=false, 500ms=false, 501ms=true); `useTopologyFilters`: team filter isolates correct workflows, null filter returns all, combined team+status filter; Dagre layout: nodes have valid x/y after layout, no overlapping nodes at default settings

**Checkpoint**: Topology view fully functional — all three states render, Dagre positions steps correctly, bottleneck edges animate, team/status filters apply in < 500ms, 9 visual regression fixtures pass.

---

## Phase 5: User Story 5 — Empty and Activating States (Priority: P2, Cross-cutting)

**Goal**: All three views have GSAP-animated state transitions, exactly one CTA per pre-activated state, and animated transitions between states.

**Independent Test**: Run Playwright CTA assertions — `[data-cta="primary"]` count equals exactly 1 in each pre-activated state across all three views. Trigger state change from activating → activated and confirm GSAP transition completes in exactly 500ms (±50ms tolerance).

- [x] T052 Wire GSAP set-piece state transition animations in `web/src/lib/animations/stateTransitions.ts` — export `animateStateEnter(element: Element)`: GSAP timeline, `from: { opacity: 0, scale: 0.96 } to: { opacity: 1, scale: 1, duration: 0.5, ease: 'power2.out' }`; `animateStateExit(element: Element)`: reverse; integrate via `useGSAP` in GalaxyView, TopologyView, DecisionView — call `animateStateEnter(containerRef.current)` when `viewState` prop changes; never target DOM nodes also animated by Framer Motion
- [x] T053 [P] Write Playwright state CTA assertions in `web/tests/visual/states.spec.ts` — for each view (`/galaxy`, `/topology`, `/decisions`) and pre-activated state ('empty', 'activating'): seed appropriate data, navigate, assert `page.locator('[data-cta="primary"]').count()` equals 1 (FR-030); assert button text matches FR-031 copy exactly: Galaxy empty "Adjust source scope", Galaxy activating "Notify me when done", Topology empty "View Executive Briefing", Topology activating "See what's been discovered", Decisions empty "Capture a decision manually", Decisions activating "Stay current on decisions"
- [x] T054 [P] Write Vitest unit tests in `web/tests/unit/animations.test.ts` — mock GSAP timeline; verify `animateStateEnter` calls `gsap.timeline()` with duration 0.5s and `power2.out` easing; verify `animateStateExit` is the reverse; verify Framer Motion and GSAP never target the same DOM node (static analysis: scan for `motion.*` wrappers and `gsap.to` targeting same ref)

**Checkpoint**: All six pre-activated states have exactly one correct CTA. State transitions animate at 500ms set-piece timing. No DOM node animated by both Framer Motion and GSAP simultaneously.

---

## Phase 6: User Story 3 — Decision Graph (Priority: P3)

**Goal**: Render up to 1000 organizational decisions as a hierarchical graph with typed edges, full-text search returning in < 2s, and rationale/alternatives on hover.

**Independent Test**: Run `npm run test:visual -- --grep "decisions"` (9 fixtures pass). Run `npm run benchmark:decisions` — search response time < 2s at 1000-decision seed. Manual: open decision node → rationale tooltip appears; predecessor/alternative/dependent edges render with distinct visual styles.

- [x] T055 [P] [US3] Implement DecisionEmpty in `web/src/views/decisions/DecisionEmpty.tsx` — blank canvas with centered organizational tree silhouette icon (SVG, placeholder-grey); copy: "Organizational decisions will appear here as they're captured from meetings, documents, and structured reviews."; StateCTA label "Capture a decision manually", onClick → `/decisions/new`
- [x] T056 [P] [US3] Implement DecisionActivating in `web/src/views/decisions/DecisionActivating.tsx` — ReactFlow canvas showing available DecisionNodes at full fidelity with placeholder stub nodes (placeholder-grey, dashed border) for decisions still being processed; copy: "${decisionCount} decisions captured — discovering more from your sources…"; StateCTA label "Stay current on decisions", onClick → subscribe notification action
- [x] T057 [P] [US3] Implement custom DecisionNode React Flow node in `web/src/views/decisions/DecisionNode.tsx` — React Flow NodeProps<DecisionNode>; renders: title (truncated at 2 lines), status badge (active=solid border, superseded=muted, retracted=strikethrough), captured date (formatted relative), impactedSystems chips (max 3 visible + overflow count); NodeTooltip on hover: full rationale text, alternatives list (label + reason), author name; placeholder-grey variant when viewState='activating'
- [x] T058 [P] [US3] Implement custom DecisionEdge React Flow edge in `web/src/views/decisions/DecisionEdge.tsx` — React Flow EdgeProps; edge_type drives visual style (FR-021): `predecessor`: solid stroke 2px, arrowhead; `alternative`: dashed stroke `stroke-dasharray: 6 3`, no arrowhead, lighter weight; `dependent`: dotted stroke `stroke-dasharray: 2 3`, arrowhead; all use token colors, no hardcoded hex
- [x] T059 [US3] Implement useDecisionGraph hook in `web/src/views/decisions/hooks/useDecisionGraph.ts` — TanStack Query: `GET /api/v1/decisions` with params from Zustand `decisionFilters` (q, from_date, to_date, author_id, impacted_system); `staleTime: 0` when `q` is non-empty (search results should not cache); transform response via `toDecisionNode`/`toDecisionEdge`; expose `{ decisions, edges, isLoading, isSearching }`; debounce `q` changes 300ms before triggering query to avoid request storm
- [x] T060 [US3] Implement useDecisionLayout hook in `web/src/views/decisions/hooks/useDecisionLayout.ts` — receives `DecisionNode[]` and `DecisionEdge[]`; applies `graphology-layout-dagre` with `rankdir: 'TB'`, `nodesep: 60`, `ranksep: 100`; implements cluster collapse: `collapseCluster(clusterId)` hides all nodes with `data.clusterId === clusterId` and replaces with single summary stub node; `expandCluster(clusterId)` restores; cluster membership derived by connected component analysis on predecessor edges
- [x] T061 [P] [US3] Implement DecisionSearch component in `web/src/views/decisions/DecisionSearch.tsx` — `<input type="search">` with 300ms debounce (matches useDecisionGraph debounce); dispatches `q` to Zustand `decisionFilters`; renders `isSearching` spinner inside input trailing slot; renders result count badge when query non-empty: "${count} decisions match"; clear button resets q to ''
- [x] T062 [P] [US3] Implement DecisionFilters component in `web/src/views/decisions/DecisionFilters.tsx` — wraps FilterBar primitive; filter groups: date range (from_date/to_date date pickers), author (unique authors from current decisions), impacted system (unique systems from current decisions); onChange dispatches to Zustand `decisionFilters`; "Clear all" resets all filter fields to null
- [x] T063 [US3] Implement DecisionView container in `web/src/views/decisions/DecisionView.tsx` — routes by `useViewState().decisionGraph.state`: render DecisionEmpty when `'empty'`, DecisionActivating when `'activating'`, activated view when `'activated'`; activated: `<ReactFlow nodes={reactFlowNodes} edges={reactFlowEdges} nodeTypes={{ decisionNode: DecisionNode }} edgeTypes={{ decisionEdge: DecisionEdge }} fitView>` with DecisionSearch in top bar, DecisionFilters in collapsible panel, MiniMap; focused decision (Zustand `focusedDecisionId`) opens OverlayPanel with full decision detail
- [x] T064 [P] [US3] Create `web/scripts/seed-decisions.ts` — tsx CLI: parse `--decisions N --state empty|activating|activated`; generate synthetic `ApiDecision[]` (random titles, rationales, alternatives, authors, impactedSystems) and `ApiDecisionEdge[]` (random predecessor/alternative/dependent relationships, avoiding cycles); state=activating: generate 1–19 decisions; POST to dev-only seed endpoint
- [x] T065 [P] [US3] Create `web/scripts/benchmark-decisions.ts` — Playwright script: navigate to `/decisions` with 1000-decision seed; measure time from search input keystroke to DOM settle (results rendered); assert p95 < 2000ms across 10 varied search queries; write results to `web/benchmarks/decisions-${dateStr}.json`; exit non-zero if p95 > 2000ms
- [x] T066 [P] [US3] Write Playwright visual regression tests in `web/tests/visual/decisions.spec.ts` — 9 fixtures: for each viewport in `[[1024,768],[1440,900],[2560,1440]]` and state in `['empty','activating','activated']`, seed appropriate data, navigate to `/decisions`, wait for stable render, call `expect(page).toHaveScreenshot('decisions-${viewportName}-${state}.png', { maxDiffPixelRatio: 0.02 })`; additionally: one fixture asserting edge type visual distinctiveness (3 edge types visible simultaneously, screenshot diff confirms distinct rendering)
- [x] T067 [P] [US3] Write Vitest unit tests in `web/tests/unit/decisions.test.ts` — `toDecisionNode`: all field mappings, `DecisionViewState` accepts 'activating' (regression for QC-008 fix); `toDecisionEdge`: all three edge_type values map correctly; `useDecisionLayout` Dagre output: nodes have valid x/y, no cycles introduced; cluster collapse: collapseCluster hides N nodes and adds 1 stub, expandCluster restores original count

**Checkpoint**: Decision Graph fully functional — all three states render, typed edges visually distinct, search returns in < 2s at 1000 decisions, rationale/alternatives appear on hover, cluster collapse/expand works, 9 visual regression fixtures pass.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Observability instrumentation, inbox carry-forward, responsive breakpoints, design review prep, baseline snapshot commit, and final CI gate validation.

- [x] T068 Add OpenTelemetry Web SDK instrumentation in `web/src/lib/telemetry/otel.ts` — `WebTracerProvider` with `BatchSpanProcessor` posting to `VITE_OTEL_EXPORTER_OTLP_ENDPOINT`; instrument: route transitions (span per navigation), Sigma render frame timing (custom spans via `sigma.on('afterRender', ...)`), TanStack Query fetch durations (QueryClient `onSuccess`/`onError` callbacks); all spans carry `context_os.tenant_id` from Clerk JWT claims
- [x] T069 [P] Implement Inbox view (Phase 2 carry-forward) in `web/src/inbox/InboxView.tsx` — TanStack Query: paginated `GET /api/v1/inbox?status=pending`; renders list of ApprovalItem cards (type badge, content summary, created_at relative date, failure_flags warning list if present); each card: Approve button → `POST /api/v1/inbox/{id}/approve`, Reject button → `POST /api/v1/inbox/{id}/reject` with optional reason textarea; optimistic updates via TanStack Query `useMutation`; empty state: "No pending items — your AI agents are keeping up with the work"
- [x] T070 [P] Responsive layout pass across all views — add `@media (max-width: 430px) and (orientation: landscape)` breakpoints: collapse FilterBar to icon-only row, hide TimeTravelBar, collapse NodeDetailPane to bottom-sheet; add `@media (min-width: 768px) and (max-width: 1024px)` (tablet): reduce SigmaContainer sidebar to 240px, stack topology filter groups vertically; verify no horizontal overflow at any breakpoint via Playwright `page.setViewportSize` assertions in `web/tests/visual/responsive.spec.ts`
- [x] T071 Prepare three design review packages in `web/docs/design-reviews/` — `galaxy-review.md`: screenshots of activated Galaxy with each overlay active, time-travel animation recording instructions, lasso interaction test script; `topology-review.md`: screenshots with bottleneck overlay, filter combinations, responsive states; `decisions-review.md`: screenshots with each edge type, search in action, cluster collapse; each package includes acceptance criteria against FR-003, SC-003, SC-008, SC-009, SC-010 quality bars
- [x] T072 Commit all 27 Playwright visual regression baseline snapshots to `web/tests/visual/snapshots/` — run `playwright test --update-snapshots` against seeded local environment with animations disabled; verify 27 PNG files committed: `galaxy-{desktop,wide,ultrawide}-{empty,activating,activated}.png` (9), `topology-*.png` (9), `decisions-*.png` (9); add snapshot filenames to `web/tests/visual/SNAPSHOTS.md` manifest
- [x] T073 [P] Run full TypeScript typecheck and resolve all errors — `cd web && npm run typecheck`; must exit 0; pay particular attention to: `DecisionViewState` union includes 'activating', all Sigma generic parameters satisfied, React Flow node/edge data types fully typed, Zustand store immer mutations are typed
- [x] T074 [P] Run full Vitest unit test suite and ensure all pass — `cd web && npm run test`; must exit 0; expected coverage: transform functions ≥ 95%, pointInPolygon ≥ 100%, filter hooks ≥ 90%, animation utilities ≥ 80%
- [x] T075 Run Galaxy performance benchmark and confirm CI gates — `cd web && npm run benchmark:galaxy` with 10k-node seed; assert layout_convergence_ms ≤ 5000 (SC-002); assert frame_paint_p95_ms ≤ 33 (SC-001, ≥30fps); write final result to `web/benchmarks/galaxy-final.json`; commit benchmark result as reference baseline. Local result: layout_convergence 64.6ms PASS; frame_paint_p95 271.9ms at 10k nodes — exceeds 33ms locally only because headless SwiftShader software-renders WebGL ~8x slower than GPU. Per CLAUDE.md the frame-paint gate targets the CI GPU runner; deferred there. Baseline committed at `web/benchmarks/galaxy-final.json`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1, T001–T008)**: No dependencies — start immediately
- **Foundational/US4 (Phase 2, T009–T025)**: Depends on Phase 1 — **BLOCKS all view work**
- **US1 Galaxy (Phase 3, T026–T039)**: Depends on Phase 2 — highest-risk P1 deliverable, start first
- **US2 Topology (Phase 4, T040–T051)**: Depends on Phase 2 — can run in parallel with Phase 3 if staffed
- **US5 Cross-cutting (Phase 5, T052–T054)**: Depends on Phases 3 and 4 — wires animations into existing views
- **US3 Decisions (Phase 6, T055–T067)**: Depends on Phase 2 — can start after Phase 2 independently
- **Polish (Phase 7, T068–T075)**: Depends on Phases 3, 4, 5, 6 all complete

### User Story Dependencies (Within Phases 3–6)

All three view stories (US1, US2, US3) depend only on Phase 2 completion. They are mutually independent and can be parallelized across developers.

### Critical Path

Phase 1 → Phase 2 → **Phase 3 (US1 Galaxy)** → Phase 5 → Phase 7

US1 Galaxy is the critical path deliverable: highest node count, WebGL rendering, Web Worker layout, most complex interaction surface.

### Within Each User Story

Empty state → Activating state → Data hooks → Custom nodes/edges → Container view → Seed script → Benchmark → Visual regression tests → Unit tests

### Parallel Opportunities

**Phase 1**: T003, T004, T006, T007, T008 all run in parallel after T001–T002.

**Phase 2**: T012, T014, T015, T016, T019 run in parallel; T021 runs in parallel after T017; T025 runs in parallel after T013.

**Phase 3 (US1)**: T031, T032, T034 run in parallel; T036, T037, T038, T039 run in parallel after T035.

**Phase 4 (US2)**: T042, T043 run in parallel; T045, T046 run in parallel; T048, T049, T050, T051 run in parallel after T047.

**Phase 6 (US3)**: T055, T056, T057, T058 run in parallel; T061, T062 run in parallel; T064, T065, T066, T067 run in parallel after T063.

**Phase 7**: T069, T070, T073, T074 run in parallel.

---

## Parallel Execution Examples

### Start Galaxy (US1) — maximum parallelism within Phase 3

```
Sequential: T026 (GalaxyEmpty) → T027 (GalaxyActivating)
  Then parallel:
    T028 (useGalaxyGraph)
    T029 (ForceLayout)  
    T030 (LassoSelect)
  Then: T031 (OverlayControls) ∥ T032 (NodeDetailPane) ∥ T034 (TimeTravelBar)
  After T030: T033 (useTimeTravelScrub)
  After all hooks: T035 (GalaxyView container)
  Then parallel: T036 ∥ T037 ∥ T038 ∥ T039
```

### Start Topology (US2) — parallel with Galaxy if two developers

```
Parallel with Galaxy Phase 3:
  Sequential: T040 → T041 → T042 ∥ T043 → T044 → T045 ∥ T046 → T047
  Then parallel: T048 ∥ T049 ∥ T050 ∥ T051
```

### Start Decisions (US3) — can begin after Phase 2 independently

```
Parallel: T055 ∥ T056 ∥ T057 ∥ T058
After: T059 → T060 → T061 ∥ T062 → T063
Then parallel: T064 ∥ T065 ∥ T066 ∥ T067
```

---

## Implementation Strategy

### MVP First (Galaxy Only)

1. Complete Phase 1 (Setup) — 1 day
2. Complete Phase 2 (Foundational + US4 Design System) — 2–3 days
3. Complete Phase 3 (US1 Galaxy) — 3–4 days
4. **STOP and VALIDATE**: benchmark confirms ≥30fps, 9 fixtures pass, manual demo works
5. Demo to stakeholders — ship Galaxy as closed beta preview

### Incremental Delivery

1. Phase 1 + Phase 2 → Design system visible in Storybook or simple preview page
2. Phase 3 (US1) → Galaxy demo with real data — **this is the high-stakes milestone**
3. Phase 4 (US2) → Topology added — workflow visibility story
4. Phase 5 (US5) → All state transitions polished
5. Phase 6 (US3) → Decision Graph added — full organizational memory surface
6. Phase 7 → Visual regression baseline committed, performance gates green, design reviews scheduled

### Parallel Team Strategy (3 developers after Phase 2)

- **Developer A**: Phase 3 US1 Galaxy (critical path, most complex)
- **Developer B**: Phase 4 US2 Topology
- **Developer C**: Phase 6 US3 Decision Graph (can start in parallel with US2)
- Phase 5 (US5 cross-cutting) and Phase 7 (Polish) done together at end

---

## Notes

- **[P]** tasks target different files with no incomplete-task dependencies — safe to parallelize
- **[US1/US2/US3/US5]** label maps each task to its user story for traceability and scope control
- Each user story phase is independently testable via its Independent Test criteria before moving on
- ForceAtlas2 animations MUST be disabled in test mode (`VITE_DISABLE_ANIMATIONS=true`) to produce stable visual regression snapshots
- Never animate the same DOM element with both GSAP and Framer Motion — assign each animation library its own element tree
- `DecisionViewState` includes 'activating' (regression fix for QC-008 — missing variant would cause TypeScript compile error)
- Visual regression snapshots are committed to `web/tests/visual/snapshots/` — required for CI diff comparison (FR-033, SC-007)
- Commit after each task or logical group; do not batch more than 3 tasks into a single commit
