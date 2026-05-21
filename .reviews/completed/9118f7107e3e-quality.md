# Code Quality Review: 9118f7107e3e (Phase 2 Foundational)
**Verdict**: PASS WITH NOTES
**Reviewer**: code-reviewer agent
**Date**: 2026-05-19

## Summary

No type safety violations — `any` is not used. The transform boundary is enforced (API shapes
never reach view code). Zustand with immer is used correctly. GSAP and Framer Motion do not
animate the same nodes (GSAP is installed but not yet used). Two issues warrant attention:
hardcoded oklch() literals in design-system primitives technically violate FR-025 (colors should
route through CSS custom properties), and `window.location.href` redirect in ProtectedRoute
breaks SPA routing. The dead `App` default export is a minor confusion risk.

## Findings

### Important

**QC-P2-001 — FR-025 violation: hardcoded oklch() literals in design-system primitives**

FR-025 requires all colors to derive from the token set. Multiple design-system files use
hardcoded oklch() values in Tailwind class strings rather than the CSS custom properties in
tokens.css:

- `web/src/design-system/primitives/StateCTA.tsx` — `text-[oklch(50%_0_0)]`
- `web/src/design-system/primitives/OverlayPanel.tsx` — `text-[oklch(50%_0_0)]`,
  `hover:text-[oklch(20%_0_0)]`
- `web/src/design-system/primitives/FilterBar.tsx` — `text-[oklch(50%_0_0)]`,
  `text-[oklch(40%_0_0)]`
- `web/src/design-system/primitives/NodeTooltip.tsx` — `text-[oklch(20%_0_0)]`,
  `text-[oklch(45%_0_0)]`
- `web/src/design-system/globals.css` — `oklch(99% 0 0)`, `oklch(20% 0 0)` in base styles
- `Button.tsx`, `StateCTA.tsx`, `FilterBar.tsx`, `router.tsx` — Tailwind semantic colors
  (blue-600/700/800) not in project token set

Fix before T073: Add neutral text tokens to tokens.css (`--color-text-primary: oklch(20% 0 0)`,
`--color-text-secondary: oklch(50% 0 0)`, `--color-interactive: oklch(50% 0.15 250)`) and
reference via `text-[var(--color-text-secondary)]`, `bg-[var(--color-interactive)]`.

**QC-P2-002 — `window.location.href` redirect breaks SPA routing**

`web/src/App.tsx` uses `window.location.href = '/sign-in'` for unauthenticated redirect,
triggering a full page reload and discarding React Router + TanStack Query state. In a SPA,
`<Navigate to="/sign-in" replace />` should be used instead.

The same pattern in `web/src/lib/api/client.ts` (401 interceptor) is additionally risky
because it fires for any 401 before TanStack Query's retry logic runs, and executes outside
the React tree where `useNavigate()` is unavailable.

Fix: Replace `window.location.href = '/sign-in'` in ProtectedRoute with
`return <Navigate to="/sign-in" replace />`. Remove the 401 redirect from the API interceptor.

### Notes (non-blocking)

**`App` default export is dead code**

`web/src/App.tsx` exports a default `App` component that wraps `RadixTooltip.Provider` and
`ProtectedRoute`. This component is never rendered — `main.tsx` uses `RouterProvider` directly.
The `RadixTooltip.Provider` is therefore never mounted. (NodeTooltip sets `delayDuration` on
its own `RadixTooltip.Root` so tooltips still work, but the provider context is absent.)

Fix: Remove the `App` default export, or mount it inside `ClerkProvider` in `main.tsx` to
actually provide the `RadixTooltip.Provider` context. The latter is preferable.

**`setViewStates` partial typing creates an API footgun**

The store action is typed `(states: Partial<ViewStateContext>) => void` but the only caller
passes the full object. A caller passing only `{ galaxy: ... }` would silently leave `topology`
and `decisionGraph` stale via `Object.assign`. Not a bug at current call sites; worth tightening
the signature when additional callers are added.

## TypeScript Correctness

- No `any` types anywhere in the codebase.
- `exactOptionalPropertyTypes: true` and `noUncheckedIndexedAccess: true` enabled. All nullable
  fields correctly use `string | null` not `string?`. Correct.
- Zustand immer mutations use assignment only — no array push or direct object mutation on
  non-drafted values. Correct.

## Transform Boundary

All API response shapes (`ApiNode`, `ApiEdge`, `ApiWorkflow*`, `ApiDecision*`, `ApiViewState`)
are defined in `web/src/types/api.ts` and are never imported by view components. View components
use only camelCase view model types. Transform functions are the only code importing API types.
Boundary is enforced. ✓

## GSAP / Framer Motion Coexistence

GSAP is installed but not used in this commit. Framer Motion owns all animations: OverlayPanel
slide-in, StateCTA entrance, FilterBar chip hover/tap. No DOM node is animated by both
libraries. Constraint satisfied for this commit. ✓
