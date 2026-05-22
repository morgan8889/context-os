# Code Quality Review — 7bb129caede7

**Commit**: fix(phase5): pgvector codec crash, Clerk JWT hang, ForceAtlas2 settings, Sigma headless, dark canvas backgrounds
**Branch**: 5-goal-driven-ux
**Overall**: Two important issues; no security or data-safety problems

---

## Critical

None.

---

## Important

### Issue 1: Dead `Protected` wrapper component in router.tsx — confidence 88

`router.tsx` lines 19–25 define a `Protected` component that is never used anywhere in
the file. The four child routes use `<Suspense>` directly; auth is handled by the parent
layout route's `<ProtectedRoute>`. This is unreachable dead code that adds confusion about
the routing auth model.

File: `web/src/router.tsx`, lines 19–25

Fix: Remove `Protected` and the unused `ReactNode` import.

---

### Issue 2: `FirstVisitCallout` bottom-center position renders left-aligned — confidence 85

`FirstVisitCallout.tsx` line 40 maps `position='bottom-center'` to
`{ position: 'relative', zIndex: 30 }`. There is no centering style. When rendered
inside a flex-column container (InboxView's scrollable content area), the 280px card
floats to the left edge.

The `ctx_os_inbox_hint` callout at `InboxView.tsx` line 536 uses `position="bottom-center"`
and will appear left-aligned instead of centered above the approval list.

File: `web/src/design-system/primitives/FirstVisitCallout.tsx` line 37–40
File: `web/src/inbox/InboxView.tsx` line 536

Fix: add `marginLeft: 'auto'` and `marginRight: 'auto'` to the bottom-center style:

```tsx
const positionStyle: CSSProperties =
  position === 'bottom-left'
    ? { position: 'fixed', bottom: 24, left: 'calc(56px + 24px)', zIndex: 30 }
    : { position: 'relative', zIndex: 30, marginLeft: 'auto', marginRight: 'auto' };
```

---

### Issue 3: `register_pgvector_codec` in vector/client.py is unreachable dead code — confidence 85

`engine.py` was changed to rely on `pgvector.sqlalchemy.Vector` ORM-level type handling,
removing asyncpg codec registration from `init_db()`. The `register_pgvector_codec`
function at `src/context_os/vector/client.py` lines 16–49 is no longer called anywhere
in the codebase.

The function body also contains `asyncio.ensure_future(_register(dbapi_conn))` inside a
sync SQLAlchemy `connect` event handler — scheduling a coroutine with no completion
guarantee before first connection use. This design flaw is moot since the function is
unreachable, but leaving it in place is misleading to future readers.

File: `src/context_os/vector/client.py` lines 16–49

Fix: Remove `register_pgvector_codec` entirely. Retain `VectorSessionHelper`.

---

## Below Threshold

- `GalaxyLegend.tsx` lines 80–82: Collapsed state uses `display: none` instead of
  `AnimatePresence`, so collapse has no exit animation while expand does. Visual
  inconsistency, not a bug. (confidence 60)

- `InboxView.tsx` line 510: `ctx_os_visited_inbox` `FirstVisitCallout` renders before
  the `isLoading` guard — first-time users on slow APIs see callout before skeleton cards
  appear. Minor ordering issue. (confidence 55)
