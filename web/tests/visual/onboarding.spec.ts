/**
 * T025: Onboarding visual regression tests — 9 fixtures.
 *
 * 3 viewports × 3 steps = 9 screenshots.
 * Each fixture seeds session state via route query param (?mock=<step>)
 * so the OnboardingShell renders the correct step without a real API.
 *
 * The mock is handled by the app's dev MSW / query mock layer when
 * VITE_DEV_BYPASS_AUTH=true and the mock query param is present.
 */
import { test, expect, type Page } from '@playwright/test';

type OnboardingStep = 'survey' | 'connect' | 'scope';

interface Viewport {
  width: number;
  height: number;
}

const VIEWPORTS: Viewport[] = [
  { width: 1024, height: 768 },
  { width: 1440, height: 900 },
  { width: 2560, height: 1440 },
];

const STEPS: OnboardingStep[] = ['survey', 'connect', 'scope'];

async function navigateToOnboardingStep(page: Page, step: OnboardingStep): Promise<void> {
  // Seed session state via mock query param; VITE_DEV_BYPASS_AUTH skips Clerk
  await page.goto(`/onboarding?mock=${step}`, { waitUntil: 'domcontentloaded' });
}

async function waitForStableRender(page: Page, step: OnboardingStep): Promise<void> {
  switch (step) {
    case 'survey':
      // Wait for the survey radio-button group
      await page.waitForSelector('fieldset', { timeout: 10_000 });
      await page.waitForTimeout(150);
      break;

    case 'connect':
      // Wait for at least one Connect button
      await page.waitForSelector('button:has-text("Connect")', { timeout: 10_000 });
      await page.waitForTimeout(150);
      break;

    case 'scope':
      // Wait for the scope confirmation button
      await page.waitForSelector('button:has-text("Confirm")', { timeout: 10_000 });
      await page.waitForTimeout(150);
      break;
  }
}

// Generate 9 fixture combinations
for (const { width, height } of VIEWPORTS) {
  for (const step of STEPS) {
    test(`onboarding-${width}-${step}`, async ({ page }) => {
      await page.setViewportSize({ width, height });

      await navigateToOnboardingStep(page, step);
      await waitForStableRender(page, step);

      await expect(page).toHaveScreenshot(`onboarding-${width}-${step}.png`, {
        maxDiffPixelRatio: 0.02,
        fullPage: false,
        clip: { x: 0, y: 0, width, height },
      });
    });
  }
}
