import { useRef, useCallback, useMemo } from 'react';
import { motion } from 'framer-motion';
import { useGSAP } from '@gsap/react';
import {
  ReactFlow,
  ReactFlowProvider,
  MiniMap,
  Controls,
  useReactFlow,
  type Node,
  type NodeTypes,
  type EdgeTypes,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { useGraphInteractionStore } from '@/lib/stores/graphInteraction';
import { animateStateEnter } from '@/lib/animations/stateTransitions';
import { useTopologyData } from './hooks/useTopologyData';
import { useTopologyFilters } from './hooks/useTopologyFilters';
import TopologyEmpty from './TopologyEmpty';
import TopologyActivating from './TopologyActivating';
import { WorkflowNode } from './WorkflowNode';
import { BottleneckEdge } from './BottleneckEdge';
import { TopologyFilters } from './TopologyFilters';
import type { WorkflowNode as WorkflowNodeData, WorkflowSummary } from '@/types/topology';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const NODE_TYPES: NodeTypes = { workflowNode: WorkflowNode as any };
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const EDGE_TYPES: EdgeTypes = { bottleneckEdge: BottleneckEdge as any };

const STATUS_COLORS: Record<string, string> = {
  healthy: 'var(--color-status-healthy)',
  degraded: 'var(--color-status-degraded)',
  blocked: 'var(--color-status-blocked)',
};

/** WorkflowSidebarItem — one row in the right sidebar workflow list. */
function WorkflowSidebarItem({
  workflow,
  onFocus,
}: {
  workflow: WorkflowSummary;
  onFocus: (id: string) => void;
}) {
  return (
    <motion.button
      onClick={() => onFocus(workflow.id)}
      whileHover={{ x: 2 }}
      transition={{ duration: 0.1 }}
      className="w-full text-left flex items-start gap-2.5 px-3 py-2.5 rounded-lg border border-transparent hover:border-[oklch(85%_0_0)] hover:bg-[oklch(97%_0_0)] transition-colors duration-[var(--motion-duration-everyday)]"
    >
      <span
        className="mt-0.5 w-2 h-2 rounded-full shrink-0"
        style={{ background: STATUS_COLORS[workflow.status] ?? 'oklch(65%_0_0)' }}
        aria-label={`Status: ${workflow.status}`}
      />
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium text-[oklch(15%_0_0)] truncate">{workflow.name}</p>
        {workflow.ownerTeam && (
          <p className="text-[10px] text-[oklch(55%_0_0)] truncate">{workflow.ownerTeam}</p>
        )}
        <p className="text-[10px] text-[oklch(65%_0_0)] mt-0.5">
          {workflow.nodeCount} step{workflow.nodeCount !== 1 ? 's' : ''}
        </p>
      </div>
    </motion.button>
  );
}

/**
 * ActivatedTopologyCanvas — the full React Flow canvas for the 'activated' state.
 * Separated so it can use the `useReactFlow` hook inside a ReactFlowProvider.
 */
function ActivatedTopologyCanvas({
  nodes,
  edges,
  workflows,
  filteredWorkflowIds,
}: {
  nodes: Node<WorkflowNodeData>[];
  edges: ReturnType<typeof useTopologyData>['edges'];
  workflows: WorkflowSummary[];
  filteredWorkflowIds: Set<string>;
}) {
  const { fitView } = useReactFlow();

  // Filter nodes to only those belonging to workflows that pass the filter
  const visibleNodes = useMemo(
    () =>
      filteredWorkflowIds.size === 0
        ? nodes
        : nodes.filter((n) => filteredWorkflowIds.has(n.data.workflowId)),
    [nodes, filteredWorkflowIds]
  );

  const visibleNodeIds = useMemo(
    () => new Set(visibleNodes.map((n) => n.id)),
    [visibleNodes]
  );

  const visibleEdges = useMemo(
    () =>
      edges.filter(
        (e) => visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target)
      ),
    [edges, visibleNodeIds]
  );

  const handleFocusWorkflow = useCallback(
    (workflowId: string) => {
      const workflowNodeIds = visibleNodes
        .filter((n) => n.data.workflowId === workflowId)
        .map((n) => ({ id: n.id }));
      if (workflowNodeIds.length > 0) {
        fitView({ nodes: workflowNodeIds, duration: 400, padding: 0.3 });
      }
    },
    [visibleNodes, fitView]
  );

  return (
    <div
      data-view="topology-activated"
      style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
    >
      {/*
       * Responsive sidebar styles:
       *  768–1024px (tablet): sidebar narrows from 240px → 180px
       *  ≤767px: sidebar stacks below canvas (column layout)
       */}
      <style>{`
        @media (min-width: 768px) and (max-width: 1024px) {
          [data-testid="topology-sidebar"] { width: 180px !important; }
        }
        @media (max-width: 767px) {
          [data-topology-canvas-row] { flex-direction: column !important; }
          [data-testid="topology-sidebar"] { width: 100% !important; max-height: 200px; border-left: none !important; border-top: 1px solid oklch(88% 0 0); }
        }
      `}</style>

      {/* Filter toolbar */}
      <TopologyFilters workflows={workflows} />

      {/* Main canvas + sidebar */}
      <div data-topology-canvas-row style={{ flex: 1, minHeight: 0, display: 'flex' }}>
        {/* React Flow canvas */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <ReactFlow
            nodes={visibleNodes}
            edges={visibleEdges}
            nodeTypes={NODE_TYPES}
            edgeTypes={EDGE_TYPES}
            fitView
            fitViewOptions={{ padding: 0.15 }}
            nodesDraggable
            nodesConnectable={false}
            elementsSelectable
          >
            <MiniMap
              nodeColor={(n) => {
                const data = n.data as WorkflowNodeData | undefined;
                if (data?.isBottleneck) return 'oklch(70% 0.22 55)';
                const statusMap: Record<string, string> = {
                  active: 'oklch(72% 0.2 145)',
                  blocked: 'oklch(55% 0.22 25)',
                  complete: 'oklch(65% 0 0)',
                  pending: 'oklch(75% 0.15 75)',
                };
                return statusMap[data?.status ?? ''] ?? 'oklch(80% 0 0)';
              }}
              style={{ background: 'oklch(97% 0 0)' }}
            />
            <Controls showInteractive={false} />
          </ReactFlow>
        </div>

        {/* Workflow summary sidebar */}
        <aside
          data-testid="topology-sidebar"
          style={{
            width: 240,
            flexShrink: 0,
            borderLeft: '1px solid oklch(88% 0 0)',
            background: 'oklch(99% 0 0)',
            display: 'flex',
            flexDirection: 'column',
            overflowY: 'auto',
          }}
          aria-label="Workflow list"
        >
          <div className="px-3 pt-3 pb-2 border-b border-[oklch(88%_0_0)]">
            <p className="text-xs font-semibold text-[oklch(40%_0_0)] uppercase tracking-wide">
              Workflows ({workflows.length})
            </p>
          </div>

          <div className="flex flex-col gap-0.5 p-1.5">
            {workflows.map((wf) => (
              <WorkflowSidebarItem
                key={wf.id}
                workflow={wf}
                onFocus={handleFocusWorkflow}
              />
            ))}

            {workflows.length === 0 && (
              <p className="text-xs text-[oklch(60%_0_0)] px-3 py-2 text-center">
                No workflows match the current filters.
              </p>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}

/** LoadingState — shown while topology data is fetching. */
function LoadingState() {
  return (
    <div
      style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
    >
      <div className="flex flex-col items-center gap-3">
        <div
          className="w-8 h-8 rounded-full border-2 border-[oklch(75%_0_0)] border-t-[oklch(40%_0_0)] animate-spin"
          aria-label="Loading topology"
        />
        <p className="text-sm text-[oklch(50%_0_0)]">Loading workflows…</p>
      </div>
    </div>
  );
}

/**
 * TopologyView — top-level container for the Topology view.
 *
 * Routes to TopologyEmpty, TopologyActivating, or the full activated
 * React Flow canvas based on the viewState from Zustand.
 *
 * Data is fetched once on mount. Filter changes are client-side only.
 */
export default function TopologyView() {
  const viewStates = useGraphInteractionStore((s) => s.viewStates);
  const topologyViewState = viewStates.topology.state;
  const workflowCount = viewStates.topology.workflowCount;

  const { nodes, edges, workflows, rawWorkflows, isLoading } = useTopologyData();
  const { topologyFilters, filterWorkflows } = useTopologyFilters();

  // Derive the set of workflow IDs that pass the current filters
  const filteredWorkflowIds = useMemo(() => {
    if (!rawWorkflows.length) return new Set<string>();
    const filtered = filterWorkflows(rawWorkflows, topologyFilters);
    return new Set(filtered.map((w) => w.id));
  }, [rawWorkflows, topologyFilters, filterWorkflows]);

  const containerRef = useRef<HTMLDivElement>(null);
  const prevStateRef = useRef(topologyViewState);

  // GSAP set-piece entrance animation on state change
  useGSAP(() => {
    if (!containerRef.current) return;
    if (prevStateRef.current === topologyViewState) return;
    prevStateRef.current = topologyViewState;
    animateStateEnter(containerRef.current);
  }, { scope: containerRef, dependencies: [topologyViewState] });

  return (
    <div
      ref={containerRef}
      data-view={`topology-${topologyViewState}`}
      className="relative flex h-full w-full flex-col overflow-hidden bg-white"
    >
      {topologyViewState === 'empty' && <TopologyEmpty />}

      {topologyViewState === 'activating' && (
        isLoading ? <LoadingState /> : (
          <TopologyActivating workflowCount={workflowCount} partialNodes={nodes} />
        )
      )}

      {topologyViewState === 'activated' && (
        isLoading ? <LoadingState /> : (
          <ReactFlowProvider>
            <ActivatedTopologyCanvas
              nodes={nodes}
              edges={edges}
              workflows={workflows}
              filteredWorkflowIds={filteredWorkflowIds}
            />
          </ReactFlowProvider>
        )
      )}
    </div>
  );
}
