import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import type { NodeProps } from '@xyflow/react';
import { NodeTooltip } from '@/design-system/primitives/NodeTooltip';
import type { DecisionNode, DecisionAlternative } from '@/types/decisions';

// ── Relative date formatting ─────────────────────────────────────────────────

const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });

function formatRelative(isoDate: string): string {
  const diffMs = new Date(isoDate).getTime() - Date.now();
  const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));

  if (Math.abs(diffDays) < 1) {
    const diffHours = Math.round(diffMs / (1000 * 60 * 60));
    if (Math.abs(diffHours) < 1) {
      const diffMinutes = Math.round(diffMs / (1000 * 60));
      return rtf.format(diffMinutes, 'minute');
    }
    return rtf.format(diffHours, 'hour');
  }
  if (Math.abs(diffDays) < 30) {
    return rtf.format(diffDays, 'day');
  }
  const diffMonths = Math.round(diffDays / 30);
  if (Math.abs(diffMonths) < 12) {
    return rtf.format(diffMonths, 'month');
  }
  return rtf.format(Math.round(diffMonths / 12), 'year');
}

// ── Status badge ─────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: DecisionNode['status'] }) {
  if (status === 'active') {
    return (
      <span
        className="inline-flex items-center rounded-full px-2 py-px text-[10px] font-semibold leading-tight"
        style={{
          border: '1.5px solid oklch(65% 0.15 145)',
          color: 'oklch(35% 0.12 145)',
          background: 'oklch(95% 0.04 145)',
        }}
        data-status="active"
      >
        active
      </span>
    );
  }
  if (status === 'superseded') {
    return (
      <span
        className="inline-flex items-center rounded-full px-2 py-px text-[10px] font-medium leading-tight"
        style={{
          border: '1.5px solid oklch(78% 0 0)',
          color: 'oklch(55% 0 0)',
          background: 'oklch(96% 0 0)',
        }}
        data-status="superseded"
      >
        superseded
      </span>
    );
  }
  // retracted
  return (
    <span
      className="inline-flex items-center rounded-full px-2 py-px text-[10px] font-medium leading-tight"
      style={{
        border: '1.5px solid oklch(82% 0 0)',
        color: 'oklch(62% 0 0)',
        background: 'oklch(97% 0 0)',
      }}
      data-status="retracted"
    >
      retracted
    </span>
  );
}

// ── Tooltip body ─────────────────────────────────────────────────────────────

function TooltipBody({
  rationale,
  alternatives,
  authorName,
}: {
  rationale: string;
  alternatives: DecisionAlternative[];
  authorName: string | null;
}) {
  return (
    <div className="flex flex-col gap-2">
      <div>
        <p className="font-medium" style={{ color: 'oklch(30% 0 0)' }}>
          Rationale
        </p>
        <p className="leading-relaxed">{rationale}</p>
      </div>

      {alternatives.length > 0 && (
        <div>
          <p className="font-medium" style={{ color: 'oklch(30% 0 0)' }}>
            Alternatives considered
          </p>
          <ul className="mt-1 flex flex-col gap-1">
            {alternatives.map((alt, i) => (
              <li key={i}>
                <span className="font-medium">{alt.label}</span>
                {alt.reason && (
                  <span style={{ color: 'oklch(55% 0 0)' }}> — {alt.reason}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {authorName && (
        <div>
          <p className="font-medium" style={{ color: 'oklch(30% 0 0)' }}>
            Author
          </p>
          <p>{authorName}</p>
        </div>
      )}
    </div>
  );
}

// ── Main component ───────────────────────────────────────────────────────────

/**
 * DecisionNodeComponent — React Flow custom node for an organizational decision.
 *
 * Renders title (2-line clamp), status badge, captured date (relative),
 * impacted-systems chips (max 3 + overflow count), and a hover tooltip
 * with full rationale, alternatives, and author.
 *
 * When `data.viewState === 'activating'`, renders in placeholder-grey
 * with a dashed border.
 */
export const DecisionNodeComponent = memo(function DecisionNodeComponent({
  data,
}: NodeProps<DecisionNode>) {
  const isPlaceholder = data.viewState === 'activating' || data.viewState === 'placeholder';
  const isRetracted = data.status === 'retracted';

  const visibleSystems = data.impactedSystems.slice(0, 3);
  const overflowCount = data.impactedSystems.length - visibleSystems.length;

  const nodeContent = (
    <div
      data-node-type="decision"
      data-status={data.status}
      data-view-state={data.viewState}
      style={{
        minWidth: 220,
        opacity: isPlaceholder ? 0.4 : 1,
        border: isPlaceholder
          ? '1.5px dashed var(--color-placeholder-grey)'
          : '1.5px solid oklch(85% 0 0)',
        background: isPlaceholder ? 'var(--color-placeholder-grey)' : 'oklch(100% 0 0)',
        boxShadow: isPlaceholder ? 'none' : 'var(--shadow-node)',
      }}
      className="rounded-lg p-3 flex flex-col gap-2 transition-[box-shadow,border-color] duration-[var(--motion-duration-everyday)] hover:shadow-[var(--shadow-panel)]"
    >
      {/* Title — 2-line clamp */}
      {!isPlaceholder && (
        <p
          style={{
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
            fontSize: '0.8125rem',
            fontWeight: 600,
            lineHeight: 1.35,
            color: 'oklch(15% 0 0)',
            textDecoration: isRetracted ? 'line-through' : 'none',
            textDecorationColor: 'oklch(55% 0 0)',
          }}
          title={data.title}
        >
          {data.title}
        </p>
      )}

      {/* Status badge + captured date */}
      {!isPlaceholder && (
        <div className="flex items-center justify-between gap-2">
          <StatusBadge status={data.status} />
          <span
            className="text-[10px] shrink-0"
            style={{ color: 'oklch(58% 0 0)' }}
          >
            {formatRelative(data.capturedAt)}
          </span>
        </div>
      )}

      {/* Impacted systems chips */}
      {!isPlaceholder && data.impactedSystems.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-0.5">
          {visibleSystems.map((sys) => (
            <span
              key={sys}
              className="inline-block rounded-full px-2 py-px text-[9px] font-medium leading-tight"
              style={{
                background: 'oklch(93% 0.02 220)',
                color: 'oklch(40% 0.08 220)',
                border: '1px solid oklch(85% 0.04 220)',
              }}
            >
              {sys}
            </span>
          ))}
          {overflowCount > 0 && (
            <span
              className="inline-block rounded-full px-2 py-px text-[9px] font-medium leading-tight"
              style={{
                background: 'oklch(93% 0 0)',
                color: 'oklch(50% 0 0)',
                border: '1px solid oklch(85% 0 0)',
              }}
            >
              +{overflowCount} more
            </span>
          )}
        </div>
      )}
    </div>
  );

  return (
    <>
      <Handle type="target" position={Position.Left} />

      {isPlaceholder ? (
        nodeContent
      ) : (
        <NodeTooltip
          title={data.title}
          body={
            <TooltipBody
              rationale={data.rationale}
              alternatives={data.alternatives}
              authorName={data.authorName}
            />
          }
          side="right"
        >
          {nodeContent}
        </NodeTooltip>
      )}

      <Handle type="source" position={Position.Right} />
    </>
  );
});
