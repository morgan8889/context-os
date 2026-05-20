import { useRef, useState, useCallback, useEffect } from 'react';
import type { MouseEvent as ReactMouseEvent } from 'react';
import { useSigma } from '@react-sigma/core';
import { useGraphInteractionStore } from '@/lib/stores/graphInteraction';

type Point = [number, number];

/**
 * pointInPolygon — Ray-casting algorithm to test if a point is inside a polygon.
 *
 * @param point - [x, y] coordinates of the test point
 * @param polygon - Array of [x, y] vertex coordinates forming the polygon
 * @returns true if the point is inside the polygon
 */
export function pointInPolygon(point: Point, polygon: Point[]): boolean {
  if (polygon.length < 3) return false;

  const [px, py] = point;
  let inside = false;

  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [xi, yi] = polygon[i]!;
    const [xj, yj] = polygon[j]!;

    const intersects =
      yi > py !== yj > py &&
      px < ((xj - xi) * (py - yi)) / (yj - yi) + xi;

    if (intersects) {
      inside = !inside;
    }
  }

  return inside;
}

/**
 * LassoSelect — SVG overlay for mouse-driven lasso selection.
 *
 * Must be rendered inside a SigmaContainer. Draws an SVG polyline
 * as the user drags. On mouseup, tests all graph nodes against the
 * lasso polygon and dispatches the resulting SelectionSet to Zustand.
 * Escape key clears the current selection.
 */
export function LassoSelect() {
  const sigma = useSigma();
  const setGalaxySelection = useGraphInteractionStore((s) => s.setGalaxySelection);
  const clearGalaxySelection = useGraphInteractionStore((s) => s.clearGalaxySelection);

  const svgRef = useRef<SVGSVGElement>(null);
  const isDrawing = useRef(false);
  const [path, setPath] = useState<Point[]>([]);
  const [size, setSize] = useState({ width: 0, height: 0 });

  // Track container size for the SVG overlay
  useEffect(() => {
    const container = sigma.getContainer();
    if (!container) return;

    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) {
        setSize({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        });
      }
    });

    observer.observe(container);
    setSize({ width: container.offsetWidth, height: container.offsetHeight });

    return () => observer.disconnect();
  }, [sigma]);

  // Escape key clears selection
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        clearGalaxySelection();
        setPath([]);
        isDrawing.current = false;
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [clearGalaxySelection]);

  const getEventPoint = useCallback((e: ReactMouseEvent<SVGSVGElement>): Point => {
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect) return [0, 0];
    return [e.clientX - rect.left, e.clientY - rect.top];
  }, []);

  const handleMouseDown = useCallback(
    (e: ReactMouseEvent<SVGSVGElement>) => {
      // Only left mouse button
      if (e.button !== 0) return;
      e.preventDefault();
      isDrawing.current = true;
      const pt = getEventPoint(e);
      setPath([pt]);
    },
    [getEventPoint]
  );

  const handleMouseMove = useCallback(
    (e: ReactMouseEvent<SVGSVGElement>) => {
      if (!isDrawing.current) return;
      const pt = getEventPoint(e);
      setPath((prev) => [...prev, pt]);
    },
    [getEventPoint]
  );

  const handleMouseUp = useCallback(() => {
    if (!isDrawing.current) return;
    isDrawing.current = false;

    const polygon = path;
    if (polygon.length < 3) {
      setPath([]);
      return;
    }

    // Close the polygon
    const closedPolygon: Point[] = [...polygon, polygon[0]!];

    // Test each node against the polygon
    const selectedIds = new Set<string>();
    sigma.getGraph().forEachNode((nodeId: string) => {
      const displayData = sigma.getNodeDisplayData(nodeId);
      if (!displayData) return;
      const { x, y } = displayData;
      if (pointInPolygon([x, y], closedPolygon)) {
        selectedIds.add(nodeId);
      }
    });

    setGalaxySelection({ nodeIds: selectedIds, source: 'lasso' });
    setPath([]);
  }, [path, sigma, setGalaxySelection]);

  const polylinePoints = path.map((p) => p.join(',')).join(' ');

  return (
    <svg
      ref={svgRef}
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 z-10"
      style={{
        width: size.width,
        height: size.height,
        // Only capture pointer events when user is actually drawing
        pointerEvents: 'all',
        cursor: 'crosshair',
      }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
    >
      {path.length > 1 && (
        <>
          {/* Lasso fill */}
          <polygon
            points={polylinePoints}
            fill="oklch(60% 0.2 220 / 0.08)"
            stroke="none"
          />
          {/* Lasso stroke */}
          <polyline
            points={polylinePoints}
            fill="none"
            stroke="var(--color-lasso-stroke, oklch(60% 0.2 220 / 0.5))"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeDasharray="4 3"
          />
        </>
      )}
    </svg>
  );
}
