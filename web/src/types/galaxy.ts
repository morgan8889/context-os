export type InitiativeType = 'goal' | 'project' | 'signal' | 'artifact';
export type InitiativeStatus = 'active' | 'paused' | 'complete' | 'at_risk';
export type NodeViewState = 'activated' | 'activating' | 'placeholder';
export type EdgeType = 'depends_on' | 'shared_actor' | 'shared_work' | 'placeholder';
export type OverlayType = 'load' | 'risk' | 'autonomy' | 'ownership';

export interface InitiativeNode {
  id: string;
  label: string;
  type: InitiativeType;
  status: InitiativeStatus;
  ownerTeam: string | null;
  actorCount: number;
  riskScore: number | null;
  autonomyLevel: number | null;
  edgeCount: number;
  x: number;
  y: number;
  size: number;
  viewState: NodeViewState;
}

export interface InitiativeEdge {
  id: string;
  source: string;
  target: string;
  type: EdgeType;
  weight: number;
}

export interface GalaxySnapshot {
  timestamp: string;
  nodes: InitiativeNode[];
  edges: InitiativeEdge[];
  layoutSeed: number;
}

export interface OverlayConfig {
  type: OverlayType | null;
  thresholds: {
    low: number;
    high: number;
  };
}

export interface SelectionSet {
  nodeIds: Set<string>;
  source: 'lasso' | 'click' | 'filter';
}
