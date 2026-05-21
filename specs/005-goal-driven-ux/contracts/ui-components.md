# UI Component Contracts: Phase 5 — Goal-Driven UX & In-Context Guidance

**Created**: 2026-05-21

---

## Contract 1: `FirstVisitCallout`

**File**: `web/src/design-system/primitives/FirstVisitCallout.tsx`  
**Status**: Create new

### Props Interface

```typescript
interface FirstVisitCalloutProps {
  storageKey: string;
  title: string;
  description: string;
  dismissLabel?: string;       // default: "Got it"
  position?: 'bottom-left' | 'bottom-center'; // default: 'bottom-left'
}
```

### Behaviour Contract

| Condition | Expected Behaviour |
|-----------|-------------------|
| `localStorage.getItem(storageKey) === "true"` | Component returns `null` — not rendered |
| `localStorage.getItem(storageKey) === null` | Component renders callout card |
| User clicks dismiss button | Sets `localStorage.setItem(storageKey, "true")`; triggers exit animation; unmounts |
| User presses `Escape` while callout is visible | Same as dismiss button |
| Component mounts | Reads localStorage synchronously; sets dismissed state before first paint |

### Visual Contract

| Property | Value |
|----------|-------|
| Width | 280px fixed |
| Background | white (`oklch(100% 0 0)`) |
| Border | `1px solid oklch(90% 0 0)` |
| Box shadow | `var(--shadow-panel)` |
| Border radius | `12px` |
| z-index | `30` |
| Position (bottom-left) | `fixed; bottom: 24px; left: calc(56px + 24px)` |
| Position (bottom-center) | Inside content flow, centered |
| Enter animation | Framer Motion: `opacity 0→1`, `y 8→0`, duration `150ms`, ease `--motion-easing-everyday` |
| Exit animation | Framer Motion: `opacity 1→0`, `y 0→8`, duration `100ms` |

### Accessibility Contract

| Requirement | Implementation |
|-------------|---------------|
| Dismiss button label | `aria-label="Dismiss orientation message"` |
| Keyboard dismiss | `onKeyDown` on document — `Escape` triggers dismiss |
| Focus management | Dismiss button is not auto-focused; user can tab to it |
| Role | No special role; treated as supplementary landmark content |

### Usage Example

```tsx
<FirstVisitCallout
  storageKey="ctx_os_visited_galaxy"
  title="Your Initiative Galaxy"
  description="Each node is an initiative — a coordinated effort. Click any node to open its detail. Use the overlay controls (top-right) to colour the galaxy by Load, Risk, Autonomy, or Ownership."
/>
```

---

## Contract 2: `HintTooltip`

**File**: `web/src/design-system/primitives/HintTooltip.tsx`  
**Status**: Create new  
**Dependency**: `web/src/design-system/components/Tooltip.tsx` (wrap, not duplicate)

### Props Interface

```typescript
interface HintTooltipProps {
  content: string;
  side?: 'top' | 'right' | 'bottom' | 'left'; // default: 'top'
}
```

### Behaviour Contract

| Condition | Expected Behaviour |
|-----------|-------------------|
| User hovers `?` icon | Tooltip opens after `300ms` delay |
| User moves mouse away | Tooltip closes |
| Click | No click behaviour — hover only |
| `content` is empty string | Component renders nothing (`null`) |

### Visual Contract

| Property | Value |
|----------|-------|
| Icon shape | Circle, 12px diameter |
| Icon color | `oklch(65% 0 0)` |
| Icon background | Transparent |
| Display | `inline-flex`, `align-middle` |
| Margin left | `4px` (`ml-1`) |
| Cursor | `help` |
| Tooltip max-width | Inherits from `Tooltip` — `max-w-xs` (320px) |

### Accessibility Contract

| Requirement | Implementation |
|-------------|---------------|
| Trigger element | `<button type="button">` (not `<span>`) |
| ARIA label | `aria-label="More information"` |
| Keyboard access | Focusable; tooltip opens on focus (Radix default) |
| Icon aria-hidden | `aria-hidden="true"` on the `?` SVG |

### Usage Example

```tsx
<span>Briefing Draft <HintTooltip content="A weekly synthesis drafted by the Operational Synthesizer agent." /></span>
```

---

## Contract 3: `GalaxyLegend`

**File**: `web/src/views/galaxy/GalaxyLegend.tsx`  
**Status**: Create new

### Props Interface

```typescript
interface GalaxyLegendProps {
  // No props — reads CSS tokens from document.documentElement
}
```

### Behaviour Contract

| Condition | Expected Behaviour |
|-----------|-------------------|
| Mount | Reads `localStorage.getItem("ctx_os_legend_galaxy")`; renders collapsed if `null` |
| User clicks pill button | Toggles expanded/collapsed; writes to localStorage |
| CSS tokens not present | Falls back to neutral grey (`oklch(60% 0 0)`) |

