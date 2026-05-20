#!/usr/bin/env tsx
/**
 * seed-decisions.ts — Generate synthetic decision data and POST to the dev seed endpoint.
 *
 * Usage:
 *   tsx scripts/seed-decisions.ts --decisions 20 --state activated
 *   tsx scripts/seed-decisions.ts --decisions 10 --state activating
 *   tsx scripts/seed-decisions.ts --state empty
 */

import { parseArgs } from 'node:util';

// ── Types ──────────────────────────────────────────────────────────────────

interface SeedDecision {
  id: string;
  title: string;
  rationale: string;
  alternatives: Array<{ label: string; reason: string }>;
  author_id: string | null;
  author_name: string | null;
  captured_at: string;
  impacted_systems: string[];
  status: 'active' | 'superseded' | 'retracted';
}

interface SeedDecisionEdge {
  id: string;
  source_id: string;
  target_id: string;
  edge_type: 'predecessor' | 'alternative' | 'dependent';
}

// ── Seed data pools ────────────────────────────────────────────────────────

const TITLES = [
  'Adopt PostgreSQL as primary datastore',
  'Use OpenTelemetry for all telemetry',
  'Enforce tenant isolation at the query layer',
  'Migrate from REST to GraphQL for client APIs',
  'Require code review approval from two engineers',
  'Use LangGraph for all multi-step agent workflows',
  'Standardise on Python 3.12 across all services',
  'Deploy on Kubernetes for container orchestration',
  'Adopt Clerk for authentication across all services',
  'Implement HNSW indexes for vector similarity search',
  'Use Apache AGE for graph queries',
  'Freeze public API contracts before GA',
  'Enforce Ruff as the sole Python linter',
  'Use Alembic for all database migrations',
  'Require OTEL spans for every agent action',
  'Adopt React 19 for the frontend workspace',
  'Use Tailwind CSS v4 for all UI styling',
  'Pin Node.js to LTS version in all services',
  'Use Vitest for unit tests in the web workspace',
  'Adopt Framer Motion for everyday UI animations',
];

const RATIONALES = [
  'Chosen for its mature ecosystem, JSONB support, and pgvector extension compatibility.',
  'Enables vendor-neutral tracing and integrates cleanly with Langfuse for LLM cost tracking.',
  'Prevents cross-tenant data leakage without requiring application-level filtering on every query.',
  'Reduces over-fetching and enables field-level access control for complex nested queries.',
  'Increases review quality and reduces single-point-of-knowledge risk.',
  'Provides durable, resumable workflow execution with human-in-the-loop support via interrupt_before.',
  'Unlocks modern type hint syntax and performance improvements in the asyncio runtime.',
  'Provides declarative infrastructure management and horizontal pod autoscaling for burst workloads.',
  'Eliminates custom auth plumbing and provides JWT RS256 with per-organization claims.',
  'Achieves sub-millisecond approximate nearest-neighbour search at production scale.',
  'Enables Cypher-based pattern matching directly within Postgres without a separate graph DB.',
  'Prevents breaking changes from shipping to production before clients can adapt.',
  'Single linter tool reduces developer cognitive overhead and CI configuration complexity.',
  'Auto-generated migrations are reviewable and version-controlled alongside application code.',
  'Creates an audit trail satisfying the Observable Autonomy principle in the constitution.',
  'Concurrent rendering and use() hook reduce waterfall patterns in data-heavy views.',
  'Zero-runtime CSS approach eliminates class-name collisions and reduces bundle size.',
  'Avoids compatibility drift between local development and CI environments.',
  'Shares the Vite transform pipeline, reducing configuration overhead for the test harness.',
  'Separates GSAP set-piece transitions from everyday hover/selection animations cleanly.',
];

const ALTERNATIVES = [
  [
    { label: 'MySQL', reason: 'Lacks native JSONB support and vector extension ecosystem.' },
    { label: 'MongoDB', reason: 'Schema flexibility not required; ACID transactions are.' },
  ],
  [
    { label: 'Datadog proprietary SDK', reason: 'Vendor lock-in and high egress costs at scale.' },
    { label: 'Custom logging only', reason: 'Insufficient for distributed trace correlation.' },
  ],
  [
    { label: 'Row-level security in PostgreSQL', reason: 'Adds migration complexity and testing overhead.' },
  ],
  [
    { label: 'tRPC', reason: 'Excellent DX but TypeScript-only; limits future non-TS clients.' },
    { label: 'gRPC', reason: 'Better for internal services; client-side complexity too high.' },
    { label: 'Keep REST', reason: 'Simplest option but over-fetching is an observable bottleneck.' },
  ],
  [
    { label: 'Single reviewer', reason: 'Faster but increases risk of defect escape.' },
    { label: 'No code review', reason: 'Rejected outright given constitution governance requirements.' },
  ],
];

const AUTHORS = [
  { id: 'usr_01', name: 'Priya Raghavan' },
  { id: 'usr_02', name: 'James Okafor' },
  { id: 'usr_03', name: 'Sofia Marchetti' },
  { id: 'usr_04', name: 'Daniel Svensson' },
  { id: 'usr_05', name: 'Mei-Lin Chen' },
];

