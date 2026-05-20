import { useRef, useEffect, useMemo } from 'react';
import { useGSAP } from '@gsap/react';
import { SigmaContainer, useRegisterEvents, useSetSettings, useSigma } from '@react-sigma/core';
import { animateStateEnter } from '@/lib/animations/stateTransitions';
import { useGraphInteractionStore } from '@/lib/stores/graphInteraction';
import { useViewState } from '@/lib/api/viewState';
import { useGalaxyGraph } from './hooks/useGalaxyGraph';
import { ForceLayout } from './ForceLayout';
import { LassoSelect } from './LassoSelect';
import { OverlayControls } from './OverlayControls';
import { NodeDetailPane } from './NodeDetailPane';
import { TimeTravelBar } from './TimeTravelBar';
import GalaxyEmpty from './GalaxyEmpty';
import GalaxyActivating from './GalaxyActivating';
import type { InitiativeType, InitiativeStatus } from '@/types/galaxy';

/** Map node type to CSS custom property name */
const NODE_COLOR_MAP: Record<InitiativeType, string> = {
  goal: '--color-node-goal',
  project: '--color-node-project',
  signal: '--color-node-signal',
  artifact: '--color-node-artifact',
};

/** Resolve a CSS custom property to its computed value */
function getCSSVar(varName: string): string {
  if (typeof window === 'undefined') return 'oklch(60% 0 0)';
  return getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
}

/** Map status to color var */
const STATUS_COLOR_MAP: Record<InitiativeStatus, string> = {
  active: '--color-status-active',
  paused: '--color-status-paused',
  at_risk: '--color-status-at-risk',
  complete: '--color-status-complete',
};

/**
 * GraphEventWiring — registers Sigma event handlers and node/edge reducers.
 * Must be inside SigmaContainer.
 */
function GraphEventWiring() {
  const sigma = useSigma();
  const registerEvents = useRegisterEvents();
  const setSettings = useSetSettings();
  const setFocusedNodeId = useGraphInteractionStore((s) => s.setFocusedNodeId);
  const clearGalaxySelection = useGraphInteractionStore((s) => s.clearGalaxySelection);
  const galaxySelection = useGraphInteractionStore((s) => s.galaxySelection);
  const galaxyOverlay = useGraphInteractionStore((s) => s.galaxyOverlay);

  // Register click handlers
  useEffect(() => {
    registerEvents({
      clickNode: ({ node }) => {
        setFocusedNodeId(node);
      },
      clickStage: () => {
        clearGalaxySelection();
        setFocusedNodeId(null);
      },
    });
  }, [registerEvents, setFocusedNodeId, clearGalaxySelection]);

  // Apply node/edge reducers when selection or overlay changes
  useEffect(() => {
    const hasSelection = galaxySelection.nodeIds.size > 0;

    setSettings({
      nodeReducer: (node, data) => {
        const nodeType = (data['type'] as InitiativeType) ?? 'project';
        const nodeStatus = (data['status'] as InitiativeStatus) ?? 'active';

        // Base color from type
        let color = getCSSVar(NODE_COLOR_MAP[nodeType]);

        // Overlay modifies color
        if (galaxyOverlay.type === 'risk') {
          const riskScore = (data['riskScore'] as number) ?? 0;
          if (riskScore >= galaxyOverlay.thresholds.high) {
            color = getCSSVar('--color-status-at-risk');
          } else if (riskScore >= galaxyOverlay.thresholds.low) {
            color = getCSSVar('--color-status-paused');
          }
        } else if (galaxyOverlay.type === 'load') {
          const edgeCount = (data['edgeCount'] as number) ?? 0;
          if (edgeCount >= 10) color = getCSSVar('--color-bottleneck');
        } else if (galaxyOverlay.type === 'autonomy') {
          const level = (data['autonomyLevel'] as number) ?? 0;
          color = level >= 4 ? getCSSVar('--color-status-at-risk') : getCSSVar('--color-node-signal');
        } else if (galaxyOverlay.type === 'ownership') {
          color = getCSSVar(STATUS_COLOR_MAP[nodeStatus]);
        }

        // Selection dimming: if there's a selection, non-selected nodes fade
        if (hasSelection && !galaxySelection.nodeIds.has(node)) {
          return { ...data, color, highlighted: false, zIndex: 0, label: '' };
        }

        return { ...data, color, highlighted: hasSelection && galaxySelection.nodeIds.has(node) };
      },

      edgeReducer: (_edge, data) => {
        if (hasSelection) {
          // Hide edges connecting unselected nodes
          return { ...data, hidden: true };
        }
        return data;
      },
    });
  }, [galaxySelection, galaxyOverlay, setSettings]);

  return null;
}

