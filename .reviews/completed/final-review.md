# Final Branch Code Review — 5-goal-driven-ux

**Reviewed against**: spec `specs/005-goal-driven-ux/spec.md` (Tier A only — FR-001–FR-014)
**Branch**: `5-goal-driven-ux` vs `main`
**Reviewer**: Claude Sonnet 4.6
**Date**: 2026-05-26

---

## Files Reviewed

### Backend (Python)
- `src/context_os/api/admin.py` — new `POST /admin/integrations/github/connect` endpoint
- `src/context_os/api/graph.py` — `POST /graph/signals`; `GET /graph/nodes` returning all node types
- `src/context_os/api/ingest.py` — `_age_label` / `node_type` separation in ingest loop
- `src/context_os/ingestion/github/normalizer.py` — PascalCase `_age_label` + lowercase `node_type`
- `src/context_os/relational/repositories.py` — `OAuthTokenRepository.upsert` (token encryption path)
- `src/context_os/auth/dependencies.py` — `TenantContext` shape

### Frontend (TypeScript/React)
- `web/src/views/onboarding/OnboardingView.tsx` — two-tab layout (GitHub connect + sample data)
- `web/src/inbox/InboxView.tsx` — `GenerateBriefingButton`, `LogSignalForm`, type badge tooltips
- `web/src/components/AppShell.tsx` — 56px sidebar, inbox badge, help link
- `web/src/design-system/primitives/FirstVisitCallout.tsx` — one-time orientation message
- `web/src/design-system/primitives/HintTooltip.tsx` — `?` icon tooltip wrapper
- `web/src/views/galaxy/GalaxyView.tsx` — `FirstVisitCallout` + `GalaxyLegend` in activated state
- `web/src/views/galaxy/GalaxyLegend.tsx` — collapsible color legend
- `web/src/views/galaxy/OverlayControls.tsx` — overlay buttons with tooltips
- `web/src/views/galaxy/GalaxyEmpty.tsx` — honest empty state copy
- `web/src/views/galaxy/GalaxyActivating.tsx` — activating state with partial nodes
- `web/src/views/galaxy/hooks/useGalaxyGraph.ts` — paginated graph fetch
- `web/src/views/galaxy/ForceLayout.tsx` — ForceAtlas2 lifecycle
- `web/src/views/topology/TopologyEmpty.tsx` — duplicate style fix
- `web/src/views/topology/TopologyView.tsx` — `FirstVisitCallout` in activated state
- `web/src/views/decisions/DecisionView.tsx` — `FirstVisitCallout` in activated state
- `web/src/views/decisions/DecisionEmpty.tsx` — honest empty state, no broken CTA
- `web/src/lib/api/client.ts` — axios client with Clerk JWT interceptor
- `web/src/lib/transforms/initiative.ts` — snake_case → camelCase transform
- `web/src/router.tsx` — AppShell layout route with lazy-loaded children

---

## Stage 1: Spec Compliance Matrix

