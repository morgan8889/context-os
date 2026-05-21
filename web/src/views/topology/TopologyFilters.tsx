import { FilterBar } from '@/design-system/primitives/FilterBar';
import type { FilterGroup } from '@/design-system/primitives/FilterBar';
import { useGraphInteractionStore } from '@/lib/stores/graphInteraction';
import type { WorkflowSummary, StepStatus } from '@/types/topology';

const STATUS_OPTIONS: Array<{ value: StepStatus; label: string }> = [
  { value: 'active', label: 'Active' },
  { value: 'blocked', label: 'Blocked' },
  { value: 'pending', label: 'Pending' },
];

interface TopologyFiltersProps {
  /** All loaded workflow summaries — used to derive unique team options. */
  workflows: WorkflowSummary[];
}

/**
 * TopologyFilters — wraps the FilterBar primitive with topology-specific
 * filter groups for team and step status.
 *
 * Filter state lives in Zustand; changes are reflected globally via
 * useGraphInteractionStore.
 */
export function TopologyFilters({ workflows }: TopologyFiltersProps) {
  const topologyFilters = useGraphInteractionStore((s) => s.topologyFilters);
  const setTopologyFilters = useGraphInteractionStore((s) => s.setTopologyFilters);
  const clearTopologyFilters = useGraphInteractionStore((s) => s.clearTopologyFilters);

  // Derive unique team names from loaded workflows
  const teamOptions = Array.from(
    new Set(workflows.map((w) => w.ownerTeam).filter((t): t is string => t !== null))
  ).map((team) => ({ value: team, label: team }));

  const filterGroups: FilterGroup[] = [
    ...(teamOptions.length > 0
      ? [{ key: 'team', label: 'Team', options: teamOptions }]
      : []),
    {
      key: 'status',
      label: 'Status',
      options: STATUS_OPTIONS,
    },
  ];

  const activeFilters: Record<string, string> = {
    team: topologyFilters.teamId ?? '',
    status: topologyFilters.status ?? '',
  };

  function handleChange(key: string, value: string) {
    if (key === 'team') {
      setTopologyFilters({ teamId: value || null });
    } else if (key === 'status') {
      setTopologyFilters({ status: (value as StepStatus) || null });
    }
  }

  return (
    <FilterBar
      filters={filterGroups}
      activeFilters={activeFilters}
      onChange={handleChange}
      onClear={clearTopologyFilters}
    />
  );
}
