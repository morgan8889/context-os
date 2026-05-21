import { memo } from 'react';
import { getBezierPath, EdgeLabelRenderer } from '@xyflow/react';
import type { EdgeProps, Edge } from '@xyflow/react';
import type { DecisionEdge as DecisionEdgeData } from '@/types/decisions';

/**
 * Visual configuration per edge type (FR-021).
 *
 * All stroke colors use oklch() — no hex values.
 */
const EDGE_STYLES: Record<
  DecisionEdgeData['type'],
  {
    stroke: string;
    strokeWidth: number;
    strokeDasharray?: string;
    markerEnd?: string;
  }
> = {
  predecessor: {
    stroke: 'oklch(50% 0 0)',
    strokeWidth: 2,
    markerEnd: 'url(#decision-arrow)',
  },
  alternative: {
    stroke: 'oklch(60% 0 0)',
    strokeWidth: 1.5,
    strokeDasharray: '6 3',
    // no arrowhead
  },
  dependent: {
    stroke: 'oklch(55% 0 0)',
    strokeWidth: 1,
    strokeDasharray: '2 3',
    markerEnd: 'url(#decision-arrow)',
  },
};

/**
 * DecisionEdge — React Flow custom edge for decision relationships.
 *
 * Edge type drives visual treatment:
 * - predecessor: solid 2px stroke with arrowhead
 * - alternative: dashed 6/3 pattern, 1.5px, no arrowhead
 * - dependent: dotted 2/3 pattern, 1px, with arrowhead
 *
 * Optional edge label rendered via EdgeLabelRenderer.
 */
export const DecisionEdgeComponent = memo(function DecisionEdgeComponent({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  label,
  markerEnd,
}: EdgeProps<Edge<DecisionEdgeData>>) {
  const edgeType = (data?.type as DecisionEdgeData['type'] | undefined) ?? 'predecessor';
  const style = EDGE_STYLES[edgeType];

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  // Use our own marker for predecessor/dependent; ignore RF-provided markerEnd
  // to avoid conflicts with the defs we inject per-edge.
  const resolvedMarkerEnd = style.markerEnd ?? markerEnd ?? undefined;

  return (
    <>
      {/* SVG defs for arrowhead — injected once; duplicate defs are harmless */}
      <defs>
        <marker
          id="decision-arrow"
          markerWidth="8"
          markerHeight="8"
          refX="6"
          refY="3"
          orient="auto"
          markerUnits="strokeWidth"
        >
          <path
            d="M0,0 L0,6 L9,3 z"
            fill={style.stroke}
          />
        </marker>
      </defs>

      <path
        id={id}
        className="react-flow__edge-path"
        d={edgePath}
        stroke={style.stroke}
        strokeWidth={style.strokeWidth}
        strokeDasharray={style.strokeDasharray}
        strokeLinecap="round"
        markerEnd={resolvedMarkerEnd}
        fill="none"
      />

      {/* Optional label */}
      {label && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: 'all',
              fontSize: 10,
              fontWeight: 500,
              color: 'oklch(45% 0 0)',
              background: 'oklch(100% 0 0)',
              border: '1px solid oklch(88% 0 0)',
              borderRadius: 4,
              padding: '1px 4px',
              whiteSpace: 'nowrap',
            }}
            className="nodrag nopan"
          >
            {String(label)}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
});
