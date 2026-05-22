import { useEffect } from 'react';
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import Graph from 'graphology';
import { apiClient } from '@/lib/api/client';
import { graphKeys } from '@/lib/api/queryKeys';
import { toInitiativeNode, toInitiativeEdge } from '@/lib/transforms/initiative';
import { useGraphInteractionStore } from '@/lib/stores/graphInteraction';
import type { ApiNode, ApiEdge, ApiGraphSnapshot, PaginatedResponse } from '@/types/api';
import type { InitiativeNode, InitiativeEdge, GalaxySnapshot } from '@/types/galaxy';

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

  // Build graphology graph from all fetched pages
  const graph = new Graph({ type: 'mixed', multi: false });

  const allNodePages = nodesQuery.data?.pages ?? [];
  const allEdges: InitiativeEdge[] = [];

  // Collect all nodes across pages
  const allNodes: InitiativeNode[] = [];
  for (const page of allNodePages) {
    for (const raw of page.items) {
      allNodes.push(toInitiativeNode(raw));
    }
  }

  // Collect all edges
  if (edgesQuery.data) {
    for (const raw of edgesQuery.data.items) {
      allEdges.push(toInitiativeEdge(raw));
    }
  }

  // Add nodes to graphology graph
  for (const node of allNodes) {
    if (!graph.hasNode(node.id)) {
      graph.addNode(node.id, {
        label: node.label,
        x: node.x,
        y: node.y,
        size: node.size,
        // Sigma reads 'type' as a rendering program name; use 'nodeType' for
        // the semantic type (goal/project/signal/artifact) so nodeReducer can
        // map it to a color without triggering an unknown-program error.
        type: 'circle',
        nodeType: node.type,
        status: node.status,
        ownerTeam: node.ownerTeam,
        actorCount: node.actorCount,
        riskScore: node.riskScore,
        autonomyLevel: node.autonomyLevel,
        edgeCount: node.edgeCount,
        viewState: node.viewState,
      });
    }
  }

  // Add edges to graphology graph
  for (const edge of allEdges) {
    if (
      graph.hasNode(edge.source) &&
      graph.hasNode(edge.target) &&
      !graph.hasEdge(edge.id)
    ) {
      graph.addEdgeWithKey(edge.id, edge.source, edge.target, {
        type: 'line',
        edgeType: edge.type,
        weight: edge.weight,
      });
    }
  }

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
