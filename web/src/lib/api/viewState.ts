import { useQuery } from '@tanstack/react-query';
import { useEffect } from 'react';
import { apiClient } from './client';
import { viewStateKeys } from './queryKeys';
import { useGraphInteractionStore } from '../stores/graphInteraction';
import type { ApiViewState } from '@/types/api';
import type { ViewStateContext } from '@/types/viewstate';

function transformViewState(raw: ApiViewState): ViewStateContext {
  return {
    galaxy: {
      state: raw.galaxy.state,
      initiativeCount: raw.galaxy.initiative_count,
      ingestProgress: raw.galaxy.ingest_progress
        ? {
            discoveredCount: raw.galaxy.ingest_progress.discovered_count,
            estimatedTotal: raw.galaxy.ingest_progress.estimated_total,
            estimatedCompletionAt: raw.galaxy.ingest_progress.estimated_completion_at,
          }
        : null,
    },
    topology: {
      state: raw.topology.state,
      workflowCount: raw.topology.workflow_count,
      discoveredCount: raw.topology.discovered_count,
    },
    decisionGraph: {
      state: raw.decision_graph.state,
      decisionCount: raw.decision_graph.decision_count,
    },
  };
}

function isFullyActivated(data: ViewStateContext | undefined): boolean {
  if (!data) return false;
  return (
    data.galaxy.state === 'activated' &&
    data.topology.state === 'activated' &&
    data.decisionGraph.state === 'activated'
  );
}

/** Read ?mock= or ?devState= URL params for local dev/test overrides. */
function getDevOverride(): ViewStateContext | null {
  if (typeof window === 'undefined') return null;
  const params = new URLSearchParams(window.location.search);

  const mock = params.get('mock');
  if (mock && ['empty', 'activating', 'activated'].includes(mock)) {
    const s = mock as 'empty' | 'activating' | 'activated';
    return {
      galaxy: { state: s, initiativeCount: 0, ingestProgress: null },
      topology: { state: s, workflowCount: 0, discoveredCount: 0 },
      decisionGraph: { state: s, decisionCount: 0 },
    };
  }

  const devState = params.get('devState');
  if (devState && ['empty', 'activating', 'activated'].includes(devState)) {
    const s = devState as 'empty' | 'activating' | 'activated';
    return {
      galaxy: { state: 'activated', initiativeCount: 50, ingestProgress: null },
      topology: { state: 'activated', workflowCount: 12, discoveredCount: 12 },
      decisionGraph: { state: s, decisionCount: 0 },
    };
  }

  return null;
}

export function useViewState() {
  const setViewStates = useGraphInteractionStore((s) => s.setViewStates);
  const devOverride = getDevOverride();

  const query = useQuery({
    queryKey: viewStateKeys.current(),
    queryFn: async () => {
      if (devOverride) return devOverride;
      const { data } = await apiClient.get<ApiViewState>('/api/v1/views/state');
      return transformViewState(data);
    },
    refetchInterval: (q) => {
      if (devOverride) return false;
      return isFullyActivated(q.state.data) ? false : 30_000;
    },
    staleTime: 0,
  });

  useEffect(() => {
    if (query.data) {
      setViewStates(query.data);
    }
  }, [query.data, setViewStates]);

  return query;
}
