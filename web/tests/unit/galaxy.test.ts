import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { render, screen, fireEvent } from '@testing-library/react';
import { createElement } from 'react';

// ── pointInPolygon utility ────────────────────────────────────────────────────

import { pointInPolygon } from '@/views/galaxy/LassoSelect';

describe('pointInPolygon', () => {
  const square: [number, number][] = [
    [0, 0],
    [10, 0],
    [10, 10],
    [0, 10],
  ];

  it('returns true for a point inside the polygon', () => {
    expect(pointInPolygon([5, 5], square)).toBe(true);
  });

  it('returns false for a point outside the polygon', () => {
    expect(pointInPolygon([15, 15], square)).toBe(false);
  });

  it('returns false for a point outside (negative coordinates)', () => {
    expect(pointInPolygon([-1, 5], square)).toBe(false);
  });

  it('returns false for degenerate triangle (fewer than 3 points)', () => {
    expect(pointInPolygon([0, 0], [[0, 0], [5, 5]])).toBe(false);
  });

  it('handles a triangle correctly — inside', () => {
    const triangle: [number, number][] = [[0, 0], [10, 0], [5, 10]];
    expect(pointInPolygon([5, 4], triangle)).toBe(true);
  });

  it('handles a triangle correctly — outside', () => {
    const triangle: [number, number][] = [[0, 0], [10, 0], [5, 10]];
    expect(pointInPolygon([9, 9], triangle)).toBe(false);
  });

  it('handles a point on the right edge (edge case — may be inside or outside)', () => {
    // Ray-casting is not required to produce a specific result for on-edge points
    const result = pointInPolygon([10, 5], square);
    expect(typeof result).toBe('boolean');
  });
});

// ── toInitiativeNode transform ────────────────────────────────────────────────

import { toInitiativeNode, toInitiativeEdge } from '@/lib/transforms/initiative';
import type { ApiNode, ApiEdge } from '@/types/api';

const mockApiNode: ApiNode = {
  id: 'node-001',
  label: 'Test Initiative',
  node_type: 'project',
  status: 'active',
  owner_team: 'platform',
  actor_count: 5,
  risk_score: 0.65,
  autonomy_level: 2,
  edge_count: 3,
};

describe('toInitiativeNode', () => {
  it('maps snake_case API fields to camelCase InitiativeNode', () => {
    const node = toInitiativeNode(mockApiNode);

    expect(node.id).toBe('node-001');
    expect(node.label).toBe('Test Initiative');
    expect(node.type).toBe('project');
    expect(node.status).toBe('active');
    expect(node.ownerTeam).toBe('platform');
    expect(node.actorCount).toBe(5);
    expect(node.riskScore).toBe(0.65);
    expect(node.autonomyLevel).toBe(2);
    expect(node.edgeCount).toBe(3);
  });

  it('defaults x and y to 0', () => {
    const node = toInitiativeNode(mockApiNode);
    expect(node.x).toBe(0);
    expect(node.y).toBe(0);
  });

  it('computes size clamped between 4 and 20', () => {
    // edge_count: 3 → size = 4 + 3 * 0.8 = 6.4
    const node = toInitiativeNode(mockApiNode);
    expect(node.size).toBeGreaterThanOrEqual(4);
    expect(node.size).toBeLessThanOrEqual(20);
    expect(node.size).toBeCloseTo(6.4);
  });

  it('clamps size to minimum 4 for edge_count=0', () => {
    const node = toInitiativeNode({ ...mockApiNode, edge_count: 0 });
    expect(node.size).toBe(4);
  });

  it('clamps size to maximum 20 for very high edge_count', () => {
    const node = toInitiativeNode({ ...mockApiNode, edge_count: 100 });
    expect(node.size).toBe(20);
  });

  it('handles null optional fields gracefully', () => {
    const node = toInitiativeNode({
      ...mockApiNode,
      owner_team: null,
      risk_score: null,
      autonomy_level: null,
    });
    expect(node.ownerTeam).toBeNull();
    expect(node.riskScore).toBeNull();
    expect(node.autonomyLevel).toBeNull();
  });

  it('sets viewState to "activated"', () => {
    const node = toInitiativeNode(mockApiNode);
    expect(node.viewState).toBe('activated');
  });
});

