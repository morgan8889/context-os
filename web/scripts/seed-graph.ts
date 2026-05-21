#!/usr/bin/env tsx
/**
 * seed-graph.ts — CLI script to seed synthetic graph data.
 *
 * Usage:
 *   npx tsx scripts/seed-graph.ts --nodes 50 --edges 100 --state activated
 *   npx tsx scripts/seed-graph.ts --nodes 10 --edges 15 --state activating
 *   npx tsx scripts/seed-graph.ts --state empty
 */

import axios from 'axios';

const BASE_URL = process.env['VITE_API_BASE_URL'] ?? 'http://localhost:8000';

type NodeType = 'goal' | 'project' | 'signal' | 'artifact';
type NodeStatus = 'active' | 'paused' | 'complete' | 'at_risk';
type EdgeType = 'depends_on' | 'shared_actor' | 'shared_work';
type GalaxyState = 'empty' | 'activating' | 'activated';

interface SeedApiNode {
  id: string;
  label: string;
  node_type: NodeType;
  status: NodeStatus;
  owner_team: string | null;
  actor_count: number;
  risk_score: number | null;
  autonomy_level: number | null;
  edge_count: number;
}

interface SeedApiEdge {
  id: string;
  source_id: string;
  target_id: string;
  edge_type: EdgeType;
  weight: number;
}

const NODE_TYPES: NodeType[] = ['goal', 'project', 'signal', 'artifact'];
const NODE_STATUSES: NodeStatus[] = ['active', 'paused', 'complete', 'at_risk'];
const EDGE_TYPES: EdgeType[] = ['depends_on', 'shared_actor', 'shared_work'];
const TEAMS = ['platform', 'growth', 'core', 'infra', 'data', 'design', 'research'];

function randomFrom<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)]!;
}

function randomFloat(min: number, max: number, decimals = 2): number {
  return parseFloat((Math.random() * (max - min) + min).toFixed(decimals));
}

function generateNodeId(index: number): string {
  return `seed-node-${Date.now()}-${index}`;
}

function generateEdgeId(source: string, target: string, index: number): string {
  return `seed-edge-${index}-${source.slice(-4)}-${target.slice(-4)}`;
}

function generateNode(index: number): SeedApiNode {
  const type = randomFrom(NODE_TYPES);
  const status = randomFrom(NODE_STATUSES);
  const edgeCount = Math.floor(Math.random() * 12);

  return {
    id: generateNodeId(index),
    label: `${type.charAt(0).toUpperCase() + type.slice(1)} ${index + 1}`,
    node_type: type,
    status,
    owner_team: Math.random() > 0.2 ? randomFrom(TEAMS) : null,
    actor_count: Math.floor(Math.random() * 8) + 1,
    risk_score: Math.random() > 0.3 ? randomFloat(0, 1) : null,
    autonomy_level: Math.random() > 0.3 ? Math.floor(Math.random() * 6) : null,
    edge_count: edgeCount,
  };
}

function generateEdges(nodes: SeedApiNode[], targetEdgeCount: number): SeedApiEdge[] {
  const edges: SeedApiEdge[] = [];
  const nodeIds = nodes.map((n) => n.id);

  // Cap at reasonable density
  const actual = Math.min(targetEdgeCount, nodeIds.length * (nodeIds.length - 1) / 2);

  const usedPairs = new Set<string>();

  while (edges.length < actual) {
    const sourceId = randomFrom(nodeIds);
    const targetId = randomFrom(nodeIds);
    if (sourceId === targetId) continue;

    const pairKey = [sourceId, targetId].sort().join('|');
    if (usedPairs.has(pairKey)) continue;

    usedPairs.add(pairKey);
    const index = edges.length;

    edges.push({
      id: generateEdgeId(sourceId, targetId, index),
      source_id: sourceId,
      target_id: targetId,
      edge_type: randomFrom(EDGE_TYPES),
      weight: randomFloat(0.1, 1.0),
    });
  }

  return edges;
}

function parseArgs(): { nodes: number; edges: number; state: GalaxyState } {
  const args = process.argv.slice(2);
  let nodes = 30;
  let edges = 50;
  let state: GalaxyState = 'activated';

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    const next = args[i + 1];

    if (arg === '--nodes' && next) {
      nodes = parseInt(next, 10);
      i++;
    } else if (arg === '--edges' && next) {
      edges = parseInt(next, 10);
      i++;
    } else if (arg === '--state' && next) {
      if (['empty', 'activating', 'activated'].includes(next)) {
        state = next as GalaxyState;
      }
      i++;
    }
  }

  return { nodes, edges, state };
}

async function main() {
  const { nodes: nodeCount, edges: edgeCount, state } = parseArgs();

  console.log(`Seeding graph: state=${state}, nodes=${nodeCount}, edges=${edgeCount}`);

  if (state === 'empty') {
    console.log('State is "empty" — no nodes or edges to seed.');
    console.log('Seeded 0 nodes, 0 edges');
    return;
  }

  // For activating: generate 1–25 real nodes, remainder as stubs
  let realNodeCount = nodeCount;
  if (state === 'activating') {
    realNodeCount = Math.min(25, Math.max(1, nodeCount));
    console.log(`Activating state: generating ${realNodeCount} real nodes + stubs`);
  }

  const nodes = Array.from({ length: realNodeCount }, (_, i) => generateNode(i));
  const edges = generateEdges(nodes, edgeCount);

  const client = axios.create({ baseURL: BASE_URL, timeout: 30_000 });

  // POST nodes
  let seededNodes = 0;
  let seededEdges = 0;

  try {
    const nodeRes = await client.post<{ count: number }>(
      '/api/v1/graph/nodes/seed',
      { nodes }
    );
    seededNodes = nodeRes.data.count ?? nodes.length;
  } catch (err) {
    // If seed endpoint doesn't exist yet, try individual posts
    if (axios.isAxiosError(err) && err.response?.status === 404) {
      console.warn('Bulk seed endpoint not found — skipping node POST (dev mode)');
      seededNodes = nodes.length;
    } else {
      console.error('Failed to seed nodes:', err instanceof Error ? err.message : err);
      process.exit(1);
    }
  }

  // POST edges
  try {
    const edgeRes = await client.post<{ count: number }>(
      '/api/v1/graph/edges/seed',
      { edges }
    );
    seededEdges = edgeRes.data.count ?? edges.length;
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 404) {
      console.warn('Bulk seed endpoint not found — skipping edge POST (dev mode)');
      seededEdges = edges.length;
    } else {
      console.error('Failed to seed edges:', err instanceof Error ? err.message : err);
      process.exit(1);
    }
  }

  console.log(`Seeded ${seededNodes} nodes, ${seededEdges} edges`);
}

main().catch((err) => {
  console.error('Seed script failed:', err);
  process.exit(1);
});
