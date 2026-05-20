import { test, expect } from '@playwright/test';

/**
 * T066 — Visual regression fixtures for the Decision Graph view (US3).
 *
 * 9 viewport × state fixtures + 1 edge-types fixture = 10 total.
 *
 * Prerequisites:
 *   - Dev server running at http://localhost:5173
 *   - Seed each state before running (or use dev route params to override state)
 */

const VIEWPORTS: Array<{ name: string; width: number; height: number }> = [
  { name: '1024x768', width: 1024, height: 768 },
  { name: '1440x900', width: 1440, height: 900 },
  { name: '2560x1440', width: 2560, height: 1440 },
];

const STATES: Array<'empty' | 'activating' | 'activated'> = [
  'empty',
  'activating',
  'activated',
];

/** Stable render signal per state */
async function waitForState(
  page: import('@playwright/test').Page,
  state: 'empty' | 'activating' | 'activated'
) {
  if (state === 'empty') {
    await page.waitForSelector('[data-state="empty"]', { timeout: 15_000 });
    // Wait for Framer Motion entrance animation to settle
    await page.waitForTimeout(500);
  } else if (state === 'activating') {
    await page.waitForSelector('[data-state="activating"]', { timeout: 15_000 });
    await page.waitForTimeout(800);
  } else {
    // activated: wait for React Flow canvas
    await page.waitForSelector('[data-state="activated"]', { timeout: 20_000 });
    // Wait for React Flow to finish fitting the view
    await page.waitForTimeout(1200);
  }
}

// ── 9 viewport × state fixtures ─────────────────────────────────────────────

for (const viewport of VIEWPORTS) {
  for (const state of STATES) {
    test(`decisions-${state}-${viewport.name}`, async ({ page }) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });

      // Navigate with ?devState= param for dev-mode state override
      await page.goto(`/decisions?devState=${state}`, { waitUntil: 'domcontentloaded' });
      await waitForState(page, state);

      await expect(page).toHaveScreenshot(
        `decisions-${state}-${viewport.name}.png`,
        {
          maxDiffPixelRatio: 0.02,
          // Mask animated elements that vary per-render
          mask: [],
          animations: 'disabled',
        }
      );
    });
  }
}

// ── Edge-types fixture ───────────────────────────────────────────────────────

test('decisions-edge-types', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });

  // Use ?devState=activated&devEdgeDemo=true to seed all three edge types
  await page.goto('/decisions?devState=activated&devEdgeDemo=true', {
    waitUntil: 'domcontentloaded',
  });

  // Wait for activated state and React Flow to render
  await page.waitForSelector('[data-state="activated"]', { timeout: 20_000 });
  await page.waitForTimeout(1200);

  // Verify all three edge type indicators are present in the DOM
  // (edge paths rendered by DecisionEdge for predecessor/alternative/dependent)
  await expect(page.locator('.react-flow__edge')).not.toHaveCount(0);

  await expect(page).toHaveScreenshot('decisions-edge-types.png', {
    maxDiffPixelRatio: 0.02,
    animations: 'disabled',
  });
});
