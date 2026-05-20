import { motion } from 'framer-motion';
import {
  ReactFlow,
  ReactFlowProvider,
  type Node,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { WorkflowNode } from './WorkflowNode';
import { StateCTA } from '@/design-system/primitives/StateCTA';
import type { WorkflowNode as WorkflowNodeData } from '@/types/topology';

const NODE_TYPES = { workflowNode: WorkflowNode };

/** Generates 4 anticipatory stub nodes to show "more workflows coming" */
function buildStubNodes(offset: number): Node<WorkflowNodeData>[] {
  const stubs: Array<{ label: string; x: number; y: number }> = [
    { label: 'Discovering…', x: offset + 320, y: -60 },
    { label: 'Discovering…', x: offset + 560, y: 20 },
    { label: 'Discovering…', x: offset + 320, y: 100 },
    { label: 'Discovering…', x: offset + 760, y: -40 },
  ];

  return stubs.map((s, i) => ({
    id: `stub-${i}`,
    type: 'workflowNode',
    position: { x: s.x, y: s.y },
    data: {
      id: `stub-${i}`,
      workflowId: `stub-${i}`,
      label: s.label,
      stepIndex: i,
      status: 'pending' as const,
      ownerTeam: null,
      ownerActor: null,
      autonomyLevel: 0,
      latencyP50Ms: null,
      latencyP95Ms: null,
      isBottleneck: false,
      viewState: 'placeholder' as const,
    },
  }));
}

interface TopologyActivatingProps {
  /** Number of fully-discovered workflows rendered at full fidelity. */
  workflowCount: number;
  /** Partial real React Flow nodes from discovered workflows. */
  partialNodes: Node<WorkflowNodeData>[];
}

/**
 * TopologyActivating — shown when topology view state is 'activating'.
 *
 * Renders real discovered workflow nodes at full fidelity, alongside
 * 4 anticipatory placeholder stub nodes that indicate more workflows
 * are being discovered. Shows progress copy and a CTA to scroll to
 * the first mapped workflow.
 */
export default function TopologyActivating({
  workflowCount,
  partialNodes,
}: TopologyActivatingProps) {
  // Calculate x offset so stubs appear after the last real node
  const maxX = partialNodes.reduce((max, n) => Math.max(max, n.position.x), 0);
  const stubNodes = buildStubNodes(maxX + 60);
  const allNodes: Node<WorkflowNodeData>[] = [...partialNodes, ...stubNodes];

  function handleCTAClick() {
    // Scroll to first mapped node — no-op when no nodes are present
    const firstNode = document.querySelector('[data-node-type="workflow-step"]');
    if (firstNode) {
      firstNode.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  return (
    <motion.div
      data-view="topology-activating"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3, ease: [0.0, 0, 0.2, 1] }}
      style={{ height: '100%', position: 'relative', display: 'flex', flexDirection: 'column' }}
    >
      {/* ReactFlow canvas with real + stub nodes */}
      <div style={{ flex: 1, minHeight: 0 }}>
        <ReactFlowProvider>
          <ReactFlow
            nodes={allNodes}
            edges={[]}
            nodeTypes={NODE_TYPES}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            nodesDraggable={false}
            nodesConnectable={false}
            elementsSelectable={false}
          />
        </ReactFlowProvider>
      </div>

      {/* Progress overlay banner */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15, duration: 0.25, ease: [0.0, 0, 0.2, 1] }}
        style={{
          position: 'absolute',
          top: '1rem',
          left: '50%',
          transform: 'translateX(-50%)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '0.75rem',
          pointerEvents: 'none',
        }}
      >
        <div
          className="px-4 py-2 rounded-full text-sm font-medium"
          style={{
            background: 'oklch(100% 0 0 / 90%)',
            border: '1px solid oklch(85% 0 0)',
            boxShadow: 'var(--shadow-panel)',
            backdropFilter: 'blur(8px)',
            color: 'oklch(30% 0 0)',
            pointerEvents: 'auto',
          }}
        >
          {workflowCount} workflow{workflowCount !== 1 ? 's' : ''} mapped —
          exploring more coordination patterns…
        </div>

        <div style={{ pointerEvents: 'auto' }}>
          <StateCTA
            label="See what's been discovered"
            onClick={handleCTAClick}
          />
        </div>
      </motion.div>
    </motion.div>
  );
}
