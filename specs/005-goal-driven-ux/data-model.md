# Data Model: Phase 5 — Goal-Driven UX & In-Context Guidance

**Created**: 2026-05-21  
**Updated**: 2026-05-22 (Tier B target entities added)

**Note**: Entities are split by scope tier.

- **Tier A (Phase 5, this build) — Entities 1–6**: client-side only
  (localStorage / TanStack Query cache / static lookups). No backend schema
  changes.
- **Tier B (Deferred — Phase 6/7) — Entities 7–10**: backend **target models**
  for the process re-architecture objective. These are NOT implemented in the
  Phase 5 build. Per Constitution Principle II they MUST be persisted as typed
  graph nodes/edges with provenance (the field tables below are logical
  shapes, not a sanctioned client-side schema). Final field definitions,
  ontology mapping (Principle VII), and persistence belong to the Phase 6/7
  plan.

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

---

## Tier B — Strategic Extension Entities (AI Process Transformation, Deferred — Phase 6/7)

The following entities are **target-model definitions** for the process
re-architecture objective (US6–US9). They are **not implemented in the Phase 5
build**. Per Principle II they will be persisted as graph nodes/edges with
provenance; the tables below are logical shapes pending the Phase 6/7 plan.

## Entity 7: ProcessBaseline

Represents current-state process behaviour prior to AI redesign.

| Field | Type | Description |
|-------|------|-------------|
| `process_id` | string | Stable process identifier |
| `name` | string | Human-readable process name |
| `stages` | Stage[] | Ordered process stages with owner and SLA |
| `handoffs` | Handoff[] | Transitions between teams/stages |
| `cycle_time_ms_p50` | number | Median end-to-end cycle time |
| `cycle_time_ms_p90` | number | P90 end-to-end cycle time |
| `rework_rate` | number | Fraction of work that loops back |
| `failure_modes` | FailureMode[] | Known failure categories and frequency |
| `captured_at` | string (ISO datetime) | Baseline snapshot timestamp |

## Entity 8: ProcessBlueprint

Proposed AI-native redesign for a baseline process.

| Field | Type | Description |
|-------|------|-------------|
| `blueprint_id` | string | Stable blueprint identifier |
| `process_id` | string | Source baseline process |
| `human_roles` | RoleAllocation[] | Human responsibilities by stage |
| `agent_roles` | RoleAllocation[] | Agent responsibilities by stage |
| `governance_checkpoints` | Checkpoint[] | Required review/approval points |
| `risk_assumptions` | string[] | Known risk assumptions |
| `expected_kpi_delta` | KpiDelta | Predicted impact vs baseline |
| `status` | enum | `draft` \| `review` \| `approved` \| `archived` |

## Entity 9: ImplementationMilestone

Tracks rollout execution for a blueprint.

| Field | Type | Description |
|-------|------|-------------|
| `milestone_id` | string | Stable milestone id |
| `blueprint_id` | string | Parent blueprint |
| `name` | string | Milestone label |
| `owner` | string | Accountable owner |
| `depends_on` | string[] | Upstream milestone ids |
| `gate` | string | Required readiness gate |
| `rollback_condition` | string | Condition to rollback |
| `status` | enum | `not_started` \| `in_progress` \| `blocked` \| `done` |
| `blocked_reason` | string \| null | Optional blocker context |

## Entity 10: KpiSnapshot

Time-windowed measurement for baseline and post-change comparisons.

| Field | Type | Description |
|-------|------|-------------|
| `snapshot_id` | string | Stable snapshot id |
| `process_id` | string | Process being measured |
| `window_type` | enum | `baseline` \| `post_change` |
| `window_start` | string (ISO datetime) | Measurement window start |
| `window_end` | string (ISO datetime) | Measurement window end |
| `cycle_time_ms_p50` | number | Median cycle time |
| `decision_latency_ms_p50` | number | Median approval/decision latency |
| `override_rate` | number | Human override frequency |
| `error_rate` | number | Failure/error frequency |
| `cost_per_outcome` | number | Cost normalized per completed outcome |