describe('toInitiativeEdge', () => {
  const mockApiEdge: ApiEdge = {
    id: 'edge-001',
    source_id: 'node-001',
    target_id: 'node-002',
    edge_type: 'depends_on',
    weight: 0.8,
  };

  it('maps snake_case API fields to camelCase InitiativeEdge', () => {
    const edge = toInitiativeEdge(mockApiEdge);
    expect(edge.id).toBe('edge-001');
    expect(edge.source).toBe('node-001');
    expect(edge.target).toBe('node-002');
    expect(edge.type).toBe('depends_on');
    expect(edge.weight).toBe(0.8);
  });
});

// ── buildGalaxyGraph (Sigma-safe graph construction) ──────────────────────────

import { buildGalaxyGraph } from '@/views/galaxy/buildGalaxyGraph';
import type { InitiativeNode as GNode, InitiativeEdge as GEdge } from '@/types/galaxy';

describe('buildGalaxyGraph', () => {
  const makeNode = (id: string, type: GNode['type']): GNode => ({
    id,
    label: `n-${id}`,
    type,
    status: 'active',
    ownerTeam: null,
    actorCount: 0,
    riskScore: null,
    autonomyLevel: null,
    edgeCount: 0,
    x: 0,
    y: 0,
    size: 8,
    viewState: 'activated',
  });

  const makeEdge = (id: string, source: string, target: string, type: GEdge['type']): GEdge => ({
    id,
    source,
    target,
    type,
    weight: 1,
  });

  it('does NOT set the Sigma `type` attribute to a domain node type (would crash the renderer)', () => {
    // Sigma reads `type` to pick a render program; a domain type like 'goal'
    // has no program and throws "could not find a suitable program for node type".
    const g = buildGalaxyGraph([makeNode('a', 'goal')], []);
    expect(g.getNodeAttributes('a')['type']).toBeUndefined();
  });

  it('preserves the domain node type under `nodeType`', () => {
    const g = buildGalaxyGraph([makeNode('a', 'goal')], []);
    expect(g.getNodeAttributes('a')['nodeType']).toBe('goal');
  });

  it('does NOT set the Sigma `type` attribute to a domain edge type', () => {
    const g = buildGalaxyGraph(
      [makeNode('a', 'goal'), makeNode('b', 'project')],
      [makeEdge('e1', 'a', 'b', 'depends_on')]
    );
    const attrs = g.getEdgeAttributes('e1');
    expect(attrs['type']).toBeUndefined();
    expect(attrs['edgeType']).toBe('depends_on');
  });

  it('skips edges whose endpoints are missing', () => {
    const g = buildGalaxyGraph(
      [makeNode('a', 'goal')],
      [makeEdge('e1', 'a', 'missing', 'depends_on')]
    );
    expect(g.hasEdge('e1')).toBe(false);
  });

  it('adds all input nodes to the graph', () => {
    const g = buildGalaxyGraph([makeNode('a', 'goal'), makeNode('b', 'project')], []);
    expect(g.order).toBe(2);
  });
});

// ── galaxy color helpers (Sigma-safe colors) ──────────────────────────────────

import { getCssVar, resolveNodeColor, withAlpha } from '@/views/galaxy/colors';