### Visual Contract — Collapsed State

| Property | Value |
|----------|-------|
| Appearance | Pill button: `◈ Legend` text |
| Position | `fixed; bottom: 24px; right: 24px; z-index: 20` |
| Background | `oklch(12% 0 0 / 0.85)` with `backdropFilter: blur(12px)` |
| Border | `1px solid oklch(100% 0 0 / 0.08)` |
| Text color | `oklch(70% 0 0)` |
| Font size | `12px`, `font-weight: 500` |

### Visual Contract — Expanded State

| Property | Value |
|----------|-------|
| Width | `160px` |
| Background | Same as collapsed pill |
| Sections | "Node types" (4 rows) and "Status" (4 rows) |
| Color swatch | 10px circle, inline before label |
| Swatch source | `getComputedStyle(document.documentElement).getPropertyValue(tokenName)` |
| Label color | `oklch(70% 0 0)` |
| Font size | `11px` |
| Row height | `20px` |

### Accessibility Contract

| Requirement | Implementation |
|-------------|---------------|
| Toggle button label | `aria-label="Toggle legend"` |
| Expanded/collapsed | `aria-expanded` on toggle button |
| Decorative swatches | `aria-hidden="true"` |

---

## Contract 4: `AppShell`

**File**: `web/src/components/AppShell.tsx`  
**Status**: Create new  
**Router integration**: Parent layout route in `router.tsx` using `<Outlet />`

### Props Interface

```typescript
interface AppShellProps {
  children: ReactNode;
}
```

### Behaviour Contract

| Condition | Expected Behaviour |
|-----------|-------------------|
| Active route matches nav item | Nav icon shows active state (white, scale 1.0) |
| Active route is `/inbox` | Inbox badge not shown |
| Inbox pending count > 0 and route ≠ `/inbox` | Red badge shown on Inbox icon |
| Inbox count > 9 | Badge shows "9+" |
| Inbox fetch error | Badge not shown (no error state exposed) |
| User clicks `?` help link | Opens `#` (placeholder) in new tab; tooltip "Docs coming soon" |

### Visual Contract

| Property | Value |
|----------|-------|
| Width | `56px` fixed |
| Height | `100vh` |
| Position | `fixed left-0 top-0 bottom-0` |
| z-index | `40` |
| Background | `oklch(10% 0 0)` |
| Border right | `1px solid oklch(100% 0 0 / 0.08)` |
| Nav icons | 4 items: Galaxy, Topology, Decisions, Inbox |
| Icon size | 20px × 20px |
| Active icon color | `oklch(95% 0 0)` |
| Inactive icon color | `oklch(50% 0 0)` |
| Help link position | Pinned to sidebar bottom, 12px from bottom edge |
| Badge size | 16px × 16px circle |
| Badge color | `oklch(60% 0.22 25)` (red) |
| Badge position | Absolute top-right of Inbox icon, -4px offset |
| Content area | `margin-left: 56px; height: 100vh` |

### Accessibility Contract

| Requirement | Implementation |
|-------------|---------------|
| Nav landmark | `<nav aria-label="Main navigation">` |
| Active page | `aria-current="page"` on active NavLink |
| Badge | `aria-label="N pending approvals"` on badge element |
| Help link | `aria-label="Documentation and help"` |
| Icon buttons | `title` attribute matching route name |

### Nav Items

| Icon | Route | Tooltip |
|------|-------|---------|
| Galaxy SVG | `/galaxy` | "Galaxy" |
| Topology SVG | `/topology` | "Topology" |
| Decisions SVG | `/decisions` | "Decisions" |
| Inbox SVG | `/inbox` | "Inbox" |

---

## Contract 5: Modified `OverlayControls`

**File**: `web/src/views/galaxy/OverlayControls.tsx`  
**Status**: Modify existing

### Change: Wrap each button in `Tooltip`

Each `div` wrapping a `motion.button` + label `<span>` is wrapped in
`<Tooltip content="..." side="right">`. The `div` becomes the tooltip trigger
(`asChild` not needed — `Tooltip` wraps children).

| Overlay | Tooltip Content |
|---------|----------------|
| Load | "Workload overlay — darker nodes carry more active work. Identify overloaded teams." |
| Risk | "Risk overlay — red = flagged at-risk, amber = moderate risk." |
| Autonomy | "Autonomy overlay — shows AI autonomy level per initiative (0–5 scale)." |
| Ownership | "Ownership overlay — colours initiatives by owning team. Spot ownership gaps." |

**Tooltip `side`**: `"right"` (appears to the right of the control panel).  
**No other behaviour changes**.
