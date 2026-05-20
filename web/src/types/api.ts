export interface ApiNode {
  id: string;
  label: string;
  node_type: 'goal' | 'project' | 'signal' | 'artifact';
  status: 'active' | 'paused' | 'complete' | 'at_risk';
  owner_team: string | null;
  actor_count: number;
  risk_score: number | null;
  autonomy_level: number | null;
  edge_count: number;
}

export interface ApiEdge {
  id: string;
  source_id: string;
  target_id: string;
  edge_type: 'depends_on' | 'shared_actor' | 'shared_work';
  weight: number;
}

export interface ApiGraphSnapshot {
  timestamp: string;
  nodes: ApiNode[];
  edges: ApiEdge[];
  layout_seed: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  next_cursor: string | null;
  total: number;
}

export interface ApiWorkflowStep {
  id: string;
  workflow_id: string;
  label: string;
  step_index: number;
  status: 'active' | 'blocked' | 'complete' | 'pending';
  owner_team: string | null;
  owner_actor: string | null;
  autonomy_level: number;
  latency_p50_ms: number | null;
  latency_p95_ms: number | null;
}

export interface ApiWorkflowEdge {
  id: string;
  source_id: string;
  target_id: string;
  label: string | null;
}

export interface ApiWorkflow {
  id: string;
  name: string;
  owner_team: string | null;
  status: 'healthy' | 'degraded' | 'blocked';
  steps: ApiWorkflowStep[];
  edges: ApiWorkflowEdge[];
}

export interface ApiDecision {
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

export interface ApiDecisionEdge {
  id: string;
  source_id: string;
  target_id: string;
  edge_type: 'predecessor' | 'alternative' | 'dependent';
}

export interface ApiViewState {
  galaxy: {
    state: 'empty' | 'activating' | 'activated';
    initiative_count: number;
    ingest_progress: {
      discovered_count: number;
      estimated_total: number | null;
      estimated_completion_at: string | null;
    } | null;
  };
  topology: {
    state: 'empty' | 'activating' | 'activated';
    workflow_count: number;
    discovered_count: number;
  };
  decision_graph: {
    state: 'empty' | 'activating' | 'activated';
    decision_count: number;
  };
}

export interface ApiApprovalItem {
  id: string;
  item_type: 'briefing_draft' | 'proposed_dependency' | 'proposed_risk';
  status: 'pending' | 'approved' | 'rejected';
  content: Record<string, unknown>;
  failure_flags: Array<{ type: string; detail: string }> | null;
  created_at: string;
}
