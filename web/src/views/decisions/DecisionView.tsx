import { useState, useCallback, useRef } from 'react';
import type { MouseEvent as ReactMouseEvent } from 'react';
import { useGSAP } from '@gsap/react';
import {
  ReactFlow,
  ReactFlowProvider,
  MiniMap,
  Controls,
  Background,
  BackgroundVariant,
} from '@xyflow/react';
import type { NodeTypes, EdgeTypes } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useGraphInteractionStore } from '@/lib/stores/graphInteraction';
import { animateStateEnter } from '@/lib/animations/stateTransitions';
import { useViewState } from '@/lib/api/viewState';
import { OverlayPanel } from '@/design-system/primitives/OverlayPanel';
import { useDecisionGraph } from './hooks/useDecisionGraph';
import { useDecisionLayout } from './hooks/useDecisionLayout';
import { DecisionNodeComponent } from './DecisionNode';
import { DecisionEdgeComponent } from './DecisionEdge';
import { DecisionSearch } from './DecisionSearch';
import { DecisionFilters } from './DecisionFilters';
import DecisionEmpty from './DecisionEmpty';
import DecisionActivating from './DecisionActivating';
import type { DecisionNode } from '@/types/decisions';
import type { Node } from '@xyflow/react';

// ── Node and edge type registrations ────────────────────────────────────────

const nodeTypes: NodeTypes = {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  decisionNode: DecisionNodeComponent as any,
};

const edgeTypes: EdgeTypes = {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  decisionEdge: DecisionEdgeComponent as any,
};

// ── Decision detail panel ────────────────────────────────────────────────────

