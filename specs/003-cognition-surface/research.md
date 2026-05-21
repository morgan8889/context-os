# Research: Cognition Surface (Phase 3)

**Branch**: `3-cognition-surface` | **Date**: 2026-05-19
**Resolved unknowns**: Build framework, Sigma.js/Graphology integration, design token architecture, motion library strategy, visual regression testing for Canvas/WebGL

---

## Decision 1: Vite + React SPA (not Next.js)

**Decision**: Build the frontend as a Vite 6 + React 19 SPA (Single Page Application), not a Next.js App Router application.

**Rationale**:
- All three graph libraries (Sigma.js, React Flow, Graphology/dagre) access `window`, `document`, and WebGL contexts — this causes SSR crashes in Next.js. Workarounds (`'use client'`, dynamic imports) add complexity with zero benefit since the app is 100% authenticated/client-only.
- Sigma.js v3 itself migrated from Webpack to Vite, signaling ecosystem alignment.
- `forceatlas2-worker` runs in a Web Worker. Next.js App Router (React Server Components) complicates Web Worker setup; Vite supports workers natively with zero config.
- Vite build times in CI: 0.5–2s cold, 100–300ms incremental. Next.js: 15–30s cold. Significant CI cost saving.
- Clerk React SDK works identically in both; no auth advantage to Next.js.

**Alternatives considered**:
- Next.js 15 App Router: rejected (SSR incompatibility with WebGL, RSC Web Worker friction, CI overhead).
- Remix: rejected (same SSR issue for graph libs).
- Vanilla Vite + no framework: rejected (too much manual wiring for routing, auth, and DX).

---

## Decision 2: Sigma.js v3 via @react-sigma/core (Galaxy)

**Decision**: Use `@react-sigma/core` (React wrapper for Sigma.js v3) + `graphology` + `@react-sigma/layout-forceatlas2` for Initiative Galaxy.

**Rationale**:
- `@react-sigma/core` provides `<SigmaContainer>`, `useSigma()`, `useLoadGraph()`, `useSetSettings()`, and `useCamera()` hooks — no manual ref management.
- `forceatlas2-worker` runs via `LayoutSupervisor` in a dedicated Web Worker; layout computation never blocks the main thread. Supervisor can be started/stopped/reconfigured without destroying state.
- Sigma v3 uses WebGL exclusively (NodeProgram/EdgeProgram vertex+fragment shaders). Canvas fallback is deprecated. This gives ≥30fps at 10k nodes/30k edges on M-series Mac and mid-range Windows laptops.
- Overlay composition uses **node/edge reducers** (`sigma.setSetting('nodeReducer', fn)`) — recompute per frame with zero relayout cost.
- Incremental node addition (activating state): nodes added to Graphology with pre-set positions are incorporated immediately; locked positions prevent ForceAtlas2 from repositioning them until explicitly unlocked.
- Time-travel scrub: `graphology.export()` serializes graph state; `graph.import(snapshot)` restores it; `sigma.getCamera().animate({ ... }, { duration: <500 })` handles the visual transition.

**Lasso selection**: Sigma v3 has no built-in lasso for WebGL. Implementation uses `sigma.getNodeDisplayData(nodeId)` to get screen-space coordinates and manual point-in-polygon testing against the drawn lasso path. This is the expected approach per Sigma's maintainer documentation.

**Alternatives considered**:
- Cosmograph: excellent at scale but proprietary license; poor control over visual customization ceiling.
- Gephi.js/Cytoscape.js: lower perf ceiling than Sigma WebGL at 10k+ nodes.
- Three.js custom renderer: highest ceiling but massive implementation cost; not justified for MVP.

---

## Decision 3: React Flow v12 (Workflow Topology)

**Decision**: Use React Flow v12 (formerly `reactflow`, now `@xyflow/react`) for Workflow Topology.

**Rationale**:
- Best DX for structured/declarative graphs; custom node components are native React components — status, ownership, and autonomy markers are trivially rendered.
- Sub-second interaction at 500 nodes is well-established in React Flow.
- Bottleneck and latency overlays implemented via custom edge components with animated stroke-dashoffset.
- Filter state managed in Zustand; React Flow re-renders only affected nodes via memo.

**Alternatives considered**:
- Sigma.js for Topology too: rejected — structured layout (Dagre) inside Sigma is awkward; React Flow's structured layout is native.
- Vis.js: rejected (older API, worse TypeScript support).

---

## Decision 4: Graphology + @dagrejs/dagre (Decision Graph)

**Decision**: Use `graphology` for the graph data model and `@dagrejs/dagre` for hierarchical layout, rendered via React Flow (not Sigma) for the Decision Graph.

**Rationale**:
- Dagre produces layered hierarchical layouts suited to decision predecessor/alternative/dependent relationships.
- Rendering via React Flow (same library as Topology) reduces total library surface — one renderer for two views.
- `graphology-layout-dagre` provides a Graphology adapter for Dagre layout results.
- React Flow's custom node API handles decision rationale display (hover/pane) natively.

**Alternatives considered**:
- Sigma + dagre: possible but Sigma's WebGL renderer doesn't give React component flexibility for rich node content.
- ELK.js: more powerful hierarchical layout than dagre, but significantly heavier; dagre sufficient for ≤1000 decisions.

---

## Decision 5: shadcn/ui (Radix + Tailwind) for Design System

**Decision**: Use shadcn/ui as the component foundation — Radix UI primitives styled with Tailwind CSS, copied into the project (`src/design-system/`) rather than installed as a dependency.

