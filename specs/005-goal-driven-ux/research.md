# Phase 5 Research: Goal-Driven UX & In-Context Guidance

**Created**: 2026-05-21  
**Status**: Complete

---

## Decision 1: localStorage vs. backend persistence for orientation dismissal

**Decision**: localStorage per-browser, per-view key.  
**Rationale**: Backend persistence (user preference API) would require a new
endpoint, a new DB column, and a round-trip on every view load. The only failure
mode of localStorage is cross-device inconsistency (user dismisses on laptop,
sees callout again on desktop) — acceptable at beta scale where users have a
single primary device. The value of the callout diminishes rapidly after first
exposure; seeing it twice on a second device is a minor inconvenience, not a
data loss.  
**Alternatives considered**: User preferences API (rejected — premature backend
complexity for a UI teaching surface); session storage only (rejected — doesn't
persist across browser restarts, defeating the purpose).  
**Key schema**: `ctx_os_visited_<view>` where `<view>` ∈ `{galaxy, topology,
decisions, inbox}`. Boolean string `"true"`. Legend state: `ctx_os_legend_galaxy`.

---

## Decision 2: FirstVisitCallout as self-contained primitive vs. global state

**Decision**: Self-contained component with `useState` + `useEffect` reading
localStorage on mount. No Zustand store, no context provider.  
**Rationale**: The callout's only responsibility is "has this view been visited
before?" This is read once on mount and never needs to be coordinated with
other components. A self-contained implementation avoids coupling to the
global interaction store (`graphInteraction.ts`) and is trivially testable.  
**Alternatives considered**: Zustand slice (rejected — unnecessary coordination
surface; store already covers interaction state, not UI teaching); React context
(rejected — provider indirection with no benefit at this scope).

---

## Decision 3: HintTooltip icon — dedicated component vs. inline pattern

**Decision**: Dedicated `HintTooltip` primitive wrapping the existing `Tooltip`
component from `web/src/design-system/components/Tooltip.tsx`.  
**Rationale**: The `?` icon + tooltip pattern appears in ≥5 locations (Inbox
type badges, failure flag header, overlay button labels, potentially more).
Extracting to a primitive ensures consistent sizing (12px circle), consistent
delay (300ms), consistent `aria-label`, and a single update point.  
**Existing Tooltip API**: `{ children, content, side?, delayDuration? }`. The
Radix `TooltipProvider` is already mounted at the `App` root — no additional
provider required.  
**Alternatives considered**: Inline Radix usage at each callsite (rejected —
would duplicate `aria-label` and sizing logic across callsites).

---

## Decision 4: GalaxyLegend positioning and collision avoidance

**Decision**: Fixed bottom-right, z-20. The legend collapses to a pill by
default and expands on click. `FirstVisitCallout` is bottom-left (z-30), so
they do not overlap.  
**Rationale**: The overlay controls are top-right (z-10 within the canvas
container). Bottom-right is unoccupied on the Galaxy canvas and remains
visible regardless of NodeDetailPane open/close (NodeDetailPane is
bottom-right-adjacent but positioned with offset). Using `position: fixed`
within the canvas viewport ensures it doesn't scroll with content.  
**z-index hierarchy** (Galaxy canvas, high = above):
- AppShell: z-40
- FirstVisitCallout: z-30
- Callout overlay backgrounds: z-20
- GalaxyLegend: z-20
- NodeDetailPane: z-10
- OverlayControls: z-10

---

## Decision 5: AppShell navigation — new component wrapping the router

**Decision**: Create `web/src/components/AppShell.tsx` as a layout wrapper
rendered by the router for all four main routes (Galaxy, Topology, Decisions,
Inbox). Router updated to use a layout route with `<Outlet />`.  
**Rationale**: No navigation shell currently exists in the codebase. The
router.tsx loads views directly with no shared chrome. AppShell must be built
from scratch to add: (1) the 56px left sidebar with view icons, (2) the Inbox
pending-count badge, (3) the docs help link.  
**Pattern**: React Router v6 layout route — `createBrowserRouter` with a parent
`path: "/"` element `<AppShell><Outlet /></AppShell>` and children for each
view. This means AppShell mounts once and views render inside it.  
**Inbox badge data**: `useQuery` with key `['inbox']` — same key as InboxView.
TanStack Query deduplicates the request. Badge count derived from
`data?.items?.length ?? 0`. Badge is hidden when the active route is `/inbox`.

---

## Decision 6: Empty state CTA repair — copy-only vs. routing changes

**Decision**: Copy-only fix. No new routes. Galaxy empty → `/onboarding` (exists);
Decision empty → remove broken CTA entirely.  
**Rationale**: `/settings/sources` (Galaxy empty CTA) and `/decisions/new`
(Decision empty CTA) are 404 routes that don't exist. The correct repair is:
(1) be honest about what the empty state means, (2) link to something that
actually exists. The onboarding flow (`/onboarding`) is the correct destination
for "something seems stalled" on Galaxy. Decision creation via the UI is not
built; promising it via a CTA creates a dead-end.  
**Alternatives considered**: Build the missing routes (rejected — significant
scope creep; not part of Phase 5); keep broken CTAs with a toast "coming soon"
(rejected — dishonest, training users to ignore CTAs).

---

## Decision 7: Overlay button tooltip content strategy

**Decision**: Wrap each `OverlayControls` button in the existing `Tooltip`
component. Tooltip content is a short (≤20 word) description of what the
overlay reveals and how to read it.  
**Rationale**: The `OverlayControls` component already maps over `OVERLAY_BUTTONS`
array. Each button is a `motion.button` inside a `div`. The `Tooltip` wraps the
outer `div` for each button. The existing `Tooltip` uses Radix
`TooltipProvider` already mounted at App root, so no provider changes needed.  
**Copy**: Defined in the plan — Load, Risk, Autonomy, Ownership each get a
specific one-sentence description that names what it shows and how to read the
colour gradient.

---

## Decision 8: Inbox type badge tooltip approach

**Decision**: Wrap existing type badge `<span>` in `HintTooltip` at the end
of the badge (inline `?` icon after the badge text), not the badge itself as
the trigger.  
**Rationale**: The badge already has colour/border styling that works. Replacing
the badge trigger with a tooltip would change hover behaviour for the entire
badge, which is not desirable (badges may have their own future click behaviour).
A trailing `?` icon makes the tooltip opt-in without disrupting the badge.  
**Failure flag tooltip**: The failure flag warning banner header gets a trailing
`HintTooltip`. The banner is already rendered per-item in `InboxView`.
