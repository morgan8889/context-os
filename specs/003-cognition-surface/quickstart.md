# Quickstart: Phase 3 — Cognition Surface

**Purpose**: Developer onboarding and test scenario guide for the Cognition Surface frontend.  
**Date**: 2026-05-19

---

## Prerequisites

```bash
# Backend (Phase 1/2) must be running
docker compose -f docker/docker-compose.yml up -d
uv run alembic upgrade head
uv run uvicorn context_os.main:app --reload --port 8000

# Frontend dev server
cd web/
npm install
npm run dev          # Vite dev server on :5173
```

---

## Seed Data

Before running integration scenarios, populate the backend with synthetic graph data.

### Minimal seed (activating state — < 10 initiatives)

```bash
cd web/
npx tsx scripts/seed-graph.ts --initiatives 5 --edges 8 --state activating
```

### Full org-scale seed (activated state — performance benchmark target)

```bash
npx tsx scripts/seed-graph.ts --initiatives 10000 --edges 30000 --state activated
```

### Empty state (no seed needed — this is the default for a fresh tenant)

```bash
# No seed command; just use a fresh Clerk tenant with no ingested data
```

---

## US1 — Initiative Galaxy

### Scenario 1: Empty state renders correctly

**Given**: A tenant with zero initiatives  
**When**: The operator opens `/galaxy`  
**Then**: A placeholder constellation renders in `--color-placeholder-grey`; explanatory copy is visible; exactly one CTA ("Adjust source scope") is present; no blank canvas.

```bash
# Verify with visual regression snapshot
npm run test:visual -- --grep "galaxy-empty"
```

### Scenario 2: Activating state renders correctly

**Given**: A tenant with 5 initiatives seeded  
**When**: The operator opens `/galaxy`  
**Then**: 5 real nodes render; placeholder constellations fill remaining space; copy includes a node count and estimated time; "Notify me when done" CTA is present.

```bash
npx tsx scripts/seed-graph.ts --initiatives 5 --edges 8 --state activating
npm run test:visual -- --grep "galaxy-activating"
```

### Scenario 3: Full graph renders at ≥30fps

**Given**: 10,000 nodes and 30,000 edges loaded  
**When**: The view renders and ForceAtlas2 runs  
**Then**: FPS measured via Chrome DevTools Protocol is ≥30fps; layout converges within 5 seconds.

```bash
npx tsx scripts/seed-graph.ts --initiatives 10000 --edges 30000 --state activated
npm run benchmark:galaxy
# Reports p50/p95 FPS and layout convergence time to benchmarks/galaxy-<date>.json
```

### Scenario 4: Lasso selection works

**Given**: A populated Galaxy view  
**When**: The operator draws a lasso around a cluster using the mouse  
**Then**: Nodes within the lasso are highlighted; the count of selected nodes is shown.

```bash
npm run test:visual -- --grep "galaxy-lasso"
# Or test manually: open :5173/galaxy, hold Shift, drag to draw lasso
```

### Scenario 5: Overlay applies without re-layout

**Given**: A rendered Galaxy with ForceAtlas2 stabilized  
**When**: The operator selects the "Risk" overlay  
**Then**: Node colors update immediately; node positions do not change.

```bash
npm run test:visual -- --grep "galaxy-overlay-risk"
```

### Scenario 6: Time-travel scrub completes in < 500ms

**Given**: Two snapshots available (30 days apart)  
**When**: The operator moves the time-travel scrubber between timestamps  
**Then**: The transition animation completes in under 500ms.

```bash
npx tsx scripts/seed-snapshots.ts --snapshots 2 --interval-days 30
npm run test:perf -- --grep "galaxy-time-travel"
```

---

## US2 — Workflow Topology

### Scenario 1: Empty state (Executive Briefing seed node)

**Given**: A tenant with zero workflows  
**When**: The operator opens `/topology`  
**Then**: One dimmed node labeled "Executive Briefing" renders in `--color-placeholder-grey`; explanatory copy is present; "View Executive Briefing" CTA is present.

```bash
npm run test:visual -- --grep "topology-empty"
```

### Scenario 2: Activating state shows mapped workflows

**Given**: A tenant with 3 workflows seeded  
**When**: The operator opens `/topology`  
**Then**: 3 workflows render at full fidelity; faint anticipated workflow nodes are visible; copy communicates "3 workflows mapped".

```bash
npx tsx scripts/seed-workflows.ts --count 3 --state activating
npm run test:visual -- --grep "topology-activating"
```

