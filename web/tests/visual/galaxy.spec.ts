import { test, expect, type Page } from '@playwright/test';

/**
 * Galaxy visual regression tests — 9 fixtures.
 *
 * 3 viewports × 3 states = 9 screenshots.
 * All fixtures disable animations via VITE_DISABLE_ANIMATIONS=true
 * (set in the environment before running Playwright).
 */

type GalaxyState = 'empty' | 'activating' | 'activated';

interface Viewport {
  name: string;
  width: number;
  height: number;
}

const VIEWPORTS: Viewport[] = [
  { name: '1024x768', width: 1024, height: 768 },
  { name: '1440x900', width: 1440, height: 900 },
  { name: '2560x1440', width: 2560, height: 1440 },
];

const STATES: GalaxyState[] = ['empty', 'activating', 'activated'];

async function navigateToGalaxy(page: Page, state: GalaxyState): Promise<void> {
  await page.goto(`/galaxy?mock=${state}`, { waitUntil: 'networkidle' });
}

async function waitForStableRender(page: Page, state: GalaxyState): Promise<void> {
  switch (state) {
    case 'empty':
      // Wait for the empty state container
      await page.waitForSelector('[data-state="empty"]', { timeout: 10_000 });
      // Allow entrance animation to settle (disabled via env var in test)
      await page.waitForTimeout(100);
      break;

    case 'activating':
      // Wait for the activating state container
      await page.waitForSelector('[data-state="activating"]', { timeout: 10_000 });
      // Wait for Sigma canvas to paint
      await page.waitForSelector('.sigma-renderer', { timeout: 10_000 });
      await page.waitForTimeout(200);
      break;

    case 'activated':
      // Wait for the galaxy view container
      await page.waitForSelector('[data-view="galaxy"]', { timeout: 10_000 });
      // Wait for Sigma renderer to appear
      await page.waitForSelector('.sigma-renderer', { timeout: 15_000 });
      // Allow initial layout to paint (ForceAtlas2 disabled in test env)
      await page.waitForTimeout(300);
      break;
  }
}

// Generate all 9 fixture combinations
for (const viewport of VIEWPORTS) {
  for (const state of STATES) {
    test(`galaxy-${viewport.name}-${state}`, async ({ page }) => {
      // Set viewport
      await page.setViewportSize({ width: viewport.width, height: viewport.height });

      // Navigate to galaxy with mock state
      await navigateToGalaxy(page, state);

      // Wait for stable render
      await waitForStableRender(page, state);

      // Take screenshot and compare
      await expect(page).toHaveScreenshot(`galaxy-${viewport.name}-${state}.png`, {
        maxDiffPixelRatio: 0.02,
        // Ensure full page is captured consistently
        fullPage: false,
        // Clip to viewport to avoid OS chrome differences
        clip: { x: 0, y: 0, width: viewport.width, height: viewport.height },
      });
    });
  }
}
