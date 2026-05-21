import { test, expect } from '@playwright/test';

type ViewportName = '1024x768' | '1440x900' | '2560x1440';
type ViewState = 'empty' | 'activating' | 'activated';

const VIEWPORTS: Array<{ name: ViewportName; width: number; height: number }> = [
  { name: '1024x768', width: 1024, height: 768 },
  { name: '1440x900', width: 1440, height: 900 },
  { name: '2560x1440', width: 2560, height: 1440 },
];

const STATES: ViewState[] = ['empty', 'activating', 'activated'];

for (const viewport of VIEWPORTS) {
  for (const state of STATES) {
    test(`topology ${viewport.name} ${state}`, async ({ page }) => {
      // Set viewport
      await page.setViewportSize({ width: viewport.width, height: viewport.height });

      // Navigate with mock query param for the given state
      await page.goto(`/topology?mock=${state}`);

      // Wait for the view container to appear
      await page.waitForSelector(`[data-view="topology-${state}"]`, {
        timeout: 15_000,
      });

      // Wait for React Flow canvas to be fully initialized (no loading spinner)
      await page.waitForFunction(
        () => {
          const spinner = document.querySelector('[aria-label="Loading topology"]');
          return !spinner;
        },
        { timeout: 10_000 }
      );

      // Allow layout animations to settle (Framer Motion entrance)
      await page.waitForTimeout(400);

      // Take screenshot
      await expect(page).toHaveScreenshot(
        `topology-${viewport.name}-${state}.png`,
        { maxDiffPixelRatio: 0.02 }
      );
    });
  }
}
