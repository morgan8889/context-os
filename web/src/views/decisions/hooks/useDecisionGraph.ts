import { useEffect, useMemo, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { decisionKeys } from '@/lib/api/queryKeys';
import { toDecisionNode, toDecisionEdge } from '@/lib/transforms/decision';
import { useGraphInteractionStore } from '@/lib/stores/graphInteraction';
import type { ApiDecision, ApiDecisionEdge } from '@/types/api';
import type { DecisionNode, DecisionEdge } from '@/types/decisions';

/** API response shape for the decisions list endpoint */
interface ApiDecisionsResponse {
  items: ApiDecision[];
  edges: ApiDecisionEdge[];
}

/** Debounce delay in milliseconds */
const DEBOUNCE_MS = 300;

/**
 * useDecisionGraph — fetches and transforms decisions + edges for the
 * Decision Graph view. Debounces filter changes (300ms) and tracks a
 * separate `isSearching` flag when a query-string search is in-flight.
 *
 * @returns decisions, edges, isLoading, isSearching
 */
export function useDecisionGraph(): {
  decisions: DecisionNode[];
  edges: DecisionEdge[];
  isLoading: boolean;
  isSearching: boolean;
} {
  const decisionFilters = useGraphInteractionStore((s) => s.decisionFilters);

  // Debounced filter state — only sent to TanStack Query after 300ms quiet
  const [debouncedFilters, setDebouncedFilters] = useState(decisionFilters);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
    }
    timerRef.current = setTimeout(() => {
      setDebouncedFilters(decisionFilters);
    }, DEBOUNCE_MS);

    return () => {
      if (timerRef.current !== null) {
        clearTimeout(timerRef.current);
      }
    };
  }, [decisionFilters]);

  // Map camelCase filters to snake_case query params
  const queryParams = useMemo(
    () => ({
      q: debouncedFilters.query || undefined,
      from_date: debouncedFilters.fromDate ?? undefined,
      to_date: debouncedFilters.toDate ?? undefined,
      author_id: debouncedFilters.authorId ?? undefined,
      impacted_system: debouncedFilters.impactedSystem ?? undefined,
    }),
    [debouncedFilters]
  );

  const queryKey = decisionKeys.list({
    ...(debouncedFilters.query ? { q: debouncedFilters.query } : {}),
    ...(debouncedFilters.fromDate ? { fromDate: debouncedFilters.fromDate } : {}),
    ...(debouncedFilters.toDate ? { toDate: debouncedFilters.toDate } : {}),
    ...(debouncedFilters.authorId ? { authorId: debouncedFilters.authorId } : {}),
    ...(debouncedFilters.impactedSystem ? { impactedSystem: debouncedFilters.impactedSystem } : {}),
  });

  const { data, isFetching, isLoading } = useQuery({
    queryKey,
    queryFn: async () => {
      const { data: raw } = await apiClient.get<ApiDecisionsResponse>(
        '/api/v1/decisions',
        { params: queryParams }
      );
      return raw;
    },
    staleTime: debouncedFilters.query ? 0 : 60_000,
    placeholderData: (prev) => prev,
  });

  // isSearching: query is currently pending AND there is a non-empty search term
  const isSearching = isFetching && Boolean(decisionFilters.query);

  const decisions = useMemo(
    () => (data?.items ?? []).map(toDecisionNode),
    [data?.items]
  );

  const edges = useMemo(
    () => (data?.edges ?? []).map(toDecisionEdge),
    [data?.edges]
  );

  return { decisions, edges, isLoading, isSearching };
}
