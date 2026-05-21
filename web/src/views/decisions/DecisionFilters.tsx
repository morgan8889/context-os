import { useMemo } from 'react';
import type { ChangeEvent } from 'react';
import { FilterBar } from '@/design-system/primitives/FilterBar';
import type { FilterGroup } from '@/design-system/primitives/FilterBar';
import { useGraphInteractionStore } from '@/lib/stores/graphInteraction';
import type { DecisionNode } from '@/types/decisions';

interface DecisionFiltersProps {
  /** All currently-loaded decisions (used to derive filter option values) */
  decisions: DecisionNode[];
}

/**
 * DecisionFilters — filter bar for the Decision Graph view.
 *
 * Derives author and impacted-system filter options from the supplied
 * decisions array. Also renders date-range inputs for from_date/to_date.
 * All state changes dispatch to Zustand via setDecisionFilters.
 */
export function DecisionFilters({ decisions }: DecisionFiltersProps) {
  const decisionFilters = useGraphInteractionStore((s) => s.decisionFilters);
  const setDecisionFilters = useGraphInteractionStore((s) => s.setDecisionFilters);
  const clearDecisionFilters = useGraphInteractionStore((s) => s.clearDecisionFilters);

  // Derive unique authors
  const authorOptions = useMemo(() => {
    const seen = new Set<string>();
    return decisions
      .filter((d) => d.authorId !== null && d.authorName !== null)
      .filter((d) => {
        if (seen.has(d.authorId!)) return false;
        seen.add(d.authorId!);
        return true;
      })
      .map((d) => ({ value: d.authorId!, label: d.authorName! }));
  }, [decisions]);

  // Derive unique impacted systems
  const systemOptions = useMemo(() => {
    const seen = new Set<string>();
    const options: { value: string; label: string }[] = [];
    for (const decision of decisions) {
      for (const sys of decision.impactedSystems) {
        if (!seen.has(sys)) {
          seen.add(sys);
          options.push({ value: sys, label: sys });
        }
      }
    }
    return options;
  }, [decisions]);

  const filterGroups: FilterGroup[] = [
    {
      key: 'authorId',
      label: 'Author',
      options: authorOptions,
    },
    {
      key: 'impactedSystem',
      label: 'System',
      options: systemOptions,
    },
  ];

  const activeFilters: Record<string, string> = {
    authorId: decisionFilters.authorId ?? '',
    impactedSystem: decisionFilters.impactedSystem ?? '',
  };

  function handleFilterChange(key: string, value: string) {
    if (key === 'authorId') {
      setDecisionFilters({ authorId: value || null });
    } else if (key === 'impactedSystem') {
      setDecisionFilters({ impactedSystem: value || null });
    }
  }

  const hasDateFilters = Boolean(decisionFilters.fromDate || decisionFilters.toDate);
  const hasAnyFilter =
    Boolean(decisionFilters.authorId) ||
    Boolean(decisionFilters.impactedSystem) ||
    hasDateFilters;

  return (
    <div className="flex flex-col border-b" style={{ borderColor: 'oklch(90% 0 0)' }}>
      {/* Author + system filter pills */}
      <FilterBar
        filters={filterGroups}
        activeFilters={activeFilters}
        onChange={handleFilterChange}
        {...(hasAnyFilter ? { onClear: clearDecisionFilters } : {})}
      />

      {/* Date-range inputs */}
      <div
        className="flex items-center gap-4 px-3 py-2"
        style={{ borderTop: '1px solid oklch(93% 0 0)', background: 'oklch(99% 0 0)' }}
      >
        <label className="flex items-center gap-2 text-xs" style={{ color: 'oklch(45% 0 0)' }}>
          <span className="font-medium shrink-0">From</span>
          <input
            type="date"
            value={decisionFilters.fromDate ?? ''}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setDecisionFilters({ fromDate: e.target.value || null })
            }
            className="rounded border px-2 py-0.5 text-xs focus:outline-none focus:ring-2"
            style={{
              borderColor: 'oklch(82% 0 0)',
              color: 'oklch(25% 0 0)',
              background: 'oklch(100% 0 0)',
            }}
            aria-label="Filter from date"
          />
        </label>

        <label className="flex items-center gap-2 text-xs" style={{ color: 'oklch(45% 0 0)' }}>
          <span className="font-medium shrink-0">To</span>
          <input
            type="date"
            value={decisionFilters.toDate ?? ''}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setDecisionFilters({ toDate: e.target.value || null })
            }
            className="rounded border px-2 py-0.5 text-xs focus:outline-none focus:ring-2"
            style={{
              borderColor: 'oklch(82% 0 0)',
              color: 'oklch(25% 0 0)',
              background: 'oklch(100% 0 0)',
            }}
            aria-label="Filter to date"
          />
        </label>

        {hasDateFilters && (
          <button
            onClick={() => setDecisionFilters({ fromDate: null, toDate: null })}
            className="text-xs focus-visible:outline-none focus-visible:underline"
            style={{ color: 'oklch(55% 0.15 220)' }}
          >
            Clear dates
          </button>
        )}
      </div>
    </div>
  );
}
