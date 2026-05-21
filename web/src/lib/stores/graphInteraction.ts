import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import type { SelectionSet, OverlayConfig, GalaxySnapshot } from '@/types/galaxy';
import type { TopologyFilters } from '@/types/topology';
import type { DecisionFilters } from '@/types/decisions';
import type { ViewStateContext } from '@/types/viewstate';

interface GraphInteractionStore {
  // Galaxy
  galaxySelection: SelectionSet;
  galaxyOverlay: OverlayConfig;
  galaxyTimeCursor: string | null;
  galaxySnapshots: GalaxySnapshot[];
  focusedNodeId: string | null;

  // Topology
  topologyFilters: TopologyFilters;

  // Decision Graph
  decisionFilters: DecisionFilters;
  focusedDecisionId: string | null;

  // Cross-view
  viewStates: ViewStateContext;

  // Actions
  setGalaxySelection: (selection: SelectionSet) => void;
  clearGalaxySelection: () => void;
  setGalaxyOverlay: (overlay: OverlayConfig) => void;
  setGalaxyTimeCursor: (cursor: string | null) => void;
  setGalaxySnapshots: (snapshots: GalaxySnapshot[]) => void;
  setFocusedNodeId: (id: string | null) => void;
  setTopologyFilters: (filters: Partial<TopologyFilters>) => void;
  clearTopologyFilters: () => void;
  setDecisionFilters: (filters: Partial<DecisionFilters>) => void;
  clearDecisionFilters: () => void;
  setFocusedDecisionId: (id: string | null) => void;
  setViewStates: (states: Partial<ViewStateContext>) => void;
}

const defaultOverlay: OverlayConfig = {
  type: null,
  thresholds: { low: 0.3, high: 0.7 },
};

const defaultTopologyFilters: TopologyFilters = {
  teamId: null,
  initiativeId: null,
  status: null,
};

const defaultDecisionFilters: DecisionFilters = {
  query: '',
  fromDate: null,
  toDate: null,
  authorId: null,
  impactedSystem: null,
};

const defaultViewStates: ViewStateContext = {
  galaxy: { state: 'empty', initiativeCount: 0, ingestProgress: null },
  topology: { state: 'empty', workflowCount: 0, discoveredCount: 0 },
  decisionGraph: { state: 'empty', decisionCount: 0 },
};

export const useGraphInteractionStore = create<GraphInteractionStore>()(
  immer((set) => ({
    galaxySelection: { nodeIds: new Set<string>(), source: 'lasso' as const },
    galaxyOverlay: defaultOverlay,
    galaxyTimeCursor: null,
    galaxySnapshots: [],
    focusedNodeId: null,
    topologyFilters: defaultTopologyFilters,
    decisionFilters: defaultDecisionFilters,
    focusedDecisionId: null,
    viewStates: defaultViewStates,

    setGalaxySelection: (selection) =>
      set((s) => {
        s.galaxySelection = selection;
      }),
    clearGalaxySelection: () =>
      set((s) => {
        s.galaxySelection = { nodeIds: new Set<string>(), source: 'lasso' as const };
      }),
    setGalaxyOverlay: (overlay) =>
      set((s) => {
        s.galaxyOverlay = overlay;
      }),
    setGalaxyTimeCursor: (cursor) =>
      set((s) => {
        s.galaxyTimeCursor = cursor;
      }),
    setGalaxySnapshots: (snapshots) =>
      set((s) => {
        s.galaxySnapshots = snapshots;
      }),
    setFocusedNodeId: (id) =>
      set((s) => {
        s.focusedNodeId = id;
      }),
    setTopologyFilters: (filters) =>
      set((s) => {
        Object.assign(s.topologyFilters, filters);
      }),
    clearTopologyFilters: () =>
      set((s) => {
        s.topologyFilters = defaultTopologyFilters;
      }),
    setDecisionFilters: (filters) =>
      set((s) => {
        Object.assign(s.decisionFilters, filters);
      }),
    clearDecisionFilters: () =>
      set((s) => {
        s.decisionFilters = defaultDecisionFilters;
      }),
    setFocusedDecisionId: (id) =>
      set((s) => {
        s.focusedDecisionId = id;
      }),
    setViewStates: (states) =>
      set((s) => {
        Object.assign(s.viewStates, states);
      }),
  }))
);
