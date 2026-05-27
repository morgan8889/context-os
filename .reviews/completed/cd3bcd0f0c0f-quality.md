# Code Quality Review — cd3bcd0f0c0f

**Commit**: fix(topology): replace React Flow ghost canvas with SVG placeholder in empty state
**Scope**: web/src/views/topology/TopologyEmpty.tsx only

---

## [CRITICAL]

None.

---

## [WARN]

### W-1: SVG node positions are hardcoded; overflow at narrow viewports
The SVG has a fixed viewBox="0 0 640 400" and width="640". On screens narrower than
~700px (640px SVG + some parent padding), the SVG will overflow horizontally even though
the surrounding div uses `overflow: hidden`. The `overflow: hidden` on the parent clips
the overflow visually but the layout still allocates space, potentially causing a
horizontal scrollbar in the body. The SVG should use `width="100%"` with `viewBox`
preserved, and `maxWidth: 640` on the container, so it scales down on small screens.

File: `web/src/views/topology/TopologyEmpty.tsx`, lines 47–100

### W-2: --color-placeholder-grey CSS variable used in SVG but not guaranteed present
The SVG uses `var(--color-placeholder-grey)` for stroke and fill. Per CLAUDE.md this
token is defined in `web/src/design-system/tokens.css`. If TopologyEmpty is rendered
before that stylesheet loads (e.g. in a test environment or with a CSS-in-JS reset that
strips vars), all SVG paths render transparent. The prior React Flow canvas used Tailwind
classes which have the same risk, so this is not a regression, but it is worth noting.

---

## [INFO]

### I-1: Dead imports fully removed
All React Flow imports (`ReactFlow`, `ReactFlowProvider`, `Node`, `NodeTypes`),
`WorkflowNode`, and `WorkflowNodeData` are removed. Bundle weight for this route drops
by roughly the size of @xyflow/react in the empty-state code path. No unused imports
remain.

### I-2: aria-hidden on decorative SVG is correct
`aria-hidden="true"` on the placeholder div is the correct accessibility pattern for
decorative illustrations. The meaningful content is the text paragraph and the CTA
button, both of which remain accessible.

### I-3: CTA card background uses hardcoded oklch literal instead of CSS token
`background: 'oklch(12% 0.005 250 / 0.95)'` (line 68) is not a design token. The
adjacent OnboardingView uses the same `oklch(12% 0 0)` pattern. Minor inconsistency;
should use a card-background token if one exists in tokens.css, otherwise define one.

## Recommendation: APPROVE (with W-1 follow-up)

The fix cleanly resolves the reported viewport/z-index regression. W-1 (SVG overflow on
narrow screens) should be addressed in a follow-up; the rest are informational.
