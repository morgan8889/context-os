import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import type { NodeProps, Node } from '@xyflow/react';
import type { WorkflowNode as WorkflowNodeData } from '@/types/topology';

/**
 * ShieldIcon — inline SVG shield representing one autonomy level unit.
 */
function ShieldIcon({ filled }: { filled: boolean }) {
  return (
    <svg
      width="10"
      height="12"
      viewBox="0 0 10 12"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path
        d="M5 0.5L0.5 2.5V6C0.5 8.76 2.47 11.34 5 12C7.53 11.34 9.5 8.76 9.5 6V2.5L5 0.5Z"
        fill={filled ? 'var(--color-bottleneck)' : 'none'}
        stroke={filled ? 'var(--color-bottleneck)' : 'oklch(65% 0 0)'}
        strokeWidth="1"
      />
    </svg>
  );
}

/**
 * StatusBadge — colored pill for step status.
 */
function StatusBadge({ status }: { status: WorkflowNodeData['status'] }) {
  const statusStyles: Record<WorkflowNodeData['status'], string> = {
    active: 'bg-[var(--color-status-active)] text-[oklch(20%_0_0)]',
    blocked: 'bg-[var(--color-status-blocked)] text-[oklch(95%_0_0)]',
    complete: 'bg-[var(--color-status-complete)] text-[oklch(20%_0_0)]',
    pending: 'bg-[var(--color-status-pending)] text-[oklch(20%_0_0)]',
  };

  return (
    <span
      className={[
        'inline-block rounded-full px-1.5 py-px text-[10px] font-medium leading-tight',
        statusStyles[status],
      ].join(' ')}
      data-status={status}
    >
      {status}
    </span>
  );
}

/**
 * WorkflowNode — React Flow custom node for a workflow step.
 *
 * Renders status badge, label, owner info, autonomy shields, and optional
 * bottleneck pulsing border. Uses placeholder styling when viewState is
 * 'placeholder'.
 */
export const WorkflowNode = memo(function WorkflowNode({
  data,
}: NodeProps<Node<WorkflowNodeData>>) {
  const isPlaceholder = data.viewState === 'placeholder';
  const isBottleneck = data.isBottleneck && !isPlaceholder;

  return (
    <>
      {/* Inject bottleneck keyframe once per document */}
      {isBottleneck && (
        <style>{`
          @keyframes bottleneckPulse {
            0%, 100% { box-shadow: 0 0 0 0 oklch(70% 0.22 55 / 40%); }
            50%       { box-shadow: 0 0 0 6px oklch(70% 0.22 55 / 0%); }
          }
          .bottleneck-pulse {
            animation: bottleneckPulse 1.8s ease-in-out infinite;
          }
        `}</style>
      )}

      <Handle type="target" position={Position.Left} />

      <div
        data-node-type="workflow-step"
        data-is-bottleneck={isBottleneck}
        data-view-state={data.viewState}
        style={{
          minWidth: 200,
          opacity: isPlaceholder ? 0.4 : 1,
          border: isPlaceholder
            ? '1.5px dashed var(--color-placeholder-grey)'
            : isBottleneck
              ? '2px solid var(--color-bottleneck)'
              : '1.5px solid oklch(85% 0 0)',
          background: isPlaceholder
            ? 'var(--color-placeholder-grey)'
            : 'oklch(100% 0 0)',
          boxShadow: isPlaceholder ? 'none' : 'var(--shadow-node)',
        }}
        className={[
          'rounded-lg p-3 flex flex-col gap-1.5',
          'transition-[box-shadow,border-color] duration-[var(--motion-duration-everyday)]',
          isBottleneck ? 'bottleneck-pulse' : '',
        ]
          .filter(Boolean)
          .join(' ')}
      >
        {/* Top row: status badge */}
        {!isPlaceholder && (
          <div className="flex items-center justify-between">
            <StatusBadge status={data.status} />
          </div>
        )}

        {/* Center: label */}
        <p
          className={[
            'font-semibold text-sm leading-snug truncate',
            isPlaceholder ? 'text-[oklch(55%_0_0)]' : 'text-[oklch(15%_0_0)]',
          ].join(' ')}
          title={data.label}
        >
          {data.label}
        </p>

        {/* Bottom row: owner + autonomy shields */}
        {!isPlaceholder && (
          <div className="flex items-center justify-between gap-2 mt-0.5">
            <div className="flex flex-col min-w-0">
              {data.ownerTeam && (
                <span className="text-[10px] text-[oklch(50%_0_0)] truncate leading-tight">
                  {data.ownerTeam}
                </span>
              )}
              {data.ownerActor && (
                <span className="text-[10px] text-[oklch(60%_0_0)] truncate leading-tight">
                  {data.ownerActor}
                </span>
              )}
            </div>

            {/* Autonomy level shield icons */}
            {data.autonomyLevel > 0 && (
              <div
                className="flex items-center gap-px shrink-0"
                aria-label={`Autonomy level ${data.autonomyLevel}`}
                title={`Autonomy level ${data.autonomyLevel}`}
              >
                {Array.from({ length: Math.min(data.autonomyLevel, 5) }).map((_, i) => (
                  <ShieldIcon key={i} filled={true} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <Handle type="source" position={Position.Right} />
    </>
  );
});