| # | Criterion | Status | Test? | Evidence |
|---|-----------|--------|-------|----------|
| FR-001 | One-time dismissible orientation message on first visit to each view | YES | NO | `FirstVisitCallout` rendered in activated state of Galaxy (`GalaxyView.tsx:254`), Topology (`TopologyView.tsx:297`), Decision (`DecisionView.tsx:374`), Inbox (`InboxView.tsx:707`) |
| FR-002 | Each message includes view purpose, main object type, primary action | YES | NO | Copy present in each mount site; Galaxy describes overlay controls, Topology describes workflow rows, Decisions describes search, Inbox describes approve/reject |
| FR-003 | Dismissal persists — message never re-appears after dismiss | YES | NO | `localStorage.setItem(storageKey, 'true')` in `dismiss` callback (`FirstVisitCallout.tsx:24`); initialized with `localStorage.getItem(storageKey) !== 'true'` |
| FR-004 | Tooltip on each overlay control (Load/Risk/Autonomy/Ownership) | YES | NO | `Tooltip` wrapping each `OverlayButton` in `OverlayControls.tsx:73`; `OVERLAY_BUTTONS` array includes `tooltip` string for all four |
| FR-005 | Visible legend mapping node-type colours and status indicators | YES | NO | `GalaxyLegend.tsx` with `NODE_ENTRIES` and `STATUS_ENTRIES` rendered in activated Galaxy |
| FR-006 | Legend is collapsible; state persists across sessions | YES | NO | `localStorage` key `ctx_os_legend_galaxy` read on mount (`GalaxyLegend.tsx:49`); toggle writes `'expanded'` or removes key |
| FR-007 | Inbox card type badge includes accessible explanation | YES | NO | `TYPE_TOOLTIPS` record with `HintTooltip` for all three item types (`InboxView.tsx:103–110, 218`) |
| FR-008 | Failure flags section shows contextual explanation | YES | NO | `HintTooltip` on the failure flags header explains they are not blocking (`InboxView.tsx:241–245`) |
| FR-009 | Navigation shows live count badge for pending inbox items | YES | NO | `AppShell.tsx:134` computes `pendingCount` from TanStack Query; `NavItem` renders badge when `badge > 0` |
| FR-010 | Navigation includes persistent help/docs link | YES | NO | Help icon pinned to bottom of sidebar (`AppShell.tsx:160–174`); `onClick` prevents navigation with tooltip "Docs coming soon" |
| FR-011 | Galaxy empty state accurately describes why empty; CTA links to functional page | YES | NO | `GalaxyEmpty.tsx` copy distinguishes processing state from empty; CTA navigates to `/onboarding` which exists |
| FR-012 | Decisions empty state describes how decisions enter graph; no broken CTA | YES | NO | `DecisionEmpty.tsx` — copy explains briefing cycle; no CTA rendered at all |
| FR-013 | Guidance copy uses operator language only | YES | NO | Copy reviewed across all components: "briefing", "initiative", "dependency", "risk", "workflow" used throughout; no "unlock", "empower", "intelligent", "seamless" found |
| FR-014 | All guidance elements meet WCAG AA contrast | PARTIAL | NO | Colours use OKLCH; `oklch(42% 0 0)` on white (`FirstVisitCallout.tsx:68`) is borderline; no automated contrast test in CI |

**Compliance: 13/14 criteria fully met, 1 partial (FR-014 contrast not CI-gated).**

---

## Stage 2: Code Review Findings

### CRITICAL

None found. No SQL injection vectors (AGE queries use parameterised input via the AGE parameter map; no user values are interpolated directly into Cypher strings). Clerk JWT authentication enforces on every route. Token encryption (Fernet AES-256) is intact through the repository layer.

---

### HIGH

**[`src/context_os/api/admin.py:190`] Internal error detail exposed to client**

The `HTTPException` raised on token store failure includes `str(e)` in the `message` field:
```python
detail={"code": "token_store_error", "message": str(e)}
```
This can leak database error strings (table names, constraint names, connection strings) to the API consumer. Replace with a generic user-facing message and log the full exception server-side only. The existing `logger.error` call already logs the detail.

**[`web/src/inbox/InboxView.tsx:442`] `setInterval` in `GenerateBriefingButton` has no unmount cleanup**

`handleGenerate` starts a `setInterval(poll, 3000)` but the component has no `useEffect` cleanup. If the user navigates away from the Inbox while a briefing is generating, the interval continues firing, calling `setStatus` and `onDone` on an unmounted component. This will trigger React's "Can't perform a state update on an unmounted component" warning and could cause stale closures to invalidate queries on wrong pages.

Fix: convert to a `useEffect`-managed interval with a ref, or use a `useRef` to hold the interval ID and clear it in a cleanup function returned from a `useEffect` that tracks the generating state.

**[`src/context_os/api/graph.py:617–624`] `ManualSignalRequest` has no input length or type constraints**

`content: str` and `signal_type: str` have no `max_length`, `min_length`, or enum constraints. A client can POST arbitrarily large content strings (multi-MB), driving unbounded AGE node property size, and any arbitrary `signal_type` value (e.g. `"<script>"`). The AGE MERGE is parameterised so there is no injection risk, but the content is stored verbatim and returned to the UI without sanitisation.

Minimum fix: add `Field(max_length=10_000)` on `content` and `Literal["observation", "risk", "blocker", "decision"]` on `signal_type`. The frontend already constrains to these four values via `SIGNAL_TYPES`, but the API must enforce it independently.

