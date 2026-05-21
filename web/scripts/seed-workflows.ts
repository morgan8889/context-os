#!/usr/bin/env tsx
/**
 * seed-workflows.ts — CLI to seed synthetic workflow data to the dev API.
 *
 * Usage:
 *   tsx scripts/seed-workflows.ts --workflows 5 --steps-per-workflow 4 --state activated
 */

import { parseArgs } from 'node:util';
import http from 'node:http';

const STEP_STATUSES = ['active', 'blocked', 'complete', 'pending'] as const;
const WORKFLOW_STATUSES = ['healthy', 'degraded', 'blocked'] as const;
const TEAMS = ['Infra', 'Product', 'Platform', 'Data', 'Frontend', 'Backend'];
const ACTORS = ['alice', 'bob', 'charlie', 'diana', 'evan', 'fatima'];

type StepStatus = typeof STEP_STATUSES[number];
type WorkflowStatus = typeof WORKFLOW_STATUSES[number];
type SeedState = 'empty' | 'activating' | 'activated';

function randomItem<T>(arr: readonly T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function generateLatency(): { p50: number | null; p95: number | null } {
  // ~25% chance of being a bottleneck (p95 > 500ms)
  const isBottleneck = Math.random() < 0.25;
  const p50 = randomInt(50, 400);
  const p95 = isBottleneck ? randomInt(501, 2000) : randomInt(p50, 480);
  return { p50, p95 };
}

interface ApiWorkflowStep {
  id: string;
  workflow_id: string;
  label: string;
  step_index: number;
  status: StepStatus;
  owner_team: string | null;
  owner_actor: string | null;
  autonomy_level: number;
  latency_p50_ms: number | null;
  latency_p95_ms: number | null;
}

interface ApiWorkflowEdge {
  id: string;
  source_id: string;
  target_id: string;
  label: string | null;
}

interface ApiWorkflow {
  id: string;
  name: string;
  owner_team: string | null;
  status: WorkflowStatus;
  steps: ApiWorkflowStep[];
  edges: ApiWorkflowEdge[];
}

function generateWorkflow(index: number, stepsCount: number): ApiWorkflow {
  const workflowId = `wf-seed-${index}-${Date.now()}`;
  const team = randomItem(TEAMS);
  const status = randomItem(WORKFLOW_STATUSES);

  const steps: ApiWorkflowStep[] = Array.from({ length: stepsCount }, (_, si) => {
    const latency = generateLatency();
    return {
      id: `${workflowId}-step-${si}`,
      workflow_id: workflowId,
      label: `Step ${si + 1}: ${randomItem(['Review', 'Approve', 'Process', 'Validate', 'Notify', 'Archive'])}`,
      step_index: si,
      status: randomItem(STEP_STATUSES),
      owner_team: Math.random() > 0.2 ? team : null,
      owner_actor: Math.random() > 0.3 ? randomItem(ACTORS) : null,
      autonomy_level: randomInt(0, 5),
      latency_p50_ms: latency.p50,
      latency_p95_ms: latency.p95,
    };
  });

  // Build edges as a chain (each step → next step)
  const edges: ApiWorkflowEdge[] = [];
  for (let i = 0; i < steps.length - 1; i++) {
    edges.push({
      id: `${workflowId}-edge-${i}`,
      source_id: steps[i].id,
      target_id: steps[i + 1].id,
      label: null,
    });
  }

  return {
    id: workflowId,
    name: `Workflow ${index + 1}: ${randomItem(['Quarterly Review', 'Release Gate', 'Incident Response', 'Compliance Audit', 'Customer Onboarding', 'Budget Approval'])}`,
    owner_team: team,
    status,
    steps,
    edges,
  };
}

function postJson(url: string, body: unknown): Promise<{ status: number; body: string }> {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const parsed = new URL(url);
    const req = http.request(
      {
        hostname: parsed.hostname,
        port: parsed.port ? parseInt(parsed.port) : 8000,
        path: parsed.pathname,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(data),
        },
      },
      (res) => {
        let responseBody = '';
        res.on('data', (chunk) => (responseBody += chunk));
        res.on('end', () => resolve({ status: res.statusCode ?? 0, body: responseBody }));
      }
    );
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

async function main() {
  const { values } = parseArgs({
    options: {
      workflows: { type: 'string', short: 'w', default: '5' },
      'steps-per-workflow': { type: 'string', short: 's', default: '4' },
      state: { type: 'string', default: 'activated' },
      host: { type: 'string', default: 'http://localhost:8000' },
    },
  });

  const workflowCount = parseInt(values.workflows as string, 10);
  const stepsPerWorkflow = parseInt(values['steps-per-workflow'] as string, 10);
  const state = (values.state as SeedState) ?? 'activated';
  const host = values.host as string;

  console.log(`Generating ${workflowCount} workflow(s) × ${stepsPerWorkflow} step(s) — state: ${state}`);

  const workflows: ApiWorkflow[] = Array.from({ length: workflowCount }, (_, i) =>
    generateWorkflow(i, stepsPerWorkflow)
  );

  const bottleneckCount = workflows.flatMap((w) => w.steps).filter(
    (s) => (s.latency_p95_ms ?? 0) > 500
  ).length;

  console.log(`  Total steps:      ${workflows.reduce((sum, w) => sum + w.steps.length, 0)}`);
  console.log(`  Bottleneck steps: ${bottleneckCount}`);

  const payload = { workflows, view_state: state };
  const endpoint = `${host}/api/v1/graph/seed`;

  console.log(`\nPOSTing to ${endpoint}…`);

  try {
    const result = await postJson(endpoint, payload);
    if (result.status >= 200 && result.status < 300) {
      console.log(`Done. Status ${result.status}`);
      console.log(result.body);
    } else {
      console.error(`Seed endpoint returned HTTP ${result.status}`);
      console.error(result.body);
      process.exit(1);
    }
  } catch (err) {
    console.error('Failed to reach seed endpoint:', err);
    console.error('Make sure the dev server is running (uv run uvicorn ...)');
    process.exit(1);
  }
}

main();
