# Data Model: Phase 5 — Goal-Driven UX & In-Context Guidance

**Created**: 2026-05-21  
**Note**: All entities are client-side only. No backend schema changes.

---

## Entity 1: OrientationMessageState (localStorage)

Tracks whether a first-visit callout has been dismissed for a given view.
Persisted in browser localStorage. Keyed per-view.

| Key | Type | Values | Description |
|-----|------|--------|-------------|
| `ctx_os_visited_galaxy` | string \| null | `"true"` \| `null` | Galaxy callout dismissed |
| `ctx_os_visited_topology` | string \| null | `"true"` \| `null` | Topology callout dismissed |
| `ctx_os_visited_decisions` | string \| null | `"true"` \| `null` | Decisions callout dismissed |
| `ctx_os_visited_inbox` | string \| null | `"true"` \| `null` | Inbox callout dismissed |
| `ctx_os_inbox_hint` | string \| null | `"true"` \| `null` | First-approval hint dismissed |

**Read**: On component mount (`useEffect` with `[]` deps).  
**Write**: On user dismiss action (button click or Escape key).  
**Reset**: `localStorage.removeItem(key)` — no automatic expiry.

---

## Entity 2: LegendPanelState (localStorage)

Controls collapsed/expanded state of the GalaxyLegend panel across sessions.

| Key | Type | Values | Description |
|-----|------|--------|-------------|
| `ctx_os_legend_galaxy` | string \| null | `"expanded"` \| `null` | Legend expanded; default collapsed |

**Read**: On GalaxyLegend mount.  
**Write**: On user toggle action.

---

## Entity 3: PendingItemCount (TanStack Query cache)

Derived from the existing `GET /api/v1/inbox?status=pending` response. Not a
new API call — the AppShell Inbox badge reads from the same TanStack Query
cache as InboxView using the shared query key `['inbox']`.

| Field | Source | Description |
|-------|--------|-------------|
| `count` | `data.items.length` | Number of pending approval items |
| `isLoading` | TanStack Query state | Whether the fetch is in-flight |
| `isError` | TanStack Query state | Whether the fetch failed (badge hidden on error) |

**Query key**: `['inbox']` (matches `inboxKeys.list()` in `web/src/lib/api/queryKeys.ts`).  
**Refetch interval**: `30_000` ms (matches InboxView polling pattern).  
**Badge display**: Hidden when `count === 0` or `isError`. Shows `count` up to
`9`; shows `"9+"` when `count > 9`. Hidden when active route is `/inbox`.

---

## Entity 4: OverlayTooltipContent (static)

Static lookup table mapping overlay type to tooltip description copy.
Not persisted; defined as a constant in `OverlayControls.tsx`.

| Overlay Type | Copy |
|-------------|------|
| `load` | "Workload overlay — darker nodes carry more active work. Identify overloaded teams." |
| `risk` | "Risk overlay — red = flagged at-risk, amber = moderate risk." |
| `autonomy` | "Autonomy overlay — shows AI autonomy level per initiative (0–5 scale)." |
| `ownership` | "Ownership overlay — colours initiatives by owning team. Spot ownership gaps." |

---

## Entity 5: InboxItemTypeMeta (static)

Static lookup table mapping inbox item type to human label and tooltip explanation.
Not persisted; used in `InboxView.tsx`.

| Type | Label | Tooltip |
|------|-------|---------|
| `briefing_draft` | "Briefing Draft" | "A weekly synthesis drafted by the Operational Synthesizer agent. Approve to schedule delivery; reject to flag an issue." |
| `proposed_dependency` | "Proposed Dependency" | "A dependency relationship between two initiatives, inferred from your work signals. Approve to record in the graph." |
| `proposed_risk` | "Proposed Risk" | "A risk flag raised by the AI against a specific initiative. Approve to acknowledge; reject if it's not applicable." |

---

## Entity 6: LegendColorEntry (static)

Static data for the GalaxyLegend panel color swatches. Derived from CSS tokens.

| Node Type | CSS Token | Label |
|-----------|-----------|-------|
| Goal | `--color-node-goal` | "Goal" |
| Project | `--color-node-project` | "Project" |
| Signal | `--color-node-signal` | "Signal" |
| Artifact | `--color-node-artifact` | "Artifact" |

| Status | CSS Token | Label |
|--------|-----------|-------|
| Active | `--color-status-active` | "Active" |
| At risk | `--color-status-at-risk` | "At risk" |
| Paused | `--color-status-paused` | "Paused" |
| Complete | `--color-status-complete` | "Complete" |
