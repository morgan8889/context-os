import { memo } from 'react';
import {
  getBezierPath,
  EdgeLabelRenderer,
  BaseEdge,
} from '@xyflow/react';
import type { EdgeProps, Edge } from '@xyflow/react';
import type { WorkflowEdge } from '@/types/topology';

const BOTTLENECK_COLOR = 'oklch(70% 0.22 55)';
const NEUTRAL_COLOR = 'oklch(50% 0 0)';

/**
 * BottleneckEdge — React Flow custom edge.
 *
 * When data.isBottleneck is true: animated dashed orange stroke with
 * a CSS dashOffset animation that conveys flow direction.
 * Otherwise: solid neutral gray stroke.
 *
 * Note: This component injects a <style> tag once for the dash animation.
 * In production you would co-locate this CSS with the global stylesheet.
 */
export const BottleneckEdge = memo(function BottleneckEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  label,
}: EdgeProps<Edge<WorkflowEdge>>) {
  const isBottleneck = data?.isBottleneck ?? false;

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetPosition,
    targetX,
    targetY,
  });

  return (
    <>
      <style>{`
        @keyframes dashOffset {
          from { stroke-dashoffset: 0; }
          to   { stroke-dashoffset: -12; }
        }
        .bottleneck-edge-path {
          animation: dashOffset 1.5s linear infinite;
        }
      `}</style>

      <BaseEdge
        id={id}
        path={edgePath}
        style={{
          stroke: isBottleneck ? BOTTLENECK_COLOR : NEUTRAL_COLOR,
          strokeWidth: isBottleneck ? 2 : 1.5,
          strokeDasharray: isBottleneck ? '8 4' : undefined,
        }}
        className={isBottleneck ? 'bottleneck-edge-path' : undefined}
      />

      {label && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: 'all',
            }}
            className={[
              'text-[10px] px-1.5 py-0.5 rounded',
              'bg-[oklch(100%_0_0)] border border-[oklch(85%_0_0)]',
              isBottleneck ? 'text-[oklch(50%_0.22_55)]' : 'text-[oklch(50%_0_0)]',
              'leading-tight nodrag nopan',
            ].join(' ')}
          >
            {label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
});
