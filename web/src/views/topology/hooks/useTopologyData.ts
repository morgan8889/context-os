import { useQuery } from '@tanstack/react-query';
import type { Node, Edge } from '@xyflow/react';
import dagre from '@dagrejs/dagre';
import { apiClient } from '@/lib/api/client';
import { workflowKeys } from '@/lib/api/queryKeys';
import { toWorkflowNode, toWorkflowEdge } from '@/lib/transforms/workflow';
import type { ApiWorkflow } from '@/types/api';
import type { WorkflowNode, WorkflowEdge, WorkflowSummary, WorkflowStatus } from '@/types/topology';

const NODE_WIDTH = 200;
const NODE_HEIGHT = 80;

interface DagreLayoutInput {
  nodes: Node<WorkflowNode>[];
  edges: Edge<WorkflowEdge>[];
}

/**
 * applyDagreLayout — positions React Flow nodes using Dagre's left-to-right layout.
 * Returns a new nodes array with x/y set; edges are unchanged.
 */
function applyDagreLayout({ nodes, edges }: DagreLayoutInput): Node<WorkflowNode>[] {
  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: 'LR', nodesep: 80, ranksep: 120 });
  g.setDefaultEdgeLabel(() => ({}));

  nodes.forEach((n) => g.setNode(n.id, { width: NODE_WIDTH, height: NODE_HEIGHT }));
  edges.forEach((e) => g.setEdge(e.source, e.target));

  dagre.layout(g);

  return nodes.map((n) => {
    const pos = g.node(n.id);
    return {
      ...n,
      position: {
        x: pos.x - NODE_WIDTH / 2,
        y: pos.y - NODE_HEIGHT / 2,
      },
    };
  });
}

/**
 * deriveWorkflowStatus — maps an ApiWorkflow's status to a WorkflowStatus
 * for display in the sidebar summary list.
 */
function deriveWorkflowStatus(raw: ApiWorkflow): WorkflowStatus {
  return raw.status;
}

function transformWorkflows(workflows: ApiWorkflow[]): {
  nodes: Node<WorkflowNode>[];
  edges: Edge<WorkflowEdge>[];
  summaries: WorkflowSummary[];
} {
  const rawNodes: Node<WorkflowNode>[] = [];
  const rawEdges: Edge<WorkflowEdge>[] = [];
  const summaries: WorkflowSummary[] = [];

  for (const workflow of workflows) {
    // Transform steps → WorkflowNode[]
    const stepNodes = workflow.steps.map((step) => toWorkflowNode(step));

    // Build React Flow nodes (position 0,0 before Dagre runs)
    for (const node of stepNodes) {
      rawNodes.push({
        id: node.id,
        type: 'workflowNode',
        position: { x: 0, y: 0 },
        data: node,
      });
    }

    // Transform edges → WorkflowEdge[]
    for (const rawEdge of workflow.edges) {
      const edge = toWorkflowEdge(rawEdge, stepNodes);
      rawEdges.push({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: 'bottleneckEdge',
        label: edge.label ?? undefined,
        data: edge,
      });
    }

    // Build summary
    summaries.push({
      id: workflow.id,
      name: workflow.name,
      ownerTeam: workflow.owner_team,
      nodeCount: workflow.steps.length,
      status: deriveWorkflowStatus(workflow),
      viewState: 'activated',
    });
  }

  // Apply Dagre layout to all nodes
  const laidOutNodes = applyDagreLayout({ nodes: rawNodes, edges: rawEdges });

  return { nodes: laidOutNodes, edges: rawEdges, summaries };
}

export interface UseTopologyDataResult {
  nodes: Node<WorkflowNode>[];
  edges: Edge<WorkflowEdge>[];
  workflows: WorkflowSummary[];
  rawWorkflows: ApiWorkflow[];
  isLoading: boolean;
  isError: boolean;
}

/**
 * useTopologyData — fetches workflow data and prepares it for React Flow.
 *
 * Performs server fetch once; all subsequent filter changes are client-side.
 * Dagre layout is applied synchronously after transform.
 */
export function useTopologyData(params?: {
  teamId?: string;
  initiativeId?: string;
}): UseTopologyDataResult {
  const query = useQuery({
    queryKey: workflowKeys.list(params),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWorkflow[]>('/api/v1/workflows', {
        params: {
          team_id: params?.teamId,
          initiative_id: params?.initiativeId,
        },
      });
      return data;
    },
    staleTime: 30_000,
  });

  if (!query.data) {
    return {
      nodes: [],
      edges: [],
      workflows: [],
      rawWorkflows: [],
      isLoading: query.isLoading,
      isError: query.isError,
    };
  }

  const { nodes, edges, summaries } = transformWorkflows(query.data);

  return {
    nodes,
    edges,
    workflows: summaries,
    rawWorkflows: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
  };
}