describe('galaxy color helpers', () => {
  it('getCssVar falls back to a concrete color when the var is undefined', () => {
    // jsdom has no tokens.css loaded, so the var resolves empty → fallback.
    const c = getCssVar('--definitely-not-defined');
    expect(c).not.toBe('');
    expect(c).not.toContain('var(');
  });

  it('getCssVar honors a custom fallback', () => {
    expect(getCssVar('--definitely-not-defined', '#abcdef')).toBe('#abcdef');
  });

  it('resolveNodeColor never returns a raw CSS var or color-mix expression', () => {
    // Regression: Sigma WebGL cannot evaluate var()/color-mix() — passing them
    // renders nodes black. The resolved color must be a concrete value.
    for (const type of ['goal', 'project', 'signal', 'artifact']) {
      const c = resolveNodeColor(type);
      expect(c).not.toContain('var(');
      expect(c).not.toContain('color-mix(');
    }
  });

  it('withAlpha bakes opacity into an oklch color', () => {
    expect(withAlpha('oklch(70% 0.15 145)', 0.5)).toBe('oklch(70% 0.15 145 / 0.5)');
  });

  it('withAlpha leaves non-oklch colors unchanged', () => {
    expect(withAlpha('#abcdef', 0.5)).toBe('#abcdef');
  });
});

// ── useGalaxyGraph hook ───────────────────────────────────────────────────────

vi.mock('@/lib/api/client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>();
  return {
    ...actual,
    useInfiniteQuery: vi.fn(),
    useQuery: vi.fn(),
  };
});

import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

describe('useGalaxyGraph', () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock paginated nodes response
    vi.mocked(useInfiniteQuery).mockReturnValue({
      data: {
        pages: [
          {
            items: [mockApiNode],
            next_cursor: null,
            total: 1,
          },
        ],
        pageParams: [null],
      },
      isLoading: false,
      isFetchingNextPage: false,
      hasNextPage: false,
      fetchNextPage: vi.fn(),
    } as ReturnType<typeof useInfiniteQuery>);

    // Mock edges + snapshots responses. Use stable object references (like
    // TanStack Query does for unchanged data) so the hook's memoized graph can
    // stay referentially stable across re-renders.
    const snapshotsResult = { data: [], isLoading: false } as ReturnType<typeof useQuery>;
    const edgesResult = {
      data: { items: [], next_cursor: null, total: 0 },
      isLoading: false,
    } as ReturnType<typeof useQuery>;
    vi.mocked(useQuery).mockImplementation((options) => {
      const key = JSON.stringify(options.queryKey);
      return key.includes('snapshots') ? snapshotsResult : edgesResult;
    });
  });

  it('calls useInfiniteQuery with graphKeys.nodes', async () => {
    const { useGalaxyGraph } = await import('@/views/galaxy/hooks/useGalaxyGraph');
    const { graphKeys } = await import('@/lib/api/queryKeys');

    renderHook(() => useGalaxyGraph(), {
      wrapper: ({ children }) =>
        createElement(QueryClientProvider, { client: queryClient }, children),
    });

    expect(useInfiniteQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: graphKeys.nodes(),
      })
    );
  });

  it('returns a graphology Graph instance', async () => {
    const { useGalaxyGraph } = await import('@/views/galaxy/hooks/useGalaxyGraph');
    const Graph = (await import('graphology')).default;

    const { result } = renderHook(() => useGalaxyGraph(), {
      wrapper: ({ children }) =>
        createElement(QueryClientProvider, { client: queryClient }, children),
    });

    expect(result.current.graph).toBeInstanceOf(Graph);
  });

  it('transforms API nodes via toInitiativeNode and adds them to the graph', async () => {
    const { useGalaxyGraph } = await import('@/views/galaxy/hooks/useGalaxyGraph');

    const { result } = renderHook(() => useGalaxyGraph(), {
      wrapper: ({ children }) =>
        createElement(QueryClientProvider, { client: queryClient }, children),
    });

    expect(result.current.graph.hasNode(mockApiNode.id)).toBe(true);
    const attrs = result.current.graph.getNodeAttributes(mockApiNode.id);
    expect(attrs['label']).toBe(mockApiNode.label);
    // Domain type lives under `nodeType`; Sigma's `type` (render program) is unset.
    expect(attrs['nodeType']).toBe(mockApiNode.node_type);
    expect(attrs['type']).toBeUndefined();
  });

  it('returns a referentially stable graph across re-renders when data is unchanged', async () => {
    // Regression: an unmemoized build returns a fresh Graph every render, which
    // makes ForceLayout reload + restart ForceAtlas2 on every render, defeating
    // layout convergence (SC-002). The graph reference must be stable when the
    // underlying query data has not changed.
    const { useGalaxyGraph } = await import('@/views/galaxy/hooks/useGalaxyGraph');

    const { result, rerender } = renderHook(() => useGalaxyGraph(), {
      wrapper: ({ children }) =>
        createElement(QueryClientProvider, { client: queryClient }, children),
    });

    const firstGraph = result.current.graph;
    rerender();
    expect(result.current.graph).toBe(firstGraph);
  });

  it('returns isLoading false when data is available', async () => {
    const { useGalaxyGraph } = await import('@/views/galaxy/hooks/useGalaxyGraph');

    const { result } = renderHook(() => useGalaxyGraph(), {
      wrapper: ({ children }) =>
        createElement(QueryClientProvider, { client: queryClient }, children),
    });

    expect(result.current.isLoading).toBe(false);
  });
});