### Scenario 3: 500 nodes render with sub-second interaction

**Given**: 500 workflow nodes across 10 workflows  
**When**: The operator pans, zooms, and applies filters  
**Then**: All interactions respond in under 1 second; no jank.

```bash
npx tsx scripts/seed-workflows.ts --count 10 --steps-per-workflow 50 --state activated
npm run test:perf -- --grep "topology-interaction"
```

### Scenario 4: Bottleneck overlay distinguishes slow steps

**Given**: A workflow with steps having varied latency  
**When**: The operator enables the bottleneck overlay (threshold: p95 > 500ms)  
**Then**: Steps with p95 latency above threshold render with animated dashed edges; layout is unchanged.

```bash
npx tsx scripts/seed-workflows.ts --count 5 --inject-bottleneck
npm run test:visual -- --grep "topology-bottleneck"
```

### Scenario 5: Team filter applies in < 500ms

**Given**: Multiple workflows owned by different teams  
**When**: The operator selects "Engineering" in the team filter  
**Then**: Only Engineering workflows are shown; response time < 500ms; filter is applied client-side from loaded data.

```bash
npm run test:perf -- --grep "topology-team-filter"
```

---

## US3 — Decision Graph

### Scenario 1: Empty state renders placeholder decisions

**Given**: A tenant with zero decisions  
**When**: The operator opens `/decisions`  
**Then**: Two placeholder decision nodes render in `--color-placeholder-grey`; explanatory copy is present; "Capture a decision manually" CTA is present.

```bash
npm run test:visual -- --grep "decisions-empty"
```

### Scenario 2: Activating state (1–19 decisions)

**Given**: 10 decisions seeded  
**When**: The operator opens `/decisions`  
**Then**: All 10 decisions render in a full dagre layout (no cluster collapse); copy says "10 decisions captured".

```bash
npx tsx scripts/seed-decisions.ts --count 10 --state activating
npm run test:visual -- --grep "decisions-activating"
```

### Scenario 3: Search locates a known decision in < 2 seconds

**Given**: 1000 decisions loaded  
**When**: The operator searches for "API versioning"  
**Then**: The matching decision is highlighted within 2 seconds of submitting the query.

```bash
npx tsx scripts/seed-decisions.ts --count 1000 --inject-known "API versioning"
npm run test:perf -- --grep "decisions-search"
```

### Scenario 4: Rationale visible on hover

**Given**: A populated Decision Graph  
**When**: The operator hovers over a decision node and holds  
**Then**: A tooltip or side pane shows the decision's rationale and alternatives without navigation.

```bash
npm run test:visual -- --grep "decisions-hover-rationale"
```

### Scenario 5: Date-range filter dims out-of-range predecessors

**Given**: 100 decisions spanning 6 months  
**When**: The operator sets a date-range filter to the last 30 days  
**Then**: Only in-range decisions render at full opacity; predecessor edges pointing outside the range render dimmed, not hidden.

```bash
npx tsx scripts/seed-decisions.ts --count 100 --date-span-months 6
npm run test:visual -- --grep "decisions-date-filter"
```

---

## US4 — Design System & Motion

### Scenario 1: All tokens derive from tokens.css

**Given**: The token set is defined in `src/design-system/tokens.css`  
**When**: A Vitest test enumerates computed CSS custom properties  
**Then**: No hardcoded hex, rgb, or oklch values exist in view-specific component files.

```bash
npm run test -- src/design-system/tokens.test.ts
```

### Scenario 2: Placeholder-grey renders consistently

**Given**: The placeholder-grey token is defined as `oklch(91% 0 0)`  
**When**: Empty/activating states render in all three views  
**Then**: The neutral lightness is visually consistent across views; visual regression locks the specific value.

```bash
npm run test:visual -- --grep "placeholder-grey"
```

### Scenario 3: GSAP set-piece motion plays within timing spec

**Given**: The time-travel scrub transition is triggered  
**When**: The GSAP timeline executes  
**Then**: The transition duration matches `--motion-duration-set-piece` (500ms); no frames drop during the animation.

```bash
npm run test:perf -- --grep "motion-set-piece"
```

### Scenario 4: Shared components appear across views

**Given**: The overlay panel, filter bar, node tooltip, and state CTA are implemented as shared primitives  
**When**: A Vitest snapshot test captures each primitive  
**Then**: The same component is rendered in Galaxy, Topology, and Decision Graph contexts — no per-view reimplementations.