function DecisionDetailPanel({
  decision,
  onClose,
}: {
  decision: DecisionNode;
  onClose: () => void;
}) {
  return (
    <OverlayPanel open title={decision.title} onClose={onClose}>
      <div className="flex flex-col gap-4 text-sm">
        {/* Status */}
        <div>
          <p
            className="text-xs font-semibold uppercase tracking-wider mb-1"
            style={{ color: 'oklch(55% 0 0)' }}
          >
            Status
          </p>
          <span
            className="inline-block rounded-full px-2.5 py-0.5 text-xs font-medium"
            style={{
              background:
                decision.status === 'active'
                  ? 'oklch(95% 0.04 145)'
                  : 'oklch(96% 0 0)',
              color:
                decision.status === 'active'
                  ? 'oklch(35% 0.12 145)'
                  : 'oklch(55% 0 0)',
              border:
                decision.status === 'active'
                  ? '1.5px solid oklch(65% 0.15 145)'
                  : '1.5px solid oklch(78% 0 0)',
            }}
          >
            {decision.status}
          </span>
        </div>

        {/* Rationale */}
        <div>
          <p
            className="text-xs font-semibold uppercase tracking-wider mb-1"
            style={{ color: 'oklch(55% 0 0)' }}
          >
            Rationale
          </p>
          <p
            className="leading-relaxed"
            style={{ color: 'oklch(25% 0 0)' }}
          >
            {decision.rationale}
          </p>
        </div>

        {/* Alternatives */}
        {decision.alternatives.length > 0 && (
          <div>
            <p
              className="text-xs font-semibold uppercase tracking-wider mb-2"
              style={{ color: 'oklch(55% 0 0)' }}
            >
              Alternatives considered
            </p>
            <ul className="flex flex-col gap-2">
              {decision.alternatives.map((alt, i) => (
                <li
                  key={i}
                  className="rounded-lg p-2.5"
                  style={{
                    background: 'oklch(97% 0 0)',
                    border: '1px solid oklch(91% 0 0)',
                  }}
                >
                  <p className="font-semibold" style={{ color: 'oklch(20% 0 0)' }}>
                    {alt.label}
                  </p>
                  {alt.reason && (
                    <p className="text-xs mt-0.5" style={{ color: 'oklch(50% 0 0)' }}>
                      {alt.reason}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Author */}
        {decision.authorName && (
          <div>
            <p
              className="text-xs font-semibold uppercase tracking-wider mb-1"
              style={{ color: 'oklch(55% 0 0)' }}
            >
              Author
            </p>
            <p style={{ color: 'oklch(25% 0 0)' }}>{decision.authorName}</p>
          </div>
        )}

        {/* Captured date */}
        <div>
          <p
            className="text-xs font-semibold uppercase tracking-wider mb-1"
            style={{ color: 'oklch(55% 0 0)' }}
          >
            Captured
          </p>
          <p style={{ color: 'oklch(35% 0 0)' }}>
            {new Date(decision.capturedAt).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </p>
        </div>

        {/* Impacted systems */}
        {decision.impactedSystems.length > 0 && (
          <div>
            <p
              className="text-xs font-semibold uppercase tracking-wider mb-2"
              style={{ color: 'oklch(55% 0 0)' }}
            >
              Impacted systems
            </p>
            <div className="flex flex-wrap gap-1.5">
              {decision.impactedSystems.map((sys) => (
                <span
                  key={sys}
                  className="inline-block rounded-full px-2.5 py-0.5 text-xs font-medium"
                  style={{
                    background: 'oklch(93% 0.02 220)',
                    color: 'oklch(40% 0.08 220)',
                    border: '1px solid oklch(85% 0.04 220)',
                  }}
                >
                  {sys}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </OverlayPanel>
  );
}

// ── Activated view (full React Flow graph) ───────────────────────────────────

function ActivatedDecisionGraph() {
  const focusedDecisionId = useGraphInteractionStore((s) => s.focusedDecisionId);
  const setFocusedDecisionId = useGraphInteractionStore((s) => s.setFocusedDecisionId);
  const [showFilters, setShowFilters] = useState(false);

  const { decisions, edges, isLoading, isSearching } = useDecisionGraph();
  const { rfNodes, rfEdges } = useDecisionLayout(decisions, edges);

  const focusedDecision = focusedDecisionId
    ? decisions.find((d) => d.id === focusedDecisionId) ?? null
    : null;

  const handleNodeClick = useCallback(
    (_: ReactMouseEvent, node: Node) => {
      setFocusedDecisionId(node.id);
    },
    [setFocusedDecisionId]
  );

  const handlePaneClick = useCallback(() => {
    setFocusedDecisionId(null);
  }, [setFocusedDecisionId]);

  return (
    <div
      data-state="activated"
      className="flex h-full w-full flex-col overflow-hidden"
      style={{ background: 'oklch(98% 0 0)' }}
    >
      {/* Top bar */}
      <div
        className="flex items-center gap-3 px-4 py-2.5 shrink-0"
        style={{
          borderBottom: '1px solid oklch(90% 0 0)',
          background: 'oklch(100% 0 0)',
        }}
      >
        <DecisionSearch isSearching={isSearching} resultCount={decisions.length} />

        <button
          onClick={() => setShowFilters((v) => !v)}
          className={[
            'ml-auto flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium',
            'border transition-colors duration-[var(--motion-duration-everyday)]',
            'focus-visible:outline-none focus-visible:ring-2',
          ].join(' ')}
          style={{
            borderColor: showFilters ? 'oklch(60% 0.15 220)' : 'oklch(82% 0 0)',
            background: showFilters ? 'oklch(93% 0.02 220)' : 'oklch(100% 0 0)',
            color: showFilters ? 'oklch(40% 0.1 220)' : 'oklch(40% 0 0)',
          }}
          aria-pressed={showFilters}
          aria-label="Toggle filters"
        >
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
            <path
              d="M1 3h10M3 6h6M5 9h2"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
          Filters
        </button>
      </div>

      {/* Collapsible filter panel */}
      {showFilters && <DecisionFilters decisions={decisions} />}

      {/* React Flow canvas */}
      <div className="flex-1 relative">
        {isLoading && (
          <div
            className="absolute inset-0 z-10 flex items-center justify-center"
            style={{ background: 'oklch(98% 0 0 / 0.7)' }}
          >
            <span className="text-sm" style={{ color: 'oklch(50% 0 0)' }}>
              Loading decisions&hellip;
            </span>
          </div>
        )}

        <ReactFlow
          nodes={rfNodes}
          edges={rfEdges}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          onNodeClick={handleNodeClick}
          onPaneClick={handlePaneClick}
          fitView
          fitViewOptions={{ padding: 0.15 }}
          attributionPosition="bottom-right"
          minZoom={0.1}
          maxZoom={3}
        >
          <Background
            variant={BackgroundVariant.Dots}
            gap={24}
            size={1}
            color="oklch(88% 0 0)"
          />
          <MiniMap
            nodeColor={(node) => {
              const data = node.data as unknown as DecisionNode | undefined;
              if (!data) return 'oklch(85% 0 0)';
              if (data.status === 'active') return 'oklch(72% 0.15 145)';
              if (data.status === 'superseded') return 'oklch(78% 0 0)';
              return 'oklch(82% 0 0)';
            }}
            style={{
              background: 'oklch(99% 0 0)',
              border: '1px solid oklch(90% 0 0)',
              borderRadius: 8,
            }}
          />
          <Controls />
        </ReactFlow>
      </div>

      {/* Focused decision detail panel */}
      {focusedDecision && (
        <DecisionDetailPanel
          decision={focusedDecision}
          onClose={() => setFocusedDecisionId(null)}
        />
      )}
    </div>
  );
}

// ── Root view component ──────────────────────────────────────────────────────

/**
 * DecisionView — root container for the Decision Graph view (US3).
 *
 * Routes rendering based on viewStates.decisionGraph.state:
 * - 'empty'      → DecisionEmpty
 * - 'activating' → DecisionActivating (partial nodes + stubs)
 * - 'activated'  → Full React Flow decision graph
 */
export default function DecisionView() {
  useViewState();
  const viewState = useGraphInteractionStore(
    (s) => s.viewStates.decisionGraph.state
  );
  const decisionCount = useGraphInteractionStore(
    (s) => s.viewStates.decisionGraph.decisionCount
  );

  const containerRef = useRef<HTMLDivElement>(null);
  const prevStateRef = useRef(viewState);

  // GSAP set-piece entrance animation on state change
  useGSAP(() => {
    if (!containerRef.current) return;
    if (prevStateRef.current === viewState) return;
    prevStateRef.current = viewState;
    animateStateEnter(containerRef.current);
  }, { scope: containerRef, dependencies: [viewState] });

  return (
    <div
      ref={containerRef}
      data-view={`decisions-${viewState}`}
      className="relative flex h-full w-full flex-col overflow-hidden bg-white"
    >
      {viewState === 'empty' && <DecisionEmpty />}

      {viewState === 'activating' && (
        <DecisionActivating
          decisionCount={decisionCount}
          partialNodes={[] as Node<DecisionNode>[]}
        />
      )}

      {viewState === 'activated' && (
        <ReactFlowProvider>
          <ActivatedDecisionGraph />
        </ReactFlowProvider>
      )}
    </div>
  );
}
