# Spec Review — 2bcbbfdb3133

## Changes Reviewed

### web/src/views/galaxy/GalaxyActivating.tsx
- Removes `color-mix(in oklch, ...)` — Sigma v3 WebGL cannot parse CSS color functions
- Adds `resolveCSSVar()` using 1×1 canvas pattern (same as GalaxyView) returning `rgba(r,g,b,0.5)`
- Real activating nodes now render at 50% opacity via rgba alpha instead of color-mix

### web/src/inbox/InboxView.tsx
- Adds `useRef<ReturnType<typeof setInterval>>` to store poll handle
- Adds `useEffect(() => () => clearInterval(pollRef.current), [])` for unmount cleanup
- Fixes `exactOptionalPropertyTypes` error: `return prev ? { prev } : {}` instead of `return { prev }`

## Spec Compliance
- Color-mix fix: activating nodes now visible in WebGL with correct node-type color at half opacity
- Interval cleanup: navigating away during briefing generation no longer leaks the interval
- TypeScript strict mode: typecheck passes with zero errors

## Verdict: PASS
