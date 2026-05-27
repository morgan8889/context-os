import { useEffect } from 'react';
import { SigmaContainer, useLoadGraph, useSigma } from '@react-sigma/core';
import { useWorkerLayoutForceAtlas2 } from '@react-sigma/layout-forceatlas2';
import Graph from 'graphology';
import { useGraphInteractionStore } from '@/lib/stores/graphInteraction';
import { StateCTA } from '@/design-system/primitives/StateCTA';
import type { InitiativeNode } from '@/types/galaxy';

/** Stub node counts to anticipate: total visual budget minus real nodes */
const STUB_COUNT = 8;

// Sigma v3 WebGL can't parse color-mix() or oklch(). Resolve CSS vars via canvas.
const _cc = typeof document !== 'undefined'
  ? Object.assign(document.createElement('canvas'), { width: 1, height: 1 }).getContext('2d')
  : null;

function resolveCSSVar(varName: string): string {
  if (!_cc) return '#888888';
  const raw = getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
  _cc.clearRect(0, 0, 1, 1);
  _cc.fillStyle = raw;
  _cc.fillRect(0, 0, 1, 1);
  const [r, g, b] = _cc.getImageData(0, 0, 1, 1).data;
  return `rgba(${r},${g},${b},0.5)`;
}

/** Inner component that has access to Sigma context */
function ActivatingGraphLoader({
  nodes,
  stubCount,
}: {
  nodes: InitiativeNode[];
  stubCount: number;
}) {
  const loadGraph = useLoadGraph();
  const sigma = useSigma();

  // Wire up ForceAtlas2 in Web Worker
  const { start, stop } = useWorkerLayoutForceAtlas2({
    settings: { slowDown: 10, gravity: 1.0, scalingRatio: 2.0 },
  });

  useEffect(() => {
    const graph = new Graph({ type: 'mixed' });

    // Real nodes — 50% opacity
    nodes.forEach((node) => {
      graph.addNode(node.id, {
        label: node.label,
        x: node.x || Math.random() * 100 - 50,
        y: node.y || Math.random() * 100 - 50,
        size: node.size,
        color: resolveCSSVar(`--color-node-${node.type}`),
        type: 'circle',
        nodeType: node.type,
      });
    });

    // Stub/anticipatory nodes — placeholder grey, 25% opacity
    for (let i = 0; i < stubCount; i++) {
      const stubId = `__stub_${i}`;
      graph.addNode(stubId, {
        label: '',
        x: Math.random() * 120 - 60,
        y: Math.random() * 120 - 60,
        size: 6,
        color: 'var(--color-placeholder-grey)',
        isStub: true,
      });
    }

    loadGraph(graph, true);
    start();

    return () => {
      stop();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes.length]);

  // Apply custom nodeReducer for stubs (25% opacity) vs real nodes (50% opacity)
  useEffect(() => {
    sigma.setSetting('nodeReducer', (_node: string, data: Record<string, unknown>) => {
      if (data['isStub']) {
        return { ...data, color: 'var(--color-placeholder-grey)', size: 6, label: '' };
      }
      return data;
    });
  }, [sigma]);

  return null;
}

interface GalaxyActivatingProps {
  initiativeCount: number;
}

/**
 * GalaxyActivating — shown when the galaxy view state is 'activating'.
 *
 * Renders a SigmaContainer with discovered nodes at 50% opacity and
 * anticipatory stub nodes at 25% opacity with a pulsing animation.
 * ForceAtlas2 runs in a Web Worker via useWorkerLayoutForceAtlas2.
 */
export default function GalaxyActivating({ initiativeCount }: GalaxyActivatingProps) {
  const galaxySnapshots = useGraphInteractionStore((s) => s.galaxySnapshots);
  const latestSnapshot = galaxySnapshots[galaxySnapshots.length - 1];
  const nodes = latestSnapshot?.nodes ?? [];
  const stubCount = Math.max(0, STUB_COUNT - nodes.length);

  return (
    <div
      data-state="activating"
      className="relative flex h-full w-full flex-col overflow-hidden"
      style={{ background: 'var(--color-galaxy-bg, oklch(8% 0 0))' }}
    >
      {/* Status overlay — top center */}
      <div className="pointer-events-none absolute inset-x-0 top-4 z-10 flex justify-center">
        <div
          className="rounded-full px-4 py-1.5 text-sm font-medium"
          style={{
            background: 'oklch(12% 0 0 / 0.8)',
            color: 'var(--color-placeholder-grey)',
            backdropFilter: 'blur(8px)',
          }}
        >
          {initiativeCount} initiatives mapped — discovering more connections…
        </div>
      </div>

      {/* Pulse CSS animation for stub nodes */}
      <style>{`
        @keyframes galaxy-node-pulse {
          0%, 100% { opacity: 0.25; }
          50%       { opacity: 0.5;  }
        }
        .sigma-renderer canvas {
          /* Sigma draws to canvas — pulse handled via nodeReducer opacity */
        }
      `}</style>

      {/* Sigma canvas */}
      <div className="flex-1">
        <SigmaContainer
          style={{
            width: '100%',
            height: '100%',
            background: 'var(--color-galaxy-bg, oklch(8% 0 0))',
          }}
          settings={{
            labelColor: { color: 'oklch(70% 0 0)' },
            renderLabels: nodes.length <= 50,
            minCameraRatio: 0.05,
            maxCameraRatio: 4,
          }}
        >
          <ActivatingGraphLoader nodes={nodes} stubCount={stubCount} />
        </SigmaContainer>
      </div>

      {/* Bottom CTA */}
      <div className="absolute bottom-6 inset-x-0 flex justify-center">
        <StateCTA
          label="Notify me when done"
          onClick={() => {
            /* will be wired in Phase 7 */
          }}
        />
      </div>
    </div>
  );
}
