/**
 * Galaxy color helpers.
 *
 * Sigma renders with WebGL and cannot evaluate CSS expressions — passing a
 * `var(--x)` or `color-mix(...)` string as a node color silently renders the
 * node black. These helpers resolve CSS custom properties to concrete computed
 * values and bake opacity into the color string instead.
 */

const DEFAULT_FALLBACK = 'oklch(60% 0 0)';

/** Resolve a CSS custom property to its computed value, with a fallback. */
export function getCssVar(varName: string, fallback: string = DEFAULT_FALLBACK): string {
  if (typeof window === 'undefined') return fallback;
  const value = getComputedStyle(document.documentElement)
    .getPropertyValue(varName)
    .trim();
  return value || fallback;
}

/** Resolve a node domain type to a concrete, Sigma-safe base color. */
export function resolveNodeColor(type: string): string {
  return getCssVar(`--color-node-${type}`);
}

/**
 * Bake an alpha into an `oklch(...)` color so Sigma's WebGL program renders it
 * with the intended opacity (Sigma's default node program has no separate
 * per-node opacity channel). Non-oklch colors are returned unchanged.
 */
export function withAlpha(color: string, alpha: number): string {
  const match = color.match(/^oklch\(([^)/]+)\)$/);
  if (!match) return color;
  return `oklch(${match[1]!.trim()} / ${alpha})`;
}
