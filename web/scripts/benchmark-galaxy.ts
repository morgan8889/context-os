#!/usr/bin/env tsx
/**
 * benchmark-galaxy.ts — Playwright-based performance benchmark for the galaxy view.
 *
 * Measures:
 *   - layout_convergence_ms: Time from ForceAtlas2 start to position stability
 *   - frame_paint_p95_ms:    p95 of Sigma afterRender events over 100 frames
 *
 * Exit codes:
 *   0 — within thresholds (layout <= 5000ms, p95 <= 33ms)
 *   1 — threshold exceeded or benchmark error
 *
 * Usage:
 *   npx tsx scripts/benchmark-galaxy.ts
 */

import { chromium } from '@playwright/test';
import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';

const GALAXY_URL = process.env['BENCHMARK_URL'] ?? 'http://localhost:5173/galaxy?mock=activated&nodes=10000';
const LAYOUT_CONVERGENCE_THRESHOLD_MS = 5000;
const FRAME_PAINT_P95_THRESHOLD_MS = 33;
const FRAME_SAMPLE_COUNT = 100;
const STABILITY_CHECK_FRAMES = 3;
const STABILITY_TOLERANCE_PX = 0.5;
// Hard cap on the layout-convergence polling phase so the benchmark can never
// hang waiting for a layout that never fully settles (e.g. under SwiftShader).
const MAX_LAYOUT_WAIT_MS = 8000;

interface BenchmarkResult {
  layout_convergence_ms: number;
  frame_paint_p95_ms: number;
  timestamp: string;
  url: string;
  node_count: number | null;
}

function percentile(sorted: number[], p: number): number {
  const idx = Math.ceil((p / 100) * sorted.length) - 1;
  return sorted[Math.max(0, Math.min(idx, sorted.length - 1))]!;
}

