export type DecisionStatus = 'active' | 'superseded' | 'retracted';
export type DecisionViewState = 'activated' | 'activating' | 'placeholder';
export type DecisionEdgeType = 'predecessor' | 'alternative' | 'dependent';

export interface DecisionAlternative {
  label: string;
  reason: string;
}

export interface DecisionNode {
  // Index signature required for React Flow Node<T> generic constraint
  [key: string]: unknown;
  id: string;
  title: string;
  rationale: string;
  alternatives: DecisionAlternative[];
  authorId: string | null;
  authorName: string | null;
  capturedAt: string;
  impactedSystems: string[];
  status: DecisionStatus;
  viewState: DecisionViewState;
}

export interface DecisionEdge {
  // Index signature required for React Flow Edge<T> generic constraint
  [key: string]: unknown;
  id: string;
  source: string;
  target: string;
  type: DecisionEdgeType;
}

export interface DecisionFilters {
  query: string;
  fromDate: string | null;
  toDate: string | null;
  authorId: string | null;
  impactedSystem: string | null;
}
