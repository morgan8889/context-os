# Code Quality Review: 303c2c7950c6 (Phase 5 Goal-Driven UX Implementation)
**Verdict**: PASS WITH ISSUES
**Date**: 2026-05-21

## Summary

Implementation is well-structured and single-responsibility. Four issues above threshold.

## Critical

### Q-1: aria-current={undefined} removes active-page screen reader signal (confidence 90)
**File**: `web/src/components/AppShell.tsx`
**Problem**: React Router's NavLink sets `aria-current="page"` automatically when active.
Passing `aria-current={undefined}` explicitly removes this. Screen readers cannot identify
the current page.
**Fix**: Remove `aria-current={undefined}` from the NavLink.

## Important

### Q-2: OverlayControls Tooltip wraps non-focusable div; keyboard users can't open tooltips (confidence 88)
**File**: `web/src/views/galaxy/OverlayControls.tsx`
**Problem**: `<Tooltip>` wraps the outer `<div>` which is not keyboard-focusable. Radix
Tooltip.Trigger uses the immediate child as the trigger element via `asChild`. The actual
interactive `<motion.button>` is a child of that div, so keyboard focus on the button does
not trigger the tooltip.
**Fix**: Move `<Tooltip>` to wrap the `<motion.button>` directly, keeping the label `<span>` outside.

### Q-3: FirstVisitCallout async localStorage read causes unnecessary render cycle (confidence 85)
**File**: `web/src/design-system/primitives/FirstVisitCallout.tsx`
**Problem**: `useState(false)` + `useEffect` reads localStorage after mount. Dismissed users
trigger a mount → read → unmount cycle. First-time users see the callout one frame late.
**Fix**: `useState(() => localStorage.getItem(storageKey) !== 'true')` + remove first useEffect.

### Q-4: Dead `Protected` helper in router.tsx (confidence 80)
**File**: `web/src/router.tsx`
**Problem**: `Protected` wrapper is defined but no child route uses it. Creates confusion
about individual route auth.
**Fix**: Use `Protected` in all child routes (removes per-route `<Suspense>` duplication)
or remove it.

## Minor

### Q-5: Empty `<li>` persists after inbox-hint callout is dismissed (confidence 80)
**File**: `web/src/inbox/InboxView.tsx`
**Problem**: `<li class="list-none">` wrapping `ctx_os_inbox_hint` stays in the DOM after
FirstVisitCallout returns null. This places an empty list item in `<ul aria-label="Pending
approval items">`.
**Fix**: Move the callout outside the `<ul>`, or conditionally render the `<li>`.

## No Issues Found In
GalaxyLegend (CSS token reads, toggle, persistence, aria), HintTooltip (wrapping, guard,
ARIA), AppShell badge logic (isInbox guard, null safety, refetch interval), GalaxyEmpty
and DecisionEmpty (copy, CTA), animation GSAP/Framer partition.