**[`src/context_os/ingestion/github/normalizer.py:235`] `user_to_actor` uses PascalCase `node_type` without `_age_label`**

All other normalizer methods separate the AGE label (`_age_label: "Initiative"`) from the ontology type (`node_type: "project"`). `user_to_actor` sets `"node_type": "Actor"` (PascalCase) and has no `_age_label` key. In `ingest.py:166`, the ingest loop does `age_label = node.pop("_age_label", node_type)`, so it falls back to `node_type = "Actor"` — which is correct for the AGE label but leaves `node_type` as `"Actor"` (PascalCase) in the persisted properties dict, inconsistent with every other node type (`"project"`, `"goal"`, `"signal"`, `"artifact"`). This will cause `_props_to_api_node` in `graph.py:416` to return `node_type="Actor"` to the frontend, which the `toInitiativeNode` transform will pass through as-is, and the galaxy's `NODE_COLOR_MAP` will not have an entry for `"Actor"`, falling back to the wrong colour. The method is not called in the current ingest pipeline (no reference in `_run_github_ingest`), but the inconsistency is a correctness trap for the next person who wires it.

---

### MEDIUM

**[`web/src/views/galaxy/hooks/useGalaxyGraph.ts:83`] Graphology graph re-created on every render**

```typescript
const graph = new Graph({ type: 'mixed', multi: false });
```
This runs on every render of any component that calls `useGalaxyGraph`. While the graph object is passed to `ForceLayout` which guards via `loadGraph(graph, true)`, the re-creation is wasteful and can cause subtle bugs if consumers compare graph identity. The graph construction should be wrapped in `useMemo` keyed on the page data.

**[`web/src/inbox/InboxView.tsx:109`] Curly apostrophe in string literal is a code-smell**

```
'A risk flag raised by the AI against a specific initiative. Approve to acknowledge; reject if it's not applicable.',
```
The apostrophe in `it's` is U+2019 (RIGHT SINGLE QUOTATION MARK), while the string delimiter is U+0027 (APOSTROPHE). TypeScript/JS parses this correctly, but linters and some editors flag curly quotes in code strings. Change to `it's` (straight apostrophe) or escape it explicitly.

**[`src/context_os/api/graph.py:655`] UUID5 collision on identical content within the same second**

```python
node_id = str(
    _uuid.uuid5(
        _uuid.UUID("00000000-0000-0000-0000-000000000002"),
        f"{tenant.tenant_id}:manual:{body.content[:64]}:{now}",
    )
)
```
`now = datetime.now(UTC).isoformat()` — if two requests arrive in the same microsecond with the same content prefix, they produce the same UUID and the second `upsert_node` silently overwrites the first. Use `uuid4()` for manual signals where deduplication is not a design requirement, or document this constraint.

**[`web/src/views/galaxy/ForceLayout.tsx:113`] Hard-coded 5-second layout convergence timer**

The `setTimeout(..., 5000)` that stops ForceAtlas2 and fits the camera fires unconditionally 5 seconds after mount, regardless of whether the graph has actually converged. On large graphs this is too short; on trivial graphs it is too long. At minimum, document why 5 seconds was chosen, or expose it as a prop / environment variable.

**[`web/src/lib/transforms/initiative.ts:17`] Random node positions on every re-render**

```typescript
x: (Math.random() - 0.5) * 400,
y: (Math.random() - 0.5) * 400,
```
`toInitiativeNode` is called inside `useGalaxyGraph` during render. Because the graph is re-created on every render (see above), every render assigns new random positions to every node. ForceAtlas2 compensates, but this causes visual jitter during re-renders and prevents stable position persistence between renders. Positions should either be seeded deterministically (e.g. from node ID hash) or preserved across renders when the graph object is memoised.

**[`web/src/design-system/primitives/FirstVisitCallout.tsx:59`] `role="complementary"` is semantically incorrect**

The ARIA `complementary` landmark (`<aside>`) is for content that complements the main content but is independently meaningful. A dismissible orientation tooltip is better represented as `role="status"` (live region) or `role="dialog"` with `aria-modal="false"`. The current role will cause screen readers to announce it incorrectly in the landmark navigation.

**[`web/src/components/AppShell.tsx:165`] Help link is a dead `<a href="#">`**

