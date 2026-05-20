import { ReactFlow, ReactFlowProvider, Background, BackgroundVariant } from '@xyflow/react';
import type { Node } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { StateCTA } from '@/design-system/primitives/StateCTA';
import type { DecisionNode } from '@/types/decisions';
import { DecisionNodeComponent } from './DecisionNode';

const nodeTypes = {
  decisionNode: DecisionNodeComponent,
};

/** A single stub node positioned pseudo-randomly within the canvas */
function buildStubNodes(count: number, startIndex: number): Node[] {
  return Array.from({ length: count }, (_, i) => ({
    id: `__stub_${startIndex + i}`,
    type: 'default',
    position: {
      x: 60 + ((startIndex + i) % 5) * 260,
      y: 60 + Math.floor((startIndex + i) / 5) * 160,
    },
    data: {},
    style: {
      width: 220,
      minHeight: 80,
      background: 'var(--color-placeholder-grey)',
      border: '1.5px dashed oklch(75% 0 0)',
      borderRadius: 8,
      opacity: 0.4,
    },
    selectable: false,
    connectable: false,
    draggable: false,
  }));
}

interface DecisionActivatingProps {
  /** Number of fully-captured decisions so far */
  decisionCount: number;
  /** Partial ReactFlow nodes for decisions already captured */
  partialNodes: Node<DecisionNode>[];
}

/**
 * DecisionActivating — shown when the decision graph view state is 'activating'.
 *
 * Renders captured DecisionNodes at full fidelity alongside placeholder stub
 * nodes (placeholder-grey, dashed border, 40% opacity) for decisions still
 * being processed, plus a status overlay and notification CTA.
 */
export default function DecisionActivating({
  decisionCount,
  partialNodes,
}: DecisionActivatingProps) {
  const stubCount = Math.max(0, 6 - partialNodes.length);
  const stubNodes = buildStubNodes(stubCount, partialNodes.length);
  const allNodes: Node[] = [...(partialNodes as Node[]), ...stubNodes];

  return (
    <div
      data-state="activating"
      className="relative flex h-full w-full flex-col overflow-hidden bg-[oklch(98%_0_0)]"
    >
      {/* Status overlay */}
      <div className="pointer-events-none absolute inset-x-0 top-4 z-10 flex justify-center">
        <div
          className="rounded-full px-4 py-1.5 text-sm font-medium"
          style={{
            background: 'oklch(97% 0 0 / 0.9)',
            color: 'oklch(35% 0 0)',
            border: '1px solid oklch(88% 0 0)',
            backdropFilter: 'blur(8px)',
          }}
        >
          {decisionCount} decisions captured — discovering more from your sources&hellip;
        </div>
      </div>

      {/* React Flow canvas with partial nodes + stubs */}
      <ReactFlowProvider>
        <div className="flex-1">
          <ReactFlow
            nodes={allNodes}
            edges={[]}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            nodesDraggable={false}
            nodesConnectable={false}
            elementsSelectable={false}
            zoomOnScroll={false}
            panOnScroll={true}
            attributionPosition="bottom-right"
          >
            <Background
              variant={BackgroundVariant.Dots}
              gap={24}
              size={1}
              color="oklch(88% 0 0)"
            />
          </ReactFlow>
        </div>
      </ReactFlowProvider>

      {/* Bottom CTA */}
      <div className="absolute bottom-6 inset-x-0 flex justify-center pointer-events-none">
        <div className="pointer-events-auto">
          <StateCTA
            label="Stay current on decisions"
            onClick={() => {
              /* notification subscription — wired in Phase 7 */
            }}
          />
        </div>
      </div>
    </div>
  );
}
