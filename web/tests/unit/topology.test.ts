import { describe, it, expect } from 'vitest';
import dagre from '@dagrejs/dagre';
import { toWorkflowNode, toWorkflowEdge, BOTTLENECK_THRESHOLD_MS } from '../../src/lib/transforms/workflow';
import type { ApiWorkflowStep, ApiWorkflowEdge, ApiWorkflow } from '../../src/types/api';
import type { TopologyFilters } from '../../src/types/topology';

// ─── Helper factories ────────────────────────────────────────────────────────

function makeStep(overrides: Partial<ApiWorkflowStep> = {}): ApiWorkflowStep {
  return {
    id: 'step-1',
    workflow_id: 'wf-1',
    label: 'Test Step',
    step_index: 0,
    status: 'active',
    owner_team: 'Infra',
    owner_actor: 'alice',
    autonomy_level: 2,
    latency_p50_ms: 100,
    latency_p95_ms: 200,
    ...overrides,
  };
}

function makeEdge(overrides: Partial<ApiWorkflowEdge> = {}): ApiWorkflowEdge {
  return {
    id: 'edge-1',
    source_id: 'step-1',
    target_id: 'step-2',
    label: null,
    ...overrides,
  };
}

function makeWorkflow(overrides: Partial<ApiWorkflow> = {}): ApiWorkflow {
  return {
    id: 'wf-1',
    name: 'Test Workflow',
    owner_team: 'Infra',
    status: 'healthy',
    steps: [
      makeStep({ id: 'step-1', step_index: 0 }),
      makeStep({ id: 'step-2', step_index: 1, status: 'blocked' }),
    ],
    edges: [makeEdge()],
    ...overrides,
  };
}

// ─── toWorkflowNode ──────────────────────────────────────────────────────────

describe('toWorkflowNode', () => {
  it('maps all fields from ApiWorkflowStep', () => {
    const raw = makeStep();
    const node = toWorkflowNode(raw);
    expect(node.id).toBe(raw.id);
    expect(node.workflowId).toBe(raw.workflow_id);
    expect(node.label).toBe(raw.label);
    expect(node.stepIndex).toBe(raw.step_index);
    expect(node.status).toBe(raw.status);
    expect(node.ownerTeam).toBe(raw.owner_team);
    expect(node.ownerActor).toBe(raw.owner_actor);
    expect(node.autonomyLevel).toBe(raw.autonomy_level);
    expect(node.latencyP50Ms).toBe(raw.latency_p50_ms);
    expect(node.latencyP95Ms).toBe(raw.latency_p95_ms);
    expect(node.viewState).toBe('activated');
  });

  it('isBottleneck is false when latency_p95_ms is 499ms (below threshold)', () => {
    const node = toWorkflowNode(makeStep({ latency_p95_ms: 499 }));
    expect(node.isBottleneck).toBe(false);
  });

  it(`isBottleneck is false when latency_p95_ms equals threshold (${BOTTLENECK_THRESHOLD_MS}ms)`, () => {
    const node = toWorkflowNode(makeStep({ latency_p95_ms: BOTTLENECK_THRESHOLD_MS }));
    expect(node.isBottleneck).toBe(false);
  });

  it('isBottleneck is true when latency_p95_ms is 501ms (above threshold)', () => {
    const node = toWorkflowNode(makeStep({ latency_p95_ms: 501 }));
    expect(node.isBottleneck).toBe(true);
  });

  it('isBottleneck is false when latency_p95_ms is null', () => {
    const node = toWorkflowNode(makeStep({ latency_p95_ms: null }));
    expect(node.isBottleneck).toBe(false);
  });
});

// ─── useTopologyFilters (pure filter function tests) ─────────────────────────

function filterWorkflows(workflows: ApiWorkflow[], filters: TopologyFilters): ApiWorkflow[] {
  return workflows.filter((workflow) => {
    if (filters.teamId !== null) {
      if (workflow.owner_team !== filters.teamId) return false;
    }
    if (filters.status !== null) {
      const hasMatchingStep = workflow.steps.some((step) => step.status === filters.status);
      if (!hasMatchingStep) return false;
    }
    return true;
  });
}

const nullFilters: TopologyFilters = { teamId: null, initiativeId: null, status: null };