**Rationale**:
- Single-source-of-truth tokens: CSS custom properties defined in `src/design-system/tokens.css` are consumed by both Tailwind config (`tailwind.config.ts` → `colors: { 'placeholder-grey': 'var(--color-placeholder-grey)' }`) and Radix component overrides.
- Placeholder-grey token: `--color-placeholder-grey: oklch(91% 0 0)` (≈ Tailwind `neutral-200`, #e5e7eb) — applied consistently across all empty/activating states in all three views.
- Copying components in (not installing a package) gives full control over token overrides and custom motion integration.

**Alternatives considered**:
- Bare Radix + manual Tailwind: same end result but more bootstrapping time.
- MUI / Chakra: rejected (opinionated theming conflicts with custom graph aesthetics).

---

## Decision 6: GSAP + Framer Motion (two-tier motion)

**Decision**: GSAP v3.12+ for set-piece transitions; Framer Motion v11+ for everyday component animations. They coexist without conflict.

**Rationale**:
- No event listener or RAF conflicts — they operate at different abstraction levels (GSAP: imperative DOM/timeline; Framer Motion: declarative React).
- GSAP used at page/canvas level: time-travel scrub timeline, empty→activating→activated state sequence, hero-section transitions.
- Framer Motion at component level: hover states, panel open/close, selection animation, filter bar collapse.
- **Critical rule**: Never animate the same DOM node with both simultaneously. Isolate by scope.
- Use `@gsap/react`'s `useGSAP()` hook for automatic timeline cleanup on unmount (prevents memory leaks and RAF conflicts).
- **License**: GSAP Standard License is free for commercial SaaS since April 2025. No licensing cost for Context-OS.

**Alternatives considered**:
- GSAP only: could work, but Framer Motion's declarative API is significantly better DX for component-level animations.
- Framer Motion only: insufficient control for complex timeline sequences (time-travel scrub requires precise sequencing).
- CSS transitions only: insufficient for the set-piece bar (60-second demo-able transitions).

---

## Decision 7: Visual Regression via Playwright (with tolerance)

**Decision**: Playwright v1.x `toHaveScreenshot()` with `maxDiffPixelRatio: 0.02` and `--force-device-scale-factor=1` for visual regression. CI runs in Playwright's official Docker image for rendering consistency.

**Rationale**:
- Playwright screenshots capture WebGL Canvas output correctly in headless Chrome when rendering is GPU-accelerated or consistently CPU-fallback.
- `maxDiffPixelRatio: 0.02` accounts for GPU anti-aliasing variance between environments.
- Determinism via: fixed `forceatlas2` seed, animations disabled during snapshot, Playwright official Docker image (consistent fonts, GPU drivers).
- 27 snapshot fixtures: 3 views × 3 viewports × 3 states (empty, activating, activated) — committed to `tests/visual/snapshots/`.

**Frame-rate benchmarking**: FPS in headless CI is not reliable for absolute values. Instead, use Chrome DevTools Protocol timing traces to measure frame paint duration and detect regressions (not absolute FPS). True GPU-level FPS benchmarks run on a dedicated GPU-capable runner (not standard CI) and are documented in `benchmarks/`.

**Alternatives considered**:
- Chromatic: good for component stories but less suited to full-page WebGL snapshots.
- Percy/AppliTools: structural AI-based comparison, but adds external service dependency; Playwright sufficient.
- headless-gl (Node.js): adds complexity; Playwright + headless Chrome is simpler.

---

## Decision 8: Zustand + React Query for State Management

**Decision**: Zustand v5 for graph interaction state (selection, overlays, filters, time-travel cursor); TanStack Query v5 (React Query) for API data fetching and caching.

**Rationale**:
- Zustand's flat atom model suits large graph state (selection sets of 10k nodes must not cause React re-render storms). Sigma, React Flow, and Graphology own their own render graphs; Zustand manages what the user has selected/filtered/configured.
- TanStack Query handles: API fetching, cache invalidation, background refetch, loading/error states for all three views.
- Clerk JWT token is injected into all API calls via TanStack Query's `queryClient` default options.

**Alternatives considered**:
- Jotai: similar performance profile; Zustand chosen for simpler DevTools integration.
- Redux Toolkit: too verbose for this scale; Zustand suffices.
- SWR: replaced by TanStack Query due to better mutation support and devtools.

---

## Decision 9: TypeScript 5.x, Vitest for Unit Tests

**Decision**: TypeScript 5.x (strict mode), Vitest for unit tests (graph state logic, reducers, data transforms). Vitest is Vite-native and 5–10× faster than Jest in CI.

**Rationale**: TypeScript strict mode catches null/undefined issues in graph data (missing node attributes, edge endpoints). Vitest shares Vite's transform pipeline — no separate Jest config needed.

---

## Summary Table

| Concern | Decision | Library/Tool |
|---------|----------|-------------|
| Build framework | Vite 6 SPA | `vite`, `@vitejs/plugin-react` |
| Galaxy renderer | Sigma.js v3 (WebGL) | `@react-sigma/core`, `graphology`, `@react-sigma/layout-forceatlas2` |
| Topology renderer | React Flow v12 | `@xyflow/react` |
| Decision renderer | Graphology + dagre → React Flow | `graphology`, `@dagrejs/dagre`, `@xyflow/react` |
| Design system | shadcn/ui (Radix + Tailwind) | `@radix-ui/*`, `tailwindcss`, shadcn copied components |
| Motion (set-piece) | GSAP v3.12 | `gsap`, `@gsap/react` |
| Motion (everyday) | Framer Motion v11 | `framer-motion` |
| State (interaction) | Zustand v5 | `zustand` |
| State (API data) | TanStack Query v5 | `@tanstack/react-query` |
| Auth | Clerk React SDK | `@clerk/react` |
| Unit tests | Vitest | `vitest`, `@testing-library/react` |
| Visual regression | Playwright | `@playwright/test` |
| TypeScript | TypeScript 5.x strict | `typescript` |
