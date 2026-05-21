import { useCallback } from 'react';
import { useGraphInteractionStore } from '@/lib/stores/graphInteraction';
import type { ApiWorkflow } from '@/types/api';
import type { TopologyFilters } from '@/types/topology';

/**
 * useTopologyFilters — reads topology filters from Zustand store and
 * provides a client-side filter function for ApiWorkflow arrays.
 *
 * All filtering is in-memory — no re-fetch is triggered by filter changes.
 */
export function useTopologyFilters() {
  const topologyFilters = useGraphInteractionStore((s) => s.topologyFilters);
  const setTopologyFilters = useGraphInteractionStore((s) => s.setTopologyFilters);
  const clearTopologyFilters = useGraphInteractionStore((s) => s.clearTopologyFilters);

  const filterWorkflows = useCallback(
    (workflows: ApiWorkflow[], filters: TopologyFilters): ApiWorkflow[] => {
      return workflows.filter((workflow) => {
        // Team filter
        if (filters.teamId !== null) {
          if (workflow.owner_team !== filters.teamId) return false;
        }

        // Status filter — any step in workflow must match
        if (filters.status !== null) {
          const hasMatchingStep = workflow.steps.some(
            (step) => step.status === filters.status
          );
          if (!hasMatchingStep) return false;
        }

        return true;
      });
    },
    []
  );

  return {
    topologyFilters,
    setTopologyFilters,
    clearTopologyFilters,
    filterWorkflows,
  };
}