const SYSTEMS = [
  'api-gateway',
  'agent-runtime',
  'graph-module',
  'vector-module',
  'auth-service',
  'observability',
  'web-frontend',
  'ingestion-pipeline',
  'workflow-engine',
  'eval-runner',
];

const STATUSES: SeedDecision['status'][] = ['active', 'active', 'active', 'superseded', 'retracted'];

const EDGE_TYPES: SeedDecisionEdge['edge_type'][] = ['predecessor', 'alternative', 'dependent'];

// ── Helpers ────────────────────────────────────────────────────────────────

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)] as T;
}

function pickN<T>(arr: T[], n: number): T[] {
  const shuffled = [...arr].sort(() => Math.random() - 0.5);
  return shuffled.slice(0, n);
}

function randomDate(daysBack: number): string {
  const ms = Date.now() - Math.floor(Math.random() * daysBack * 24 * 60 * 60 * 1000);
  return new Date(ms).toISOString();
}

function generateDecisions(count: number): SeedDecision[] {
  return Array.from({ length: count }, (_, i) => {
    const author = Math.random() > 0.1 ? pick(AUTHORS) : null;
    return {
      id: `dec_seed_${String(i).padStart(4, '0')}`,
      title: TITLES[i % TITLES.length] ?? `Decision ${i}`,
      rationale: RATIONALES[i % RATIONALES.length] ?? 'No rationale provided.',
      alternatives: pick(ALTERNATIVES),
      author_id: author?.id ?? null,
      author_name: author?.name ?? null,
      captured_at: randomDate(365),
      impacted_systems: pickN(SYSTEMS, 1 + Math.floor(Math.random() * 3)),
      status: pick(STATUSES),
    };
  });
}

function generateEdges(decisions: SeedDecision[]): SeedDecisionEdge[] {
  if (decisions.length < 2) return [];

  const edges: SeedDecisionEdge[] = [];
  const edgeSet = new Set<string>();

  // Generate roughly N/2 edges, avoiding obvious cycles
  const targetEdgeCount = Math.floor(decisions.length / 2);

  for (let i = 0; i < targetEdgeCount * 3 && edges.length < targetEdgeCount; i++) {
    const sourceIdx = Math.floor(Math.random() * decisions.length);
    // Target must have a higher index to avoid back-edges (simple cycle prevention)
    const remaining = decisions.length - sourceIdx - 1;
    if (remaining <= 0) continue;
    const targetIdx = sourceIdx + 1 + Math.floor(Math.random() * remaining);

    const source = decisions[sourceIdx];
    const target = decisions[targetIdx];
    if (!source || !target) continue;

    const key = `${source.id}→${target.id}`;
    if (edgeSet.has(key)) continue;
    edgeSet.add(key);

    edges.push({
      id: `edge_seed_${edges.length.toString().padStart(4, '0')}`,
      source_id: source.id,
      target_id: target.id,
      edge_type: pick(EDGE_TYPES),
    });
  }

  return edges;
}

// ── Main ───────────────────────────────────────────────────────────────────

async function main() {
  const { values } = parseArgs({
    options: {
      decisions: { type: 'string', default: '20' },
      state: { type: 'string', default: 'activated' },
      endpoint: { type: 'string', default: 'http://localhost:8000/api/v1/dev/seed-decisions' },
    },
    strict: true,
    allowPositionals: false,
  });

  const state = values.state as 'empty' | 'activating' | 'activated';
  const endpoint = values.endpoint as string;

  let count = parseInt(values.decisions as string, 10);
  if (isNaN(count) || count < 0) count = 20;

  // State-specific count constraints
  if (state === 'empty') {
    count = 0;
  } else if (state === 'activating') {
    count = Math.min(Math.max(count, 1), 19);
  }

  console.log(`[seed-decisions] state=${state} decisions=${count}`);

  const decisions = generateDecisions(count);
  const edges = generateEdges(decisions);

  const payload = { decisions, edges, view_state: state };

  console.log(`[seed-decisions] Posting ${decisions.length} decisions, ${edges.length} edges to ${endpoint}`);

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const body = await response.text();
      console.error(`[seed-decisions] POST failed: ${response.status} ${response.statusText}`);
      console.error(body);
      process.exit(1);
    }

    console.log(`[seed-decisions] Seed complete.`);
    console.log(`  Decisions : ${decisions.length}`);
    console.log(`  Edges     : ${edges.length}`);
    console.log(`  View state: ${state}`);

    const authors = new Set(decisions.filter((d) => d.author_id).map((d) => d.author_id));
    console.log(`  Authors   : ${authors.size}`);

    const systems = new Set(decisions.flatMap((d) => d.impacted_systems));
    console.log(`  Systems   : ${systems.size}`);
  } catch (err) {
    console.error('[seed-decisions] Network error:', err);
    process.exit(1);
  }
}

main();
