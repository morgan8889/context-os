import { useEffect, useMemo } from 'react';
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import Graph from 'graphology';
import { apiClient } from '@/lib/api/client';
import { graphKeys } from '@/lib/api/queryKeys';
import { toInitiativeNode, toInitiativeEdge } from '@/lib/transforms/initiative';
import { buildGalaxyGraph } from '@/views/galaxy/buildGalaxyGraph';
import { useGraphInteractionStore } from '@/lib/stores/graphInteraction';
import type { ApiNode, ApiEdge, ApiGraphSnapshot, PaginatedResponse } from '@/types/api';
import type { InitiativeNode, InitiativeEdge, GalaxySnapshot } from '@/types/galaxy';

const NODE_TYPES = ['goal', 'project', 'signal', 'artifact'] as const;
const NODE_STATUSES = ['active', 'paused', 'at_risk', 'complete'] as const;

/** Generate N random InitiativeNodes for benchmark/mock purposes */
function generateMockNodes(n: number): InitiativeNode[] {
  return Array.from({ length: n }, (_, i) => ({
    id: `mock-${i}`,
    label: `Node ${i}`,
    type: NODE_TYPES[i % NODE_TYPES.length]!,
    status: NODE_STATUSES[i % NODE_STATUSES.length]!,
    ownerTeam: null,
    actorCount: Math.floor(Math.random() * 10),
    riskScore: Math.random(),
    autonomyLevel: Math.floor(Math.random() * 5),
    edgeCount: 0,
    x: (Math.random() - 0.5) * 1000,
    y: (Math.random() - 0.5) * 1000,
    size: 6 + Math.random() * 6,
    viewState: 'activated' as const,
  }));
}

interface UseGalaxyGraphResult {
  graph: Graph;
  isLoading: boolean;
  isFetchingNextPage: boolean;
  fetchNextPage: () => void;
  hasNextPage: boolean;
}

/**
 * useGalaxyGraph — fetches and manages the galaxy graph data.
 *
 * - Paginated fetch of nodes via GET /api/v1/graph/nodes?cursor=...
 * - Fetches snapshots and stores in Zustand via setGalaxySnapshots
 * - Returns a graphology Graph instance with InitiativeNode attributes
 */
export function useGalaxyGraph(): UseGalaxyGraphResult {
  const setGalaxySnapshots = useGraphInteractionStore((s) => s.setGalaxySnapshots);

  const benchmarkNodes = (() => {
    if (typeof window === 'undefined') return 0;
    const params = new URLSearchParams(window.location.search);
    const mock = params.get('mock');
    const n = parseInt(params.get('nodes') ?? '0', 10);
    return mock && n > 0 ? n : 0;
  })();

  // Generate the benchmark graph ONCE (memoized) — regenerating every render
  // would thrash ForceLayout and freeze the page with large node counts.
  const benchmarkGraph = useMemo(() => {
    if (benchmarkNodes <= 0) return null;
    return buildGalaxyGraph(generateMockNodes(benchmarkNodes), []);
  }, [benchmarkNodes]);

  // Paginated nodes query
  const nodesQuery = useInfiniteQuery({
    queryKey: graphKeys.nodes(),
    queryFn: async ({ pageParam }) => {
      const params: Record<string, string> = {};
      if (pageParam) {
        params['cursor'] = pageParam as string;
      }
      const { data } = await apiClient.get<PaginatedResponse<ApiNode>>(
        '/api/v1/graph/nodes',
        { params }
      );
      return data;
    },
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
  });

  // Edges query (non-paginated for now; load all)
  const edgesQuery = useQuery({
    queryKey: graphKeys.edges(),
    queryFn: async () => {
      const { data } = await apiClient.get<PaginatedResponse<ApiEdge>>(
        '/api/v1/graph/edges'
      );
      return data;
    },
  });

  // Snapshots query
  const snapshotsQuery = useQuery({
    queryKey: graphKeys.snapshots(),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiGraphSnapshot[]>(
        '/api/v1/graph/snapshots'
      );
      return data;
    },
  });

  // Push snapshots into Zustand store
  useEffect(() => {
    if (snapshotsQuery.data) {
      const mapped: GalaxySnapshot[] = snapshotsQuery.data.map((raw) => ({
        timestamp: raw.timestamp,
        layoutSeed: raw.layout_seed,
        nodes: raw.nodes.map(toInitiativeNode),
        edges: raw.edges.map(toInitiativeEdge),
      }));
      setGalaxySnapshots(mapped);
    }
  }, [snapshotsQuery.data, setGalaxySnapshots]);

  // Benchmark / mock: return generated nodes if ?mock=<state>&nodes=N is set
  if (benchmarkGraph) {
    return { graph: benchmarkGraph, isLoading: false, isFetchingNextPage: false, fetchNextPage: () => {}, hasNextPage: false };
  }

  // Collect all nodes across pages
  const allNodePages = nodesQuery.data?.pages ?? [];
  const allNodes: InitiativeNode[] = [];
  for (const page of allNodePages) {
    for (const raw of page.items) {
      allNodes.push(toInitiativeNode(raw));
    }
  }

  // Collect all edges
  const allEdges: InitiativeEdge[] = [];
  if (edgesQuery.data) {
    for (const raw of edgesQuery.data.items) {
      allEdges.push(toInitiativeEdge(raw));
    }
  }

  const graph = buildGalaxyGraph(allNodes, allEdges);

  return {
    graph,
    isLoading: nodesQuery.isLoading,
    isFetchingNextPage: nodesQuery.isFetchingNextPage,
    fetchNextPage: () => {
      if (nodesQuery.hasNextPage && !nodesQuery.isFetchingNextPage) {
        void nodesQuery.fetchNextPage();
      }
    },
    hasNextPage: nodesQuery.hasNextPage ?? false,
  };
}
