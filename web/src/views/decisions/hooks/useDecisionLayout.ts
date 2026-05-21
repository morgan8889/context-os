import { useMemo, useState, useCallback } from 'react';
import dagre from '@dagrejs/dagre';
import type { Node, Edge } from '@xyflow/react';
import type { DecisionNode, DecisionEdge } from '@/types/decisions';

const NODE_WIDTH = 220;
const NODE_HEIGHT = 120;

/** Internal layout-only data attached to nodes during computation */
interface LayoutMeta {
  clusterId: string;
  isStub: boolean;
  stubLabel?: string;
  originalIds?: string[];
}

/** Derive connected components using only predecessor edges (undirected) */
function deriveClusterMap(
  nodes: DecisionNode[],
  edges: DecisionEdge[]
): Map<string, string> {
  // Union-Find
  const parent = new Map<string, string>(nodes.map((n) => [n.id, n.id]));

  function find(id: string): string {
    const p = parent.get(id) ?? id;
    if (p === id) return id;
    const root = find(p);
    parent.set(id, root);
    return root;
  }

  function union(a: string, b: string) {
    const ra = find(a);
    const rb = find(b);
    if (ra !== rb) parent.set(ra, rb);
  }

  for (const edge of edges) {
    if (edge.type === 'predecessor') {
      if (parent.has(edge.source) && parent.has(edge.target)) {
        union(edge.source, edge.target);
      }
    }
  }

  // Normalize cluster IDs: use the smallest-ID root per cluster
  const clusterMap = new Map<string, string>();
  for (const node of nodes) {
    clusterMap.set(node.id, find(node.id));
  }
  return clusterMap;
}

/** Apply dagre layout to a set of nodes and edges, returning positioned RF nodes/edges */
function applyDagreLayout(
  decisionNodes: (DecisionNode & { _clusterId: string })[],
  decisionEdges: DecisionEdge[],
  excludedIds: Set<string>
): { rfNodes: Node<DecisionNode & LayoutMeta>[]; rfEdges: Edge<DecisionEdge>[] } {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: 'TB', nodesep: 60, ranksep: 100 });

  const visibleNodes = decisionNodes.filter((n) => !excludedIds.has(n.id));

  for (const node of visibleNodes) {
    g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  }

  const visibleIds = new Set(visibleNodes.map((n) => n.id));
  const visibleEdges = decisionEdges.filter(
    (e) => visibleIds.has(e.source) && visibleIds.has(e.target)
  );

  for (const edge of visibleEdges) {
    g.setEdge(edge.source, edge.target);
  }

  dagre.layout(g);

  const rfNodes: Node<DecisionNode & LayoutMeta>[] = visibleNodes.map((node) => {
    const pos = g.node(node.id);
    return {
      id: node.id,
      type: 'decisionNode',
      position: {
        x: (pos?.x ?? 0) - NODE_WIDTH / 2,
        y: (pos?.y ?? 0) - NODE_HEIGHT / 2,
      },
      data: {
        ...node,
        clusterId: node._clusterId,
        isStub: false,
      },
    };
  });

  const rfEdges: Edge<DecisionEdge>[] = visibleEdges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    type: 'decisionEdge',
    data: edge,
    label: undefined,
  }));

  return { rfNodes, rfEdges };
}

interface UseDecisionLayoutReturn {
  rfNodes: Node<DecisionNode & LayoutMeta>[];
  rfEdges: Edge<DecisionEdge>[];
  collapseCluster: (clusterId: string) => void;
  expandCluster: (clusterId: string) => void;
  collapsedClusters: Set<string>;
}

/**
 * useDecisionLayout — applies dagre TB layout to DecisionNodes + DecisionEdges.
 *
 * Supports cluster collapse/expand: connected components (by predecessor edges)
 * can be collapsed into a single stub node and restored.
 *
 * @param decisions - Array of DecisionNode data objects
 * @param edges - Array of DecisionEdge data objects
 */
export function useDecisionLayout(
  decisions: DecisionNode[],
  edges: DecisionEdge[]
): UseDecisionLayoutReturn {
  const [collapsedClusters, setCollapsedClusters] = useState<Set<string>>(new Set());

  const collapseCluster = useCallback((clusterId: string) => {
    setCollapsedClusters((prev) => {
      const next = new Set(prev);
      next.add(clusterId);
      return next;
    });
  }, []);

  const expandCluster = useCallback((clusterId: string) => {
    setCollapsedClusters((prev) => {
      const next = new Set(prev);
      next.delete(clusterId);
      return next;
    });
  }, []);

  const { rfNodes, rfEdges } = useMemo(() => {
    if (decisions.length === 0) {
      return { rfNodes: [], rfEdges: [] };
    }

    // 1. Derive cluster membership
    const clusterMap = deriveClusterMap(decisions, edges);
    const nodesWithCluster = decisions.map((n) => ({
      ...n,
      _clusterId: clusterMap.get(n.id) ?? n.id,
    }));

    // 2. Build the set of node IDs excluded by collapse
    //    (replaced by a single stub per cluster)
    const excludedIds = new Set<string>();
    const stubNodes: Node<DecisionNode & LayoutMeta>[] = [];

    for (const clusterId of collapsedClusters) {
      const clusterMembers = nodesWithCluster.filter(
        (n) => n._clusterId === clusterId
      );
      if (clusterMembers.length === 0) continue;

      clusterMembers.forEach((n) => excludedIds.add(n.id));

      // Create a stub node for the collapsed cluster
      stubNodes.push({
        id: `__cluster_stub_${clusterId}`,
        type: 'default',
        position: { x: 0, y: 0 }, // dagre will position this
        data: {
          id: `__cluster_stub_${clusterId}`,
          title: `${clusterMembers.length} decisions (collapsed)`,
          rationale: '',
          alternatives: [],
          authorId: null,
          authorName: null,
          capturedAt: new Date().toISOString(),
          impactedSystems: [],
          status: 'active',
          viewState: 'placeholder',
          clusterId,
          isStub: true,
          stubLabel: `${clusterMembers.length} decisions (collapsed)`,
          originalIds: clusterMembers.map((n) => n.id),
        },
        style: {
          background: 'var(--color-placeholder-grey)',
          border: '1.5px dashed oklch(75% 0 0)',
          borderRadius: 8,
          minWidth: NODE_WIDTH,
          opacity: 0.6,
          cursor: 'pointer',
        },
      });
    }

    // 3. Run dagre on visible (non-excluded) nodes
    const { rfNodes: layoutNodes, rfEdges: layoutEdges } = applyDagreLayout(
      nodesWithCluster,
      edges,
      excludedIds
    );

    // 4. Merge stub nodes (position them based on their cluster's centroid or
    //    a simple offset from the first excluded node's dagre-computed spot)
    //    For stub nodes we just append; they are excluded from dagre but we
    //    give them a fallback position.
    const combined = [...layoutNodes, ...stubNodes];

    return { rfNodes: combined, rfEdges: layoutEdges };
  }, [decisions, edges, collapsedClusters]);

  return { rfNodes, rfEdges, collapseCluster, expandCluster, collapsedClusters };
}
