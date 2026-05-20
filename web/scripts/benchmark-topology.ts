#!/usr/bin/env tsx
/**
 * benchmark-topology.ts — Playwright performance benchmark for the Topology view.
 *
 * Navigates to /topology with a 500-node seed, then:
 *   1. Measures pan/zoom responsiveness
 *   2. Measures filter-change-to-DOM-settle time
 *
 * Writes results to web/benchmarks/topology-<date>.json.
 * Exits non-zero if filter p95 > 1000ms.
 */

import { chromium, type Page } from '@playwright/test';
import { writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const FILTER_P95_THRESHOLD_MS = 1_000;
const QUIET_PERIOD_MS = 100;
const RUNS = 5;

/** Waits until no DOM mutations occur for `quietMs` milliseconds. */
async function waitForDomQuiet(page: Page, quietMs = QUIET_PERIOD_MS): Promise<number> {
  const start = Date.now();
  await page.evaluate((quiet) => {
    return new Promise<void>((resolve) => {
      let timer: ReturnType<typeof setTimeout>;

      function reset() {
        clearTimeout(timer);
        timer = setTimeout(resolve, quiet);
      }

      const observer = new MutationObserver(reset);
      observer.observe(document.body, { subtree: true, childList: true, attributes: true });
      reset();
    });
  }, quietMs);
  return Date.now() - start;
}

/** Click a filter button and measure settle time. */
async function measureFilterChange(page: Page, filterLabel: string): Promise<number> {
  // Find a filter button by its text content
  const button = page.getByRole('button', { name: filterLabel });
  const clickStart = Date.now();
  await button.click();
  const settleMs = await waitForDomQuiet(page);
  return clickStart + settleMs - clickStart;
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });
  const page = await context.newPage();

  // Navigate to topology with activated state and 500-node mock
  await page.goto('http://localhost:5173/topology?mock=activated&nodes=500');

  // Wait for canvas to be ready
  try {
    await page.waitForSelector('[data-view="topology-activated"]', { timeout: 30_000 });
  } catch {
    console.error('Topology activated view did not appear within 30s');
    await browser.close();
    process.exit(1);
  }

  // Allow React Flow to finish its fitView animation
  await page.waitForTimeout(1_000);

  // ── Pan/zoom benchmark ──────────────────────────────────────────────────

  const panZoomTimes: number[] = [];

  for (let i = 0; i < RUNS; i++) {
    const start = Date.now();
    // Simulate scroll zoom
    await page.mouse.move(720, 450);
    await page.mouse.wheel(0, -100);
    const settled = await waitForDomQuiet(page, 50);
    panZoomTimes.push(start + settled - start);
  }

  // ── Filter benchmark ────────────────────────────────────────────────────

  const filterTimes: number[] = [];

  // Toggle a status filter multiple times
  for (let i = 0; i < RUNS; i++) {
    const ms = await measureFilterChange(page, i % 2 === 0 ? 'Active' : 'Blocked');
    filterTimes.push(ms);
  }

  // Clear filters between toggle runs
  const clearBtn = page.getByRole('button', { name: 'Clear all' });
  if (await clearBtn.isVisible()) {
    await clearBtn.click();
    await waitForDomQuiet(page);
  }

  await browser.close();

  // ── Statistics ──────────────────────────────────────────────────────────

  function p95(arr: number[]): number {
    const sorted = [...arr].sort((a, b) => a - b);
    return sorted[Math.floor(sorted.length * 0.95)] ?? sorted[sorted.length - 1] ?? 0;
  }

  function avg(arr: number[]): number {
    return arr.reduce((s, v) => s + v, 0) / arr.length;
  }

  const dateStr = new Date().toISOString().slice(0, 10);
  const results = {
    date: new Date().toISOString(),
    panZoom: {
      runs: panZoomTimes,
      avgMs: Math.round(avg(panZoomTimes)),
      p95Ms: Math.round(p95(panZoomTimes)),
    },
    filter: {
      runs: filterTimes,
      avgMs: Math.round(avg(filterTimes)),
      p95Ms: Math.round(p95(filterTimes)),
    },
    thresholds: {
      filterP95ThresholdMs: FILTER_P95_THRESHOLD_MS,
      pass: p95(filterTimes) <= FILTER_P95_THRESHOLD_MS,
    },
  };

  // Write JSON report
  const benchDir = join(process.cwd(), 'benchmarks');
  mkdirSync(benchDir, { recursive: true });
  const reportPath = join(benchDir, `topology-${dateStr}.json`);
  writeFileSync(reportPath, JSON.stringify(results, null, 2));

  console.log('Topology Benchmark Results');
  console.log('══════════════════════════');
  console.log(`Pan/zoom avg: ${results.panZoom.avgMs}ms  p95: ${results.panZoom.p95Ms}ms`);
  console.log(`Filter    avg: ${results.filter.avgMs}ms  p95: ${results.filter.p95Ms}ms`);
  console.log(`Report: ${reportPath}`);

  if (!results.thresholds.pass) {
    console.error(
      `FAIL: Filter p95 (${results.filter.p95Ms}ms) exceeds threshold (${FILTER_P95_THRESHOLD_MS}ms)`
    );
    process.exit(1);
  }

  console.log(`PASS: Filter p95 within ${FILTER_P95_THRESHOLD_MS}ms threshold`);
}

main().catch((err) => {
  console.error('Benchmark error:', err);
  process.exit(1);
});