```bash
npm run test -- src/design-system/primitives.test.ts
```

---

## US5 — Empty / Activating States (cross-cutting)

### Scenario 1: Every state has exactly one CTA

```bash
npm run test:visual -- --grep "state-cta-count"
# Asserts: exactly one button[data-cta="primary"] exists in each state fixture
```

### Scenario 2: State copy is view-specific and honest

**Manual review checklist**:
- Galaxy empty: references "source scope" and "initiatives"
- Galaxy activating: includes discovered count + estimated time
- Topology empty: references "Executive Briefing" by name
- Topology activating: includes mapped workflow count
- Decision empty: references "briefing reviews" and "approval"
- Decision activating: includes captured decision count

### Scenario 3: State transitions are animated

**Given**: Ingest delivers a batch of new initiatives while Galaxy is open  
**When**: The view state transitions from activating → activated  
**Then**: The transition plays smoothly; no blank canvas flash.

```bash
npx tsx scripts/trigger-ingest-batch.ts --initiatives 10
# Watch :5173/galaxy for transition animation
```

---

## Visual Regression Snapshot Guide

Snapshots are committed to `tests/visual/snapshots/` and must be regenerated
when intentional UI changes are made.

```bash
# Update all snapshots (run only for intentional design changes)
npm run test:visual -- --update-snapshots

# Run snapshot tests in CI mode (fail on any diff > maxDiffPixelRatio)
npm run test:visual
```

### Fixture Matrix (27 total)

| View | Viewport | State | File |
|---|---|---|---|
| Galaxy | mobile-landscape (1024×768) | empty | `galaxy-mobile-empty.png` |
| Galaxy | mobile-landscape (1024×768) | activating | `galaxy-mobile-activating.png` |
| Galaxy | mobile-landscape (1024×768) | activated | `galaxy-mobile-activated.png` |
| Galaxy | laptop (1440×900) | empty | `galaxy-laptop-empty.png` |
| Galaxy | laptop (1440×900) | activating | `galaxy-laptop-activating.png` |
| Galaxy | laptop (1440×900) | activated | `galaxy-laptop-activated.png` |
| Galaxy | large display (2560×1440) | empty | `galaxy-large-empty.png` |
| Galaxy | large display (2560×1440) | activating | `galaxy-large-activating.png` |
| Galaxy | large display (2560×1440) | activated | `galaxy-large-activated.png` |
| Topology | mobile-landscape | empty | `topology-mobile-empty.png` |
| Topology | mobile-landscape | activating | `topology-mobile-activating.png` |
| Topology | mobile-landscape | activated | `topology-mobile-activated.png` |
| Topology | laptop | empty | `topology-laptop-empty.png` |
| Topology | laptop | activating | `topology-laptop-activating.png` |
| Topology | laptop | activated | `topology-laptop-activated.png` |
| Topology | large display | empty | `topology-large-empty.png` |
| Topology | large display | activating | `topology-large-activating.png` |
| Topology | large display | activated | `topology-large-activated.png` |
| Decisions | mobile-landscape | empty | `decisions-mobile-empty.png` |
| Decisions | mobile-landscape | activating | `decisions-mobile-activating.png` |
| Decisions | mobile-landscape | activated | `decisions-mobile-activated.png` |
| Decisions | laptop | empty | `decisions-laptop-empty.png` |
| Decisions | laptop | activating | `decisions-laptop-activating.png` |
| Decisions | laptop | activated | `decisions-laptop-activated.png` |
| Decisions | large display | empty | `decisions-large-empty.png` |
| Decisions | large display | activating | `decisions-large-activating.png` |
| Decisions | large display | activated | `decisions-large-activated.png` |

---

## Performance Benchmark Reference

Benchmark outputs are written to `benchmarks/` and committed after each run on
a GPU-capable runner. Do not rely on headless CI FPS values for absolute benchmarks.

```bash
# Run galaxy benchmark (requires 10k-node seed)
npm run benchmark:galaxy
# Output: benchmarks/galaxy-<date>.json
# Keys: layout_convergence_ms, frame_paint_p50_ms, frame_paint_p95_ms

# Run topology benchmark (requires 500-node seed)
npm run benchmark:topology
# Output: benchmarks/topology-<date>.json
# Keys: pan_p95_ms, zoom_p95_ms, filter_p95_ms

# Run decision search benchmark (requires 1000-decision seed)
npm run benchmark:decisions
# Output: benchmarks/decisions-<date>.json
# Keys: search_p50_ms, search_p95_ms
```
