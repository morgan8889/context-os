import type { ApiWorkflowStep, ApiWorkflowEdge } from '@/types/api';
import type { WorkflowNode, WorkflowEdge } from '@/types/topology';

export const BOTTLENECK_THRESHOLD_MS = 500;

export function toWorkflowNode(raw: ApiWorkflowStep): WorkflowNode {
  const p95 = raw.latency_p95_ms ?? 0;
  return {
    id: raw.id,
    workflowId: raw.workflow_id,
    label: raw.label,
    stepIndex: raw.step_index,
    status: raw.status,
    ownerTeam: raw.owner_team,
    ownerActor: raw.owner_actor,
    autonomyLevel: raw.autonomy_level,
    latencyP50Ms: raw.latency_p50_ms,
    latencyP95Ms: raw.latency_p95_ms,
    isBottleneck: p95 > BOTTLENECK_THRESHOLD_MS,
    viewState: 'activated',
  };
}

export function toWorkflowEdge(raw: ApiWorkflowEdge, steps: WorkflowNode[]): WorkflowEdge {
  const sourceStep = steps.find((s) => s.id === raw.source_id);
  const targetStep = steps.find((s) => s.id === raw.target_id);
  const isBottleneck = (sourceStep?.isBottleneck ?? false) || (targetStep?.isBottleneck ?? false);
  return {
    id: raw.id,
    source: raw.source_id,
    target: raw.target_id,
    label: raw.label,
    isBottleneck,
  };
}
