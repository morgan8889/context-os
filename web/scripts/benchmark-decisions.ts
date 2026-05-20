#!/usr/bin/env tsx
/**
 * benchmark-decisions.ts — Playwright-based performance benchmark for the
 * Decision Graph search interaction.
 *
 * Measures from keystroke to DOM settle (100ms quiet period via MutationObserver).
 * Runs 10 varied search queries, asserts p95 < 2000ms.
 *
 * Usage:
 *   tsx scripts/benchmark-decisions.ts
 *
 * Prerequisites:
 *   - Dev server running at http://localhost:5173
 *   - 1000-decision seed applied (use seed-decisions.ts --decisions 1000 --state activated)
 */

import { chromium } from '@playwright/test';
import { writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const BASE_URL = process.env['BENCHMARK_URL'] ?? 'http://localhost:5173';
const THRESHOLD_MS = 2000;

const SEARCH_QUERIES = [
  'PostgreSQL',
  'OpenTelemetry',
  'auth',
  'graph',
  'React',
  'agent',
  'migration',
  'vector',
  'LangGraph',
  'Kubernetes',
];

/** Wait for the DOM to settle: no mutations for `quietMs` milliseconds */
const DOM_SETTLE_SCRIPT = (quietMs: number) => `
  () => new Promise((resolve) => {
    let timer;
    const observer = new MutationObserver(() => {
      clearTimeout(timer);
      timer = setTimeout(() => { observer.disconnect(); resolve(); }, ${quietMs});
    });
    observer.observe(document.body, { childList: true, subtree: true, attributes: true });
    // Initial timeout in case there are no mutations at all
    timer = setTimeout(() => { observer.disconnect(); resolve(); }, ${quietMs});
  })
`;

function percentile(sortedMs: number[], p: number): number {
  const idx = Math.ceil((p / 100) * sortedMs.length) - 1;
  return sortedMs[Math.max(0, idx)] ?? 0;
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });
  const page = await context.newPage();

  console.log(`[benchmark-decisions] Navigating to ${BASE_URL}/decisions`);
  await page.goto(`${BASE_URL}/decisions`, { waitUntil: 'networkidle' });

  // Confirm we are in the activated state (search input must exist)
  const searchInput = page.locator('input[type="search"]');
  try {
    await searchInput.waitFor({ state: 'visible', timeout: 10_000 });
  } catch {
    console.error(
      '[benchmark-decisions] Search input not found — is the view in activated state?\n' +
        'Run: tsx scripts/seed-decisions.ts --decisions 1000 --state activated'
    );
    await browser.close();
    process.exit(1);
  }

  const measurements: number[] = [];

  for (const query of SEARCH_QUERIES) {
    // Clear input
    await searchInput.fill('');
    await page.waitForTimeout(400);

    // Start timing
    const start = Date.now();

    // Type query character-by-character to simulate real keystroke
    await searchInput.pressSequentially(query, { delay: 30 });

    // Wait for DOM to settle (100ms quiet period)
    await page.evaluate(DOM_SETTLE_SCRIPT(100));

    const elapsed = Date.now() - start;
    measurements.push(elapsed);

    console.log(`  query="${query}" → ${elapsed}ms`);
  }

  await browser.close();

  // ── Stats ──────────────────────────────────────────────────────────────

  const sorted = [...measurements].sort((a, b) => a - b);
  const p50 = percentile(sorted, 50);
  const p95 = percentile(sorted, 95);
  const p99 = percentile(sorted, 99);
  const max = sorted[sorted.length - 1] ?? 0;

  console.log('\n[benchmark-decisions] Results:');
  console.log(`  p50 : ${p50}ms`);
  console.log(`  p95 : ${p95}ms  (threshold: ${THRESHOLD_MS}ms)`);
  console.log(`  p99 : ${p99}ms`);
  console.log(`  max : ${max}ms`);

  // ── Write JSON report ──────────────────────────────────────────────────

  const dateStr = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const outDir = join(process.cwd(), 'benchmarks');
  mkdirSync(outDir, { recursive: true });

  const reportPath = join(outDir, `decisions-${dateStr}.json`);
  const report = {
    timestamp: new Date().toISOString(),
    queries: SEARCH_QUERIES.map((q, i) => ({ query: q, ms: measurements[i] ?? 0 })),
    stats: { p50, p95, p99, max },
    threshold: THRESHOLD_MS,
    pass: p95 < THRESHOLD_MS,
  };

  writeFileSync(reportPath, JSON.stringify(report, null, 2));
  console.log(`\n[benchmark-decisions] Report written to ${reportPath}`);

  // ── Assert ─────────────────────────────────────────────────────────────

  if (p95 >= THRESHOLD_MS) {
    console.error(
      `\n[benchmark-decisions] FAIL: p95 ${p95}ms >= threshold ${THRESHOLD_MS}ms`
    );
    process.exit(1);
  }

  console.log(`[benchmark-decisions] PASS: p95 ${p95}ms < ${THRESHOLD_MS}ms`);
}

main().catch((err) => {
  console.error('[benchmark-decisions] Unexpected error:', err);
  process.exit(1);
});
