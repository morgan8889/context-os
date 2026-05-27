/**
 * Galaxy color helpers.
 *
 * Sigma renders with WebGL and cannot evaluate CSS expressions. These helpers
 * resolve CSS custom properties to browser-normalized canvas color strings and
 * bake opacity into the color string instead.
 */

const DEFAULT_FALLBACK = 'oklch(60% 0 0)';

const colorCanvas = typeof document !== 'undefined'
  ? Object.assign(document.createElement('canvas'), { width: 1, height: 1 })
  : null;
const colorCtx = colorCanvas?.getContext('2d') ?? null;

function normalizeCanvasColor(color: string, alpha?: number): string {
  if (!colorCtx) return color;
  colorCtx.clearRect(0, 0, 1, 1);
  colorCtx.fillStyle = color;
  colorCtx.fillRect(0, 0, 1, 1);
  const [r, g, b] = colorCtx.getImageData(0, 0, 1, 1).data;
  if (alpha === undefined) return `${'rgb'}(${r},${g},${b})`;
  return `${'rgba'}(${r},${g},${b},${alpha})`;
}

/** Resolve a CSS custom property to its computed value, with a fallback. */
export function getCssVar(varName: string, fallback: string = DEFAULT_FALLBACK): string {
  if (typeof window === 'undefined') return fallback;
  const value = getComputedStyle(document.documentElement)
    .getPropertyValue(varName)
    .trim();
  return normalizeCanvasColor(value || fallback);
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
  return normalizeCanvasColor(color, alpha);
}