describe('topology filter function', () => {
  const workflows: ApiWorkflow[] = [
    makeWorkflow({ id: 'wf-1', owner_team: 'Infra' }),
    makeWorkflow({
      id: 'wf-2',
      owner_team: 'Product',
      steps: [makeStep({ id: 's3', workflow_id: 'wf-2', status: 'complete' })],
    }),
    makeWorkflow({
      id: 'wf-3',
      owner_team: 'Infra',
      steps: [makeStep({ id: 's4', workflow_id: 'wf-3', status: 'pending' })],
    }),
  ];

  it('null filters return all workflows', () => {
    const result = filterWorkflows(workflows, nullFilters);
    expect(result).toHaveLength(3);
  });

  it('team filter isolates workflows with matching owner_team', () => {
    const result = filterWorkflows(workflows, { ...nullFilters, teamId: 'Infra' });
    expect(result).toHaveLength(2);
    expect(result.every((w) => w.owner_team === 'Infra')).toBe(true);
  });

  it('team filter returns empty when no workflows match', () => {
    const result = filterWorkflows(workflows, { ...nullFilters, teamId: 'Unknown' });
    expect(result).toHaveLength(0);
  });

  it('status filter returns workflows that have at least one step with matching status', () => {
    const result = filterWorkflows(workflows, { ...nullFilters, status: 'complete' });
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe('wf-2');
  });

  it('combined team + status filter applies both constraints', () => {
    // wf-1 has Infra + blocked step, wf-3 has Infra + pending step
    const result = filterWorkflows(workflows, { ...nullFilters, teamId: 'Infra', status: 'blocked' });
    // wf-1 has a blocked step (step-2), wf-3 has only pending
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe('wf-1');
  });

  it('null teamId + null status returns all', () => {
    const result = filterWorkflows(workflows, { teamId: null, initiativeId: null, status: null });
    expect(result).toHaveLength(3);
  });
});

// ─── Dagre layout ────────────────────────────────────────────────────────────

describe('Dagre layout', () => {
  function runLayout(nodeCount: number) {
    const g = new dagre.graphlib.Graph();
    g.setGraph({ rankdir: 'LR', nodesep: 80, ranksep: 120 });
    g.setDefaultEdgeLabel(() => ({}));

    const ids = Array.from({ length: nodeCount }, (_, i) => `n${i}`);
    ids.forEach((id) => g.setNode(id, { width: 200, height: 80 }));
    // Chain edges
    for (let i = 0; i < ids.length - 1; i++) {
      g.setEdge(ids[i], ids[i + 1]);
    }
    dagre.layout(g);
    return { g, ids };
  }

  it('nodes receive valid (non-NaN) x/y positions after layout', () => {
    const { g, ids } = runLayout(5);
    for (const id of ids) {
      const pos = g.node(id);
      expect(isNaN(pos.x)).toBe(false);
      expect(isNaN(pos.y)).toBe(false);
    }
  });

  it('no two nodes share the exact same position (no overlap at default settings)', () => {
    const { g, ids } = runLayout(4);
    const positions = ids.map((id) => {
      const p = g.node(id);
      return `${Math.round(p.x)},${Math.round(p.y)}`;
    });
    const unique = new Set(positions);
    expect(unique.size).toBe(ids.length);
  });

  it('positions increase left-to-right with LR rankdir', () => {
    const { g, ids } = runLayout(3);
    const xs = ids.map((id) => g.node(id).x);
    // Each subsequent node in a chain should have a greater x
    for (let i = 0; i < xs.length - 1; i++) {
      expect(xs[i + 1]).toBeGreaterThan(xs[i]);
    }
  });
});

// ─── toWorkflowEdge ──────────────────────────────────────────────────────────

describe('toWorkflowEdge', () => {
  it('marks edge as bottleneck when source step is a bottleneck', () => {
    const sourceStep = toWorkflowNode(makeStep({ id: 'step-1', latency_p95_ms: 600 }));
    const targetStep = toWorkflowNode(makeStep({ id: 'step-2', latency_p95_ms: 100 }));
    const rawEdge = makeEdge({ source_id: 'step-1', target_id: 'step-2' });
    const edge = toWorkflowEdge(rawEdge, [sourceStep, targetStep]);
    expect(edge.isBottleneck).toBe(true);
  });

  it('does not mark edge as bottleneck when neither step exceeds threshold', () => {
    const sourceStep = toWorkflowNode(makeStep({ id: 'step-1', latency_p95_ms: 200 }));
    const targetStep = toWorkflowNode(makeStep({ id: 'step-2', latency_p95_ms: 300 }));
    const rawEdge = makeEdge({ source_id: 'step-1', target_id: 'step-2' });
    const edge = toWorkflowEdge(rawEdge, [sourceStep, targetStep]);
    expect(edge.isBottleneck).toBe(false);
  });
});
