import type { ApiDecision, ApiDecisionEdge } from '@/types/api';
import type { DecisionNode, DecisionEdge } from '@/types/decisions';

export function toDecisionNode(raw: ApiDecision): DecisionNode {
  return {
    id: raw.id,
    title: raw.title,
    rationale: raw.rationale,
    alternatives: raw.alternatives,
    authorId: raw.author_id,
    authorName: raw.author_name,
    capturedAt: raw.captured_at,
    impactedSystems: raw.impacted_systems,
    status: raw.status,
    viewState: 'activated',
  };
}

export function toDecisionEdge(raw: ApiDecisionEdge): DecisionEdge {
  return {
    id: raw.id,
    source: raw.source_id,
    target: raw.target_id,
    type: raw.edge_type,
  };
}