async function main() {
  console.log('Starting galaxy benchmark...');
  console.log(`URL: ${GALAXY_URL}`);

  const browser = await chromium.launch({
    // SwiftShader provides software WebGL in headless mode (required for Sigma canvas)
    args: ['--no-sandbox', '--use-gl=swiftshader', '--disable-dev-shm-usage'],
  });

  const page = await browser.newPage();
  await page.setViewportSize({ width: 1440, height: 900 });

  try {
    await page.goto(GALAXY_URL, { waitUntil: 'domcontentloaded' });

    // Wait for the galaxy view container, then for Sigma to initialise
    await page.waitForSelector('[data-view="galaxy"]', { timeout: 10_000 });
    // BenchmarkRef sets window.__sigma once SigmaContainer mounts; poll for it
    await page.waitForFunction(() => !!(window as { __sigma?: unknown }).__sigma, { timeout: 20_000 });

    // Inject measurement code into the page. Self-driven and bounded so it can
    // never hang: layout convergence is polled (capped at maxLayoutMs), then
    // frame-paint timing forces a fixed number of repaints via sigma.refresh()
    // and measures inter-frame intervals (natural afterRender events stop once
    // the layout converges, so we drive the renders ourselves).
    //
    // NOTE: every callback here is an anonymous argument — no named function
    // expressions. tsx/esbuild's keepNames would otherwise wrap named functions
    // with a `__name()` helper that is undefined in the page's eval context.
    const metrics = await page.evaluate(
      async ({ frameCount, stabilityFrames, stabilityTolerance, maxLayoutMs }) => {
        type SigmaLike = {
          getGraph: () => { nodes: () => string[] };
          getNodeDisplayData: (id: string) => { x: number; y: number } | undefined;
          refresh: () => void;
        };
        const win = window as typeof window & { __sigma?: SigmaLike };

        // Wait (≤10s) for the Sigma instance exposed by BenchmarkRef.
        const sigma = await new Promise<SigmaLike>((resolve, reject) => {
          let attempts = 0;
          const iv = setInterval(() => {
            if (win.__sigma) {
              clearInterval(iv);
              resolve(win.__sigma);
            } else if (++attempts >= 100) {
              clearInterval(iv);
              reject(new Error('Sigma instance not found on window.__sigma after 10s'));
            }
          }, 100);
        });

        // Phase 1 — layout convergence via position stability (polled, capped).
        const layoutStart = performance.now();
        const layoutConvergenceMs = await new Promise<number>((resolve) => {
          let lastPositions: Record<string, { x: number; y: number }> = {};
          let stableCount = 0;
          const iv = setInterval(() => {
            const now = performance.now();
            const cur: Record<string, { x: number; y: number }> = {};
            for (const id of sigma.getGraph().nodes().slice(0, 50)) {
              const d = sigma.getNodeDisplayData(id);
              if (d) cur[id] = { x: d.x, y: d.y };
            }
            if (Object.keys(lastPositions).length > 0) {
              let maxDelta = 0;
              for (const id of Object.keys(cur)) {
                const prev = lastPositions[id];
                if (prev) {
                  const dx = cur[id]!.x - prev.x;
                  const dy = cur[id]!.y - prev.y;
                  maxDelta = Math.max(maxDelta, Math.sqrt(dx * dx + dy * dy));
                }
              }
              stableCount = maxDelta < stabilityTolerance ? stableCount + 1 : 0;
              if (stableCount >= stabilityFrames) {
                clearInterval(iv);
                resolve(now - layoutStart);
                return;
              }
            }
            lastPositions = cur;
            if (now - layoutStart >= maxLayoutMs) {
              clearInterval(iv);
              resolve(now - layoutStart);
            }
          }, 16);
        });

        // Phase 2 — frame paint timing: force repaints and measure intervals.
        const frameTimesMs = await new Promise<number[]>((resolve) => {
          const times: number[] = [];
          let last = performance.now();
          const iv = setInterval(() => {
            const now = performance.now();
            times.push(now - last);
            last = now;
            sigma.refresh();
            if (times.length >= frameCount) {
              clearInterval(iv);
              resolve(times);
            }
          }, 0);
        });

        return {
          layoutConvergenceMs,
          frameTimesMs,
          nodeCount: sigma.getGraph().nodes().length,
        };
      },
      {
        frameCount: FRAME_SAMPLE_COUNT,
        stabilityFrames: STABILITY_CHECK_FRAMES,
        stabilityTolerance: STABILITY_TOLERANCE_PX,
        maxLayoutMs: MAX_LAYOUT_WAIT_MS,
      }
    );

    const sortedFrameTimes = [...metrics.frameTimesMs].sort((a, b) => a - b);
    const p95 = percentile(sortedFrameTimes, 95);

    const result: BenchmarkResult = {
      layout_convergence_ms: metrics.layoutConvergenceMs,
      frame_paint_p95_ms: p95,
      timestamp: new Date().toISOString(),
      url: GALAXY_URL,
      node_count: metrics.nodeCount,
    };

    console.log('\nBenchmark Results:');
    console.log(`  layout_convergence_ms : ${result.layout_convergence_ms.toFixed(1)} ms`);
    console.log(`  frame_paint_p95_ms    : ${result.frame_paint_p95_ms.toFixed(1)} ms`);
    console.log(`  node_count            : ${result.node_count ?? 'unknown'}`);

    // Write results to file
    const dateStr = new Date().toISOString().replace(/:/g, '-').slice(0, 19);
    const outDir = join(process.cwd(), 'benchmarks');
    mkdirSync(outDir, { recursive: true });
    const outPath = join(outDir, `galaxy-${dateStr}.json`);
    writeFileSync(outPath, JSON.stringify(result, null, 2));
    console.log(`\nResults written to: ${outPath}`);

    // Check thresholds
    const failures: string[] = [];

    if (result.layout_convergence_ms > LAYOUT_CONVERGENCE_THRESHOLD_MS) {
      failures.push(
        `layout_convergence_ms ${result.layout_convergence_ms.toFixed(1)} exceeds ${LAYOUT_CONVERGENCE_THRESHOLD_MS}ms threshold`
      );
    }

    if (result.frame_paint_p95_ms > FRAME_PAINT_P95_THRESHOLD_MS) {
      failures.push(
        `frame_paint_p95_ms ${result.frame_paint_p95_ms.toFixed(1)} exceeds ${FRAME_PAINT_P95_THRESHOLD_MS}ms threshold`
      );
    }

    if (failures.length > 0) {
      console.error('\nThreshold failures:');
      failures.forEach((f) => console.error(`  FAIL: ${f}`));
      process.exit(1);
    }

    console.log('\nAll thresholds passed.');
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error('Benchmark failed:', err instanceof Error ? err.message : err);
  process.exit(1);
});