/**
 * GalaxyView — main container for the galaxy visualization.
 *
 * Routes between empty / activating / activated states based on
 * the viewStates.galaxy.state from the Zustand store (populated
 * by useViewState polling).
 */
export default function GalaxyView() {
  useViewState();

  const viewStates = useGraphInteractionStore((s) => s.viewStates);
  const galaxySnapshots = useGraphInteractionStore((s) => s.galaxySnapshots);
  const focusedNodeId = useGraphInteractionStore((s) => s.focusedNodeId);

  const { graph, isLoading, hasNextPage, fetchNextPage } = useGalaxyGraph();

  const containerRef = useRef<HTMLDivElement>(null);
  const prevState = useRef<string>('');

  const galaxyState = viewStates.galaxy.state;
  const initiativeCount = viewStates.galaxy.initiativeCount;

  // GSAP set-piece entrance animation when galaxy state changes
  useGSAP(() => {
    if (!containerRef.current) return;
    if (prevState.current === galaxyState) return;
    prevState.current = galaxyState;
    animateStateEnter(containerRef.current);
  }, { scope: containerRef, dependencies: [galaxyState] });

  // Load next page lazily when needed (e.g., after first render of activated state)
  useEffect(() => {
    if (galaxyState === 'activated' && hasNextPage && !isLoading) {
      fetchNextPage();
    }
  }, [galaxyState, hasNextPage, isLoading, fetchNextPage]);

  // Find the focused node's data from the graph
  const focusedNode = useMemo(() => {
    if (!focusedNodeId || !graph.hasNode(focusedNodeId)) return null;
    const attrs = graph.getNodeAttributes(focusedNodeId);
    return {
      id: focusedNodeId,
      label: (attrs['label'] as string) ?? focusedNodeId,
      type: (attrs['type'] as InitiativeType) ?? 'project',
      status: (attrs['status'] as InitiativeStatus) ?? 'active',
      ownerTeam: (attrs['ownerTeam'] as string | null) ?? null,
      actorCount: (attrs['actorCount'] as number) ?? 0,
      riskScore: (attrs['riskScore'] as number | null) ?? null,
      autonomyLevel: (attrs['autonomyLevel'] as number | null) ?? null,
      edgeCount: (attrs['edgeCount'] as number) ?? 0,
      x: (attrs['x'] as number) ?? 0,
      y: (attrs['y'] as number) ?? 0,
      size: (attrs['size'] as number) ?? 8,
      viewState: 'activated' as const,
    };
  }, [focusedNodeId, graph]);

  return (
    <div
      ref={containerRef}
      data-view="galaxy"
      className="relative flex h-full w-full flex-col overflow-hidden"
      style={{ background: 'var(--color-galaxy-bg, oklch(8% 0 0))' }}
    >
      {/* ── Empty state ── */}
      {galaxyState === 'empty' && <GalaxyEmpty />}

      {/* ── Activating state ── */}
      {galaxyState === 'activating' && (
        <GalaxyActivating initiativeCount={initiativeCount} />
      )}

      {/* ── Activated state ── */}
      {galaxyState === 'activated' && (
        <div className="relative flex flex-1 flex-col overflow-hidden">
          {/* Sigma canvas fills available space */}
          <div className="flex-1 relative">
            <SigmaContainer
              style={{
                width: '100%',
                height: '100%',
                background: 'var(--color-galaxy-bg, oklch(8% 0 0))',
              }}
              settings={{
                labelColor: { color: 'oklch(70% 0 0)' },
                labelSize: 11,
                labelWeight: '500',
                renderLabels: true,
                minCameraRatio: 0.05,
                maxCameraRatio: 6,
                defaultEdgeColor: 'oklch(35% 0 0)',
                defaultEdgeType: 'line',
              }}
            >
              {/* Loads graph + runs ForceAtlas2 in Web Worker */}
              <ForceLayout graph={graph} />

              {/* SVG lasso overlay */}
              <LassoSelect />

              {/* Event wiring and reducers */}
              <GraphEventWiring />
            </SigmaContainer>

            {/* Overlay controls — top right */}
            <div className="absolute right-4 top-4 z-20">
              <OverlayControls />
            </div>
          </div>

          {/* Time travel bar — bottom */}
          {galaxySnapshots.length >= 2 && (
            <TimeTravelBar />
          )}
        </div>
      )}

      {/* Node detail pane (rendered outside SigmaContainer, portal-friendly) */}
      <NodeDetailPane node={focusedNode} />
    </div>
  );
}