// ── OverlayControls component ─────────────────────────────────────────────────

vi.mock('@react-sigma/core', () => ({
  SigmaContainer: ({ children }: { children: React.ReactNode }) =>
    createElement('div', { className: 'sigma-container' }, children),
  useSigma: () => ({ getGraph: () => ({ forEachNode: vi.fn() }), getContainer: vi.fn() }),
  useLoadGraph: () => vi.fn(),
  useRegisterEvents: () => vi.fn(),
  useSetSettings: () => vi.fn(),
}));

vi.mock('@react-sigma/layout-forceatlas2', () => ({
  useWorkerLayoutForceAtlas2: () => ({ start: vi.fn(), stop: vi.fn(), isRunning: false }),
}));

vi.mock('gsap', () => ({
  default: { to: vi.fn(), fromTo: vi.fn() },
}));

vi.mock('@gsap/react', () => ({
  useGSAP: vi.fn((fn: () => void) => fn()),
}));

import React from 'react';
import { OverlayControls } from '@/views/galaxy/OverlayControls';
import { useGraphInteractionStore } from '@/lib/stores/graphInteraction';

describe('OverlayControls', () => {
  beforeEach(() => {
    // Reset store to default state
    act(() => {
      useGraphInteractionStore.getState().setGalaxyOverlay({
        type: null,
        thresholds: { low: 0.3, high: 0.7 },
      });
    });
  });

  it('renders 4 overlay toggle buttons', () => {
    render(createElement(OverlayControls));

    expect(screen.getByRole('button', { name: /load overlay/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /risk overlay/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /autonomy overlay/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /ownership overlay/i })).toBeInTheDocument();
  });

  it('renders legend labels under each button', () => {
    render(createElement(OverlayControls));

    expect(screen.getByText('Load')).toBeInTheDocument();
    expect(screen.getByText('Risk')).toBeInTheDocument();
    expect(screen.getByText('Autonomy')).toBeInTheDocument();
    expect(screen.getByText('Ownership')).toBeInTheDocument();
  });

  it('clicking a button dispatches the correct overlay type to Zustand', () => {
    render(createElement(OverlayControls));

    const riskButton = screen.getByRole('button', { name: /risk overlay/i });
    fireEvent.click(riskButton);

    const { galaxyOverlay } = useGraphInteractionStore.getState();
    expect(galaxyOverlay.type).toBe('risk');
    expect(galaxyOverlay.thresholds).toEqual({ low: 0.3, high: 0.7 });
  });

  it('clicking an active button sets overlay type to null (toggle off)', () => {
    // First activate 'load'
    act(() => {
      useGraphInteractionStore.getState().setGalaxyOverlay({
        type: 'load',
        thresholds: { low: 0.3, high: 0.7 },
      });
    });

    render(createElement(OverlayControls));

    const loadButton = screen.getByRole('button', { name: /load overlay \(active\)/i });
    fireEvent.click(loadButton);

    const { galaxyOverlay } = useGraphInteractionStore.getState();
    expect(galaxyOverlay.type).toBeNull();
  });

  it('active button has aria-pressed=true', () => {
    act(() => {
      useGraphInteractionStore.getState().setGalaxyOverlay({
        type: 'autonomy',
        thresholds: { low: 0.3, high: 0.7 },
      });
    });

    render(createElement(OverlayControls));

    const autonomyButton = screen.getByRole('button', { name: /autonomy overlay \(active\)/i });
    expect(autonomyButton).toHaveAttribute('aria-pressed', 'true');

    const riskButton = screen.getByRole('button', { name: /risk overlay$/i });
    expect(riskButton).toHaveAttribute('aria-pressed', 'false');
  });
});

