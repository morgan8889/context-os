# Quickstart & Integration Scenarios: Phase 5

**Created**: 2026-05-21

---

## Setup

```bash
cd web
npm run dev    # Vite dev server :5173

# Auth bypass for local testing
VITE_DEV_BYPASS_AUTH=true npm run dev
```

---

## Scenario 1: First-visit callout appears on first navigation

**Precondition**: localStorage cleared for this origin.

```javascript
// In browser DevTools console:
localStorage.clear();
```

1. Navigate to `/galaxy` — callout appears bottom-left:  
   > "Your Initiative Galaxy — Each node is an initiative — a coordinated effort..."
2. Click "Got it" — callout fades out.
3. Refresh page — callout does NOT reappear.
4. Run the same sequence for `/topology`, `/decisions`, `/inbox`.

**Verification**:
```javascript
// After dismiss:
localStorage.getItem('ctx_os_visited_galaxy') // → "true"
```

---

## Scenario 2: Galaxy overlay tooltips

1. Navigate to `/galaxy` (activated state with seed data).
2. Hover over the "Load" button in the top-right overlay control panel.
3. Tooltip appears to the right after 500ms:  
   > "Workload overlay — darker nodes carry more active work. Identify overloaded teams."
4. Hover each of Risk, Autonomy, Ownership — each shows its distinct tooltip.

---

## Scenario 3: Galaxy legend expand/collapse

1. Navigate to `/galaxy` (activated state).
2. Bottom-right: pill button "◈ Legend" is visible.
3. Click — legend expands with node type and status color swatches.
4. Click again — legend collapses back to pill.
5. Refresh — legend state persists (expanded stays expanded).

```javascript
// Check persistence:
localStorage.getItem('ctx_os_legend_galaxy') // → "expanded" or null
```

---

## Scenario 4: Inbox item type tooltips

1. Navigate to `/inbox` (with pending items from seed data).
2. Each card shows a type badge: "Briefing Draft", "Proposed Dependency", or "Proposed Risk".
3. A `?` icon appears inline after each badge label.
4. Hover the `?` — tooltip explains the item type.
5. For a card with failure flags, hover the `?` next to "Failure flags" header.

---

## Scenario 5: Inbox first-approval callout

1. Clear localStorage: `localStorage.removeItem('ctx_os_inbox_hint')`.
2. Navigate to `/inbox` (with ≥1 pending items).
3. Above the first card, callout appears:  
   > "This is your first approval. Read the summary, check for failure flags, then approve or reject with a reason."
4. Dismiss — callout disappears; localStorage key set.
5. Navigate away and back — callout does not reappear.

---

## Scenario 6: AppShell Inbox badge

1. Ensure backend has pending items (seed data loaded).
2. Navigate to `/galaxy`.
3. The Inbox icon in the left sidebar shows a red badge with the pending count.
4. Navigate to `/inbox` — badge disappears (cleared on Inbox route).
5. Navigate back to `/galaxy` — badge reappears.

---

## Scenario 7: Galaxy empty state — honest copy

1. Use a tenant with no initiatives (empty seed) or disconnect from backend.
2. Navigate to `/galaxy`.
3. See new heading: "Your galaxy is taking shape"
4. See body copy explaining ingest process (no broken CTA).
5. "Review onboarding" button navigates to `/onboarding`.

---

## Scenario 8: Decision empty state — no broken CTA

1. Use a tenant with no decisions.
2. Navigate to `/decisions`.
3. See new heading: "Decisions accumulate over time"
4. See body copy explaining briefing cycle.
5. No CTA button present (broken "Capture manually" removed).

---

## TypeScript validation

```bash
cd web
npm run typecheck   # tsc --noEmit, must pass with zero errors
```

---

## Visual regression

Run after all changes committed:
```bash
# From project root
/verify-visual
# or
/verify-brand
```

---

## Strategic extension scenarios (spec target)

These scenarios define acceptance intent for the AI process transformation
objective. They are expected for follow-on phases and may not be fully
implemented in current Phase 5 builds.

## Scenario 9: Process baseline capture

1. Select an existing business workflow.
2. System produces a baseline map with stages, owners, handoffs, cycle-time,
   and rework/failure hotspots.
3. Operator can export or pin this baseline as the comparison anchor.

## Scenario 10: AI-native process redesign proposal

1. Start from a baseline process.
2. System proposes a redesign with:
   - human responsibilities
   - agent responsibilities
   - governance checkpoints
   - expected KPI deltas
3. Operator reviews and approves/rejects proposal.

## Scenario 11: Implementation control plan

1. Approve a redesign blueprint.
2. System generates milestones with owners, dependencies, readiness gates,
   and rollback conditions.
3. Blockers are surfaced with explicit root-cause status.

## Scenario 12: KPI before/after measurement

1. Baseline KPI window is locked before rollout.
2. Post-change KPI window is collected after rollout activation.
3. Dashboard shows deltas for cycle time, latency, rework, override rate,
   and cost per outcome with audit trail.

## Scenario 13: Drift and optimisation loop

1. Monitor transformed process for sustained KPI drift.
2. System generates targeted optimisation recommendations.
3. Operator accepts/rejects recommendations and tracks resulting KPI change.
