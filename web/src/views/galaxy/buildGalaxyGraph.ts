import Graph from 'graphology';
import type { InitiativeNode, InitiativeEdge } from '@/types/galaxy';

/**
 * Build a graphology graph from initiative nodes and edges.
 *
 * Sigma reads the `type` attribute to select a rendering *program* (default
 * 'circle' for nodes, 'line' for edges). Domain types such as 'goal' or
 * 'depends_on' are NOT valid Sigma programs — setting them on `type` throws
 * "could not find a suitable program for node type ..." and crashes the
 * renderer. Domain type is therefore stored under `nodeType` / `edgeType`,
 * leaving Sigma's `type` unset so it falls back to the default program.
 */
export function buildGalaxyGraph(
  nodes: InitiativeNode[],
  edges: InitiativeEdge[]
): Graph {
  const graph = new Graph({ type: 'mixed', multi: false });

  for (const node of nodes) {
    if (graph.hasNode(node.id)) continue;
    graph.addNode(node.id, {
      label: node.label,
      x: node.x,
      y: node.y,
      size: node.size,
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

  for (const edge of edges) {
    if (
      graph.hasNode(edge.source) &&
      graph.hasNode(edge.target) &&
      !graph.hasEdge(edge.id)
    ) {
      graph.addEdgeWithKey(edge.id, edge.source, edge.target, {
        edgeType: edge.type,
        weight: edge.weight,
      });
    }
  }

  return graph;
}
