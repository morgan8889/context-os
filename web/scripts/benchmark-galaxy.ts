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
    args: ['--enable-gpu', '--no-sandbox'],
  });

  const page = await browser.newPage();

  try {
    await page.goto(GALAXY_URL, { waitUntil: 'domcontentloaded' });

    // Wait for the Sigma renderer to appear
    await page.waitForSelector('.sigma-renderer', { timeout: 15_000 });

    // Inject measurement code into the page
    const metrics = await page.evaluate(
      async ({ frameCount, stabilityFrames, stabilityTolerance }) => {
        return new Promise<{
          layoutConvergenceMs: number;
          frameTimesMs: number[];
          nodeCount: number | null;
        }>((resolve, reject) => {
          const win = window as typeof window & {
            __sigma?: {
              getGraph: () => { nodes: () => string[] };
              getNodeDisplayData: (id: string) => { x: number; y: number } | undefined;
              on: (event: string, cb: () => void) => void;
            };
          };

          // Wait for sigma instance to be exposed
          let attempts = 0;
          const maxAttempts = 100;

          const waitForSigma = setInterval(() => {
            attempts++;
            const sigma = win.__sigma;

            if (sigma) {
              clearInterval(waitForSigma);

              const frameTimes: number[] = [];
              const layoutStart = performance.now();

              // Track node positions for convergence detection
              let lastPositions: Record<string, { x: number; y: number }> = {};
              let stableCount = 0;
              let layoutConvergenceMs = -1;
              let frameIndex = 0;

              sigma.on('afterRender', () => {
                const now = performance.now();

                // Record frame time after first frame
                if (frameIndex > 0) {
                  const frameTime = now - lastFrameTime;
                  frameTimes.push(frameTime);
                }
                lastFrameTime = now;
                frameIndex++;

                // Check layout convergence via position stability
                if (layoutConvergenceMs === -1) {
                  const graph = sigma.getGraph();
                  const nodes = graph.nodes();
                  const currentPositions: Record<string, { x: number; y: number }> = {};

                  for (const nodeId of nodes.slice(0, 50)) {
                    const data = sigma.getNodeDisplayData(nodeId);
                    if (data) {
                      currentPositions[nodeId] = { x: data.x, y: data.y };
                    }
                  }

                  // Compare with previous positions
                  if (Object.keys(lastPositions).length > 0) {
                    let maxDelta = 0;
                    for (const [id, pos] of Object.entries(currentPositions)) {
                      const prev = lastPositions[id];
                      if (prev) {
                        const delta = Math.sqrt(
                          Math.pow(pos.x - prev.x, 2) + Math.pow(pos.y - prev.y, 2)
                        );
                        maxDelta = Math.max(maxDelta, delta);
                      }
                    }

                    if (maxDelta < stabilityTolerance) {
                      stableCount++;
                    } else {
                      stableCount = 0;
                    }

                    if (stableCount >= stabilityFrames) {
                      layoutConvergenceMs = now - layoutStart;
                    }
                  }

                  lastPositions = currentPositions;
                }

                // Done collecting frames
                if (frameTimes.length >= frameCount) {
                  const nodeCount = sigma.getGraph().nodes().length;
                  resolve({
                    layoutConvergenceMs: layoutConvergenceMs >= 0 ? layoutConvergenceMs : now - layoutStart,
                    frameTimesMs: frameTimes,
                    nodeCount,
                  });
                }
              });

              let lastFrameTime = performance.now();
            } else if (attempts >= maxAttempts) {
              clearInterval(waitForSigma);
              reject(new Error('Sigma instance not found on window.__sigma after 10s'));
            }
          }, 100);
        });
      },
      {
        frameCount: FRAME_SAMPLE_COUNT,
        stabilityFrames: STABILITY_CHECK_FRAMES,
        stabilityTolerance: STABILITY_TOLERANCE_PX,
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
