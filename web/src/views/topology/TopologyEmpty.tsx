import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ReactFlow,
  ReactFlowProvider,
  type Node,
  type NodeTypes,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { WorkflowNode } from './WorkflowNode';
import { StateCTA } from '@/design-system/primitives/StateCTA';
import type { WorkflowNode as WorkflowNodeData } from '@/types/topology';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const NODE_TYPES: NodeTypes = { workflowNode: WorkflowNode as any };

const PLACEHOLDER_NODE: Node<WorkflowNodeData> = {
  id: 'executive-briefing',
  type: 'workflowNode',
  position: { x: 0, y: 0 },
  data: {
    id: 'executive-briefing',
    workflowId: 'executive-briefing',
    label: 'Executive Briefing',
    stepIndex: 0,
    status: 'active',
    ownerTeam: null,
    ownerActor: null,
    autonomyLevel: 0,
    latencyP50Ms: null,
    latencyP95Ms: null,
    isBottleneck: false,
    viewState: 'placeholder',
  },
};

/**
 * TopologyEmpty — shown when the topology view state is 'empty'.
 *
 * Renders a single placeholder WorkflowNode ("Executive Briefing") on a
 * ReactFlow canvas at reduced opacity, accompanied by explanatory copy
 * and a CTA to view the executive briefing workflow.
 */
export default function TopologyEmpty() {
  const navigate = useNavigate();

  return (
    <motion.div
      data-view="topology-empty"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3, ease: [0.0, 0, 0.2, 1] }}
      style={{ height: '100%', position: 'relative', display: 'flex', flexDirection: 'column', background: 'var(--color-galaxy-bg, oklch(8% 0 0))' }}
    >
      {/* ReactFlow canvas — fills space */}
      <div style={{ flex: 1, minHeight: 0 }}>
        <ReactFlowProvider>
          <ReactFlow
            nodes={[PLACEHOLDER_NODE]}
            edges={[]}
            nodeTypes={NODE_TYPES}
            fitView
            fitViewOptions={{ padding: 0.4 }}
            nodesDraggable={false}
            nodesConnectable={false}
            elementsSelectable={false}
            zoomOnScroll={false}
            panOnDrag={false}
            style={{ opacity: 0.4, background: 'var(--color-galaxy-bg, oklch(8% 0 0))' }}
          />
        </ReactFlowProvider>
      </div>

      {/* Overlay CTA */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1.5rem',
          pointerEvents: 'none',
          zIndex: 10,
        }}
      >
        <div style={{ pointerEvents: 'auto', maxWidth: 440, textAlign: 'center' }}>
          <p
            className="text-sm text-[oklch(65%_0_0)] leading-relaxed mb-4"
            style={{ padding: '0 1rem' }}
          >
            Workflows derive from your team's coordination patterns. Executive Briefing
            is active by default; others appear as patterns emerge.
          </p>
          <StateCTA
            label="View Executive Briefing"
            onClick={() => navigate('/inbox?filter=briefing')}
          />
        </div>
      </div>
    </motion.div>
  );
}
