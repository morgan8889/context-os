import type { ApiNode, ApiEdge } from '@/types/api';
import type { InitiativeNode, InitiativeEdge } from '@/types/galaxy';

export const BOTTLENECK_EDGE_COUNT_THRESHOLD = 5;

export function toInitiativeNode(raw: ApiNode): InitiativeNode {
  return {
    id: raw.id,
    label: raw.label,
    type: raw.node_type,
    status: raw.status,
    ownerTeam: raw.owner_team,
    actorCount: raw.actor_count,
    riskScore: raw.risk_score,
    autonomyLevel: raw.autonomy_level,
    edgeCount: raw.edge_count,
    x: 0,
    y: 0,
    size: Math.max(4, Math.min(20, 4 + raw.edge_count * 0.8)),
    viewState: 'activated',
  };
}

export function toInitiativeEdge(raw: ApiEdge): InitiativeEdge {
  return {
    id: raw.id,
    source: raw.source_id,
    target: raw.target_id,
    type: raw.edge_type,
    weight: raw.weight,
  };
}
