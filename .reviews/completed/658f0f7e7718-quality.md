# Quality Review — 658f0f7 (fix(web): memoize galaxy graph + resolve Sigma WebGL colors)

**Branch**: 3-cognition-surface
**Reviewer**: feature-dev:code-reviewer (agent a4cac428)
**Verdict**: approve-with-nits

Both fixes are mechanically correct; the regression tests genuinely cover the
described bugs. No critical or important issues. Three nits, none blocking.

## Correctness — confirmed
- **useMemo keys**: `nodesData`/`edgesData` (lines 126-127) are the same refs as
  `nodesQuery.data`/`edgesQuery.data`; deps `[nodesData, edgesData]` trigger only
  on real data change. Sound.
- **Rules of Hooks**: hook sequence is unconditional before the line-143 return.
- **`withAlpha` regex** `/^oklch\(([^)/]+)\)$/`: parses `oklch(L C H)` forms,
  rejects already-alpha'd inputs (`/` excluded) → idempotent. Correct.
- **Reference-stability test** (`galaxy.test.ts`): records graph, `rerender()`
  with stable mocked data, asserts `toBe` — directly covers the SC-002 regression.
- **Color-resolution tests**: assert no `var(`/`color-mix(` from `resolveNodeColor`
  across all four types; cover the WebGL black-render regression.

## Nits
- **NIT-Q-1 (confidence 80):** `benchmarkNodes` IIFE (`useGalaxyGraph.ts:52-58`)
  rebuilds `URLSearchParams` every render. Value is session-stable so memo
  stability holds, but wrapping in `useMemo([], [])` would be cleaner.
- **NIT-Q-2 (confidence 80):** `ActivatingGraphLoader` effect dep `[nodes.length]`
  with a bare `eslint-disable` (`GalaxyActivating.tsx:70`) won't rebuild if node
  content changes at the same count. Unlikely in the single-snapshot activating
  state, but prefer `[nodes]` or add a rationale comment.
- **NIT-Q-3 (confidence 80):** `withAlpha` idempotency on an already-alpha'd
  oklch color is correct but untested — add a case to lock it against future
  regex changes.

## Minor
- `getCssVar` fallback is `oklch(60% 0 0)` (generic grey), not a per-token
  fallback; acceptable given the SSR guard and that real browsers load tokens.css.
