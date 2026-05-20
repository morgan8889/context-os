import type { CSSProperties } from 'react';
import { useGraphInteractionStore } from '@/lib/stores/graphInteraction';
import { OverlayPanel } from '@/design-system/primitives/OverlayPanel';
import type { InitiativeNode, InitiativeType, InitiativeStatus } from '@/types/galaxy';

interface NodeDetailPaneProps {
  /** The node data to display, looked up from the graph */
  node: InitiativeNode | null;
}

const TYPE_LABELS: Record<InitiativeType, string> = {
  goal: 'Goal',
  project: 'Project',
  signal: 'Signal',
  artifact: 'Artifact',
};

const STATUS_LABELS: Record<InitiativeStatus, string> = {
  active: 'Active',
  paused: 'Paused',
  complete: 'Complete',
  at_risk: 'At Risk',
};

const STATUS_COLORS: Record<InitiativeStatus, string> = {
  active: 'var(--color-status-active)',
  paused: 'var(--color-status-paused)',
  at_risk: 'var(--color-status-at-risk)',
  complete: 'var(--color-status-complete)',
};

const TYPE_COLORS: Record<InitiativeType, string> = {
  goal: 'var(--color-node-goal)',
  project: 'var(--color-node-project)',
  signal: 'var(--color-node-signal)',
  artifact: 'var(--color-node-artifact)',
};

/**
 * NodeDetailPane — slide-in panel showing initiative details.
 *
 * Opens when focusedNodeId is set in the Zustand store.
 * Closes when focusedNodeId is cleared or the panel Escape/close is triggered.
 */
export function NodeDetailPane({ node }: NodeDetailPaneProps) {
  const setFocusedNodeId = useGraphInteractionStore((s) => s.setFocusedNodeId);
  const focusedNodeId = useGraphInteractionStore((s) => s.focusedNodeId);
  const open = focusedNodeId !== null && node !== null;

  if (!open || !node) return null;

  return (
    <OverlayPanel
      open={open}
      onClose={() => setFocusedNodeId(null)}
      title={node.label}
    >
      <div className="flex flex-col gap-4">
        {/* Badges row */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Type badge */}
          <span
            className="rounded-full px-2.5 py-0.5 text-xs font-semibold"
            style={{
              background: `color-mix(in oklch, ${TYPE_COLORS[node.type]}, transparent 80%)`,
              color: TYPE_COLORS[node.type],
              border: `1px solid color-mix(in oklch, ${TYPE_COLORS[node.type]}, transparent 60%)`,
            }}
          >
            {TYPE_LABELS[node.type]}
          </span>

          {/* Status badge */}
          <span
            className="rounded-full px-2.5 py-0.5 text-xs font-semibold"
            style={{
              background: `color-mix(in oklch, ${STATUS_COLORS[node.status]}, transparent 80%)`,
              color: STATUS_COLORS[node.status],
              border: `1px solid color-mix(in oklch, ${STATUS_COLORS[node.status]}, transparent 60%)`,
            }}
          >
            {STATUS_LABELS[node.status]}
          </span>
        </div>

        {/* Metadata rows */}
        <dl className="flex flex-col gap-2.5">
          {node.ownerTeam && (
            <DetailRow label="Owner team" value={node.ownerTeam} />
          )}
          <DetailRow label="Actors" value={String(node.actorCount)} />
          {node.riskScore !== null && (
            <DetailRow
              label="Risk"
              value={`Risk: ${node.riskScore.toFixed(2)}`}
              valueStyle={{ color: node.riskScore >= 0.7 ? 'var(--color-status-at-risk)' : undefined }}
            />
          )}
          {node.autonomyLevel !== null && (
            <DetailRow label="Autonomy" value={`Autonomy: L${node.autonomyLevel}`} />
          )}
          <DetailRow label="Connections" value={`Connections: ${node.edgeCount}`} />
        </dl>
      </div>
    </OverlayPanel>
  );
}

interface DetailRowProps {
  label: string;
  value: string;
  valueStyle?: CSSProperties;
}

function DetailRow({ label, value, valueStyle }: DetailRowProps) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <dt className="text-xs font-medium" style={{ color: 'oklch(50% 0 0)' }}>
        {label}
      </dt>
      <dd className="text-sm font-medium text-right" style={valueStyle}>
        {value}
      </dd>
    </div>
  );
}
