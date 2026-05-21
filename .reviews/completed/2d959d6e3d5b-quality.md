# Quality Review — 2d959d6e3d5b

**Commit**: feat(phase5): UI clarity & in-context guidance — first-visit callouts, overlays, inbox hints  
**Overall**: PASS WITH NOTES

## Findings

### Q-1 — GalaxyLegend async localStorage initialization
**File**: `web/src/views/galaxy/GalaxyLegend.tsx:53–55`  
**Confidence**: 90  
`expanded` state is `useState(false)` followed by `useEffect` to read localStorage. This causes a flash-of-collapsed on first render for users who had previously expanded the legend. The fix applied to `FirstVisitCallout` (sync lazy init: `useState(() => localStorage.getItem(key) === 'expanded')`) was not applied here. Pattern inconsistency with the sibling component.

**Fix**: `const [expanded, setExpanded] = useState(() => localStorage.getItem(STORAGE_KEY) === 'expanded');` — remove the `useEffect`.

### Q-2 — GalaxyLegend pill button hidden via inline style, not DOM removal
**File**: `web/src/views/galaxy/GalaxyLegend.tsx:68–75`  
**Confidence**: 75  
When expanded, the pill button's `style.display` is set to `'none'` but it remains in the DOM with `aria-expanded={true}`. The collapse button inside the panel lacks `aria-expanded`. Not a blocking bug — screen reader impact is mild (hidden button is not focusable), but the ARIA contract is inconsistent. Consider using `AnimatePresence` on the pill or simply not rendering it when expanded.

### Q-3 — Dead `Protected` helper in router.tsx
**File**: `web/src/router.tsx:27`  
**Confidence**: 85  
Function defined but never called (all routes now use `ProtectedRoute` from App.tsx). Commit message incorrectly states it was removed. Should be deleted to avoid confusion.

### Q-4 — `getCSSToken` called at render time on every ColorRow
**File**: `web/src/views/galaxy/GalaxyLegend.tsx:24–27`  
**Confidence**: 65  
`getComputedStyle(document.documentElement).getPropertyValue(token)` runs synchronously at render time for each of 8 entries. CSS custom properties are stable — the value never changes. Negligible cost on ≤8 entries; no action needed for MVP.

## Verdict: PASS WITH NOTES

Q-1 (async init flash) and Q-3 (dead code) are the only meaningful issues. Both are low-severity and non-blocking. Q-1 fix is a one-liner if desired.
