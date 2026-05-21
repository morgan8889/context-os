import { test, expect } from '@playwright/test';

/**
 * T053 — FR-030 CTA count and copy assertions across all pre-activated states.
 * Each view in empty/activating state must have exactly one [data-cta="primary"] button
 * with exact label text per FR-031.
 */

const PRE_ACTIVATED_STATES = [
  {
    view: '/galaxy',
    state: 'empty',
    expectedCTAText: 'Adjust source scope',
    dataView: 'galaxy',
  },
  {
    view: '/galaxy',
    state: 'activating',
    expectedCTAText: 'Notify me when done',
    dataView: 'galaxy',
  },
  {
    view: '/topology',
    state: 'empty',
    expectedCTAText: 'View Executive Briefing',
    dataView: 'topology',
  },
  {
    view: '/topology',
    state: 'activating',
    expectedCTAText: 'See what\'s been discovered',
    dataView: 'topology',
  },
  {
    view: '/decisions',
    state: 'empty',
    expectedCTAText: 'Capture a decision manually',
    dataView: 'decisions',
  },
  {
    view: '/decisions',
    state: 'activating',
    expectedCTAText: 'Stay current on decisions',
    dataView: 'decisions',
  },
] as const;

for (const { view, state, expectedCTAText } of PRE_ACTIVATED_STATES) {
  test(`${view} ${state} — exactly one [data-cta="primary"] with correct label`, async ({ page }) => {
    await page.goto(`${view}?mock=${state}`);

    // Wait for the view container to be present
    await page.waitForSelector(`[data-cta="primary"]`, { timeout: 10_000 });

    // Assert exactly one CTA button (FR-030)
    const ctaButtons = page.locator('[data-cta="primary"]');
    await expect(ctaButtons).toHaveCount(1);

    // Assert button text matches FR-031 copy exactly
    await expect(ctaButtons.first()).toHaveText(expectedCTAText);
  });
}

test('galaxy activated — no [data-cta="primary"] buttons', async ({ page }) => {
  await page.goto('/galaxy?mock=activated');
  await page.waitForTimeout(1000);
  const ctaButtons = page.locator('[data-cta="primary"]');
  await expect(ctaButtons).toHaveCount(0);
});

test('topology activated — no [data-cta="primary"] buttons', async ({ page }) => {
  await page.goto('/topology?mock=activated');
  await page.waitForTimeout(1000);
  const ctaButtons = page.locator('[data-cta="primary"]');
  await expect(ctaButtons).toHaveCount(0);
});

test('decisions activated — no [data-cta="primary"] buttons', async ({ page }) => {
  await page.goto('/decisions?mock=activated');
  await page.waitForTimeout(1000);
  const ctaButtons = page.locator('[data-cta="primary"]');
  await expect(ctaButtons).toHaveCount(0);
});