// ── NodeDetailPane component ──────────────────────────────────────────────────

import { NodeDetailPane } from '@/views/galaxy/NodeDetailPane';
import type { InitiativeNode } from '@/types/galaxy';

const mockNode: InitiativeNode = {
  id: 'node-001',
  label: 'Test Initiative',
  type: 'project',
  status: 'active',
  ownerTeam: 'platform',
  actorCount: 5,
  riskScore: 0.72,
  autonomyLevel: 3,
  edgeCount: 12,
  x: 0,
  y: 0,
  size: 8,
  viewState: 'activated',
};

describe('NodeDetailPane', () => {
  beforeEach(() => {
    act(() => {
      useGraphInteractionStore.getState().setFocusedNodeId(null);
    });
  });

  it('renders null when focusedNodeId is null', () => {
    const { container } = render(createElement(NodeDetailPane, { node: null }));
    expect(container.firstChild).toBeNull();
  });

  it('renders null when node is null even if focusedNodeId is set', () => {
    act(() => {
      useGraphInteractionStore.getState().setFocusedNodeId('node-001');
    });

    const { container } = render(createElement(NodeDetailPane, { node: null }));
    expect(container.firstChild).toBeNull();
  });

  it('shows initiative label when node and focusedNodeId are set', () => {
    act(() => {
      useGraphInteractionStore.getState().setFocusedNodeId('node-001');
    });

    render(createElement(NodeDetailPane, { node: mockNode }));

    expect(screen.getByText('Test Initiative')).toBeInTheDocument();
  });

  it('shows type and status badges', () => {
    act(() => {
      useGraphInteractionStore.getState().setFocusedNodeId('node-001');
    });

    render(createElement(NodeDetailPane, { node: mockNode }));

    expect(screen.getByText('Project')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('shows formatted risk score', () => {
    act(() => {
      useGraphInteractionStore.getState().setFocusedNodeId('node-001');
    });

    render(createElement(NodeDetailPane, { node: mockNode }));

    expect(screen.getByText('Risk: 0.72')).toBeInTheDocument();
  });

  it('shows formatted autonomy level', () => {
    act(() => {
      useGraphInteractionStore.getState().setFocusedNodeId('node-001');
    });

    render(createElement(NodeDetailPane, { node: mockNode }));

    expect(screen.getByText('Autonomy: L3')).toBeInTheDocument();
  });

  it('shows edge count', () => {
    act(() => {
      useGraphInteractionStore.getState().setFocusedNodeId('node-001');
    });

    render(createElement(NodeDetailPane, { node: mockNode }));

    expect(screen.getByText('Connections: 12')).toBeInTheDocument();
  });

  it('shows owner team', () => {
    act(() => {
      useGraphInteractionStore.getState().setFocusedNodeId('node-001');
    });

    render(createElement(NodeDetailPane, { node: mockNode }));

    expect(screen.getByText('platform')).toBeInTheDocument();
  });

  it('clears focusedNodeId when panel close is triggered', () => {
    act(() => {
      useGraphInteractionStore.getState().setFocusedNodeId('node-001');
    });

    render(createElement(NodeDetailPane, { node: mockNode }));

    const closeButton = screen.getByRole('button', { name: /close panel/i });
    fireEvent.click(closeButton);

    expect(useGraphInteractionStore.getState().focusedNodeId).toBeNull();
  });
});
