export interface IngestProgress {
  discoveredCount: number;
  estimatedTotal: number | null;
  estimatedCompletionAt: string | null;
}

export interface GalaxyViewState {
  state: 'empty' | 'activating' | 'activated';
  initiativeCount: number;
  ingestProgress: IngestProgress | null;
}

export interface TopologyViewState {
  state: 'empty' | 'activating' | 'activated';
  workflowCount: number;
  discoveredCount: number;
}

export interface DecisionGraphViewState {
  state: 'empty' | 'activating' | 'activated';
  decisionCount: number;
}

export interface ViewStateContext {
  galaxy: GalaxyViewState;
  topology: TopologyViewState;
  decisionGraph: DecisionGraphViewState;
}