```tsx
href="#"
onClick={(e: MouseEvent<HTMLAnchorElement>) => e.preventDefault()}
```
The spec says (Assumptions section): "The help link can link to a 'coming soon' page or be replaced with a visible placeholder — but it must exist in the navigation as a signal that help exists." The tooltip says "Docs coming soon." This is acceptable per spec, but using `<a href="#">` with a click-preventer is fragile — middle-click and right-click → "open in new tab" will still navigate to `#`. Use `<button type="button">` instead, or set `href` to a real placeholder URL.

---

### LOW / Style

**[`src/context_os/api/admin.py:154–155`] `GitHubConnectRequest.token` has no blank/empty validation**

`token: str` will accept an empty string `""`. Pydantic V2 does not strip or validate length by default. Add `Field(min_length=1)` or a `@field_validator` to reject blank tokens before they reach the repository.

**[`src/context_os/api/graph.py:437`] `list_nodes` docstring says "initiative nodes" but now returns all types**

```python
"""Paginated list of initiative nodes for the galaxy canvas."""
```
After this branch change, `node_type=None` is passed to `get_nodes_for_tenant`, returning Goal, Signal, Artifact, and Initiative nodes. Update the docstring to reflect this.

**[`web/src/views/topology/TopologyView.tsx:28–31`] Repeated `eslint-disable` for `any` cast on ReactFlow custom node/edge types**

Two consecutive `eslint-disable-next-line` comments suppress `@typescript-eslint/no-explicit-any` for the `NODE_TYPES` and `EDGE_TYPES` casts. The proper fix is to type the custom node/edge components correctly against React Flow's generic `NodeProps<T>` / `EdgeProps`. This is a carry-forward issue but worth addressing in a cleanup PR.

**[`web/src/views/galaxy/GalaxyActivating.tsx:37`] `color-mix()` usage for Sigma node colours**

```typescript
color: `color-mix(in oklch, var(--color-node-${node.type}), transparent 50%)`,
```
Sigma v3's WebGL renderer cannot parse `color-mix()` (same constraint as oklch noted in project memory). The 1×1 canvas technique from `GalaxyView.tsx` is not applied here. This will likely render nodes as opaque black or the fallback grey. The activating state may be visually broken for real nodes; stub nodes use a CSS variable directly which also won't work in Sigma's WebGL context.

**[`web/src/inbox/InboxView.tsx` general`] `GenerateBriefingButton` has no maximum poll duration guard**

If the briefing API enters a permanent non-terminal state (neither `completed`, `approved`, nor `failed`), the `setInterval` runs indefinitely at 3-second intervals until the user navigates away (or, given the missing cleanup, even after). Add a poll timeout (e.g. 5 minutes) after which the interval is cleared and an error message is shown.

---

## Summary of Key Findings

**Security**: No injection or auth bypass issues. One information leakage issue in admin error response (`str(e)` exposed to client).

**Performance**: Graph re-created on every render; random node positions re-assigned every render. Both are correctness and stability issues in addition to performance.

**Correctness**: `setInterval` in `GenerateBriefingButton` has no unmount cleanup — memory/state leak on navigation. `user_to_actor` in the GitHub normalizer uses PascalCase `node_type` inconsistently with no `_age_label`. `color-mix()` in `GalaxyActivating.tsx` will not render correctly in Sigma v3 WebGL.

**Maintainability**: `ManualSignalRequest` missing input constraints. Hard-coded 5-second convergence timer. Dead help link pattern.

---

## Verdict: CONDITIONAL_PASS

**Block on before merge:**
1. Add unmount cleanup to `GenerateBriefingButton` interval (`InboxView.tsx:442`)
2. Fix `color-mix()` in `GalaxyActivating.tsx:37` — use the same 1×1 canvas converter as `GalaxyView.tsx`

**Fix before next sprint:**
3. Replace `str(e)` with a generic message in the `HTTPException` detail in `admin.py:190`
4. Add `max_length` and `Literal` constraints to `ManualSignalRequest` in `graph.py`
5. Add `_age_label: "Actor"` and lowercase `node_type: "actor"` to `user_to_actor` in `normalizer.py`
6. Wrap graphology graph construction in `useMemo` in `useGalaxyGraph.ts`
7. Add a maximum poll duration to `GenerateBriefingButton`

