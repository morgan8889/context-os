export type StepStatus = 'active' | 'blocked' | 'complete' | 'pending';
export type StepViewState = 'activated' | 'activating' | 'placeholder';
export type WorkflowStatus = 'healthy' | 'degraded' | 'blocked';
export type WorkflowViewState = 'activated' | 'activating' | 'placeholder';

export interface WorkflowNode {
  // Index signature required for React Flow Node<T> generic constraint
  [key: string]: unknown;
  id: string;
  workflowId: string;
  label: string;
  stepIndex: number;
  status: StepStatus;
  ownerTeam: string | null;
  ownerActor: string | null;
  autonomyLevel: number;
  latencyP50Ms: number | null;
  latencyP95Ms: number | null;
  isBottleneck: boolean;
  viewState: StepViewState;
}

export interface WorkflowEdge {
  // Index signature required for React Flow Edge<T> generic constraint
  [key: string]: unknown;
  id: string;
  source: string;
  target: string;
  label: string | null;
  isBottleneck: boolean;
}

export interface WorkflowSummary {
  id: string;
  name: string;
  ownerTeam: string | null;
  nodeCount: number;
  status: WorkflowStatus;
  viewState: WorkflowViewState;
}

export interface TopologyFilters {
  teamId: string | null;
  initiativeId: string | null;
  status: StepStatus | null;
}
