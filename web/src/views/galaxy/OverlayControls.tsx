import { motion } from 'framer-motion';
import { useGraphInteractionStore } from '@/lib/stores/graphInteraction';
import { Tooltip } from '@/design-system/components/Tooltip';
import type { OverlayType } from '@/types/galaxy';

interface OverlayButton {
  type: OverlayType;
  label: string;
  tooltip: string;
}

const OVERLAY_BUTTONS: OverlayButton[] = [
  {
    type: 'load',
    label: 'Load',
    tooltip: 'Workload overlay — darker nodes carry more active work. Identify overloaded teams.',
  },
  {
    type: 'risk',
    label: 'Risk',
    tooltip: 'Risk overlay — red = flagged at-risk, amber = moderate risk.',
  },
  {
    type: 'autonomy',
    label: 'Autonomy',
    tooltip: 'Autonomy overlay — shows AI autonomy level per initiative (0–5 scale).',
  },
  {
    type: 'ownership',
    label: 'Ownership',
    tooltip: 'Ownership overlay — colours initiatives by owning team. Spot ownership gaps.',
  },
];

/**
 * OverlayControls — toolbar for toggling galaxy overlay modes.
 *
 * Four toggle buttons: Load, Risk, Autonomy, Ownership.
 * Clicking an active button deactivates it. Clicking an inactive one
 * activates it with default thresholds { low: 0.3, high: 0.7 }.
 * Uses Framer Motion layout animation for button state transitions.
 */
export function OverlayControls() {
  const galaxyOverlay = useGraphInteractionStore((s) => s.galaxyOverlay);
  const setGalaxyOverlay = useGraphInteractionStore((s) => s.setGalaxyOverlay);

  const handleToggle = (type: OverlayType) => {
    if (galaxyOverlay.type === type) {
      // Toggle off
      setGalaxyOverlay({ type: null, thresholds: { low: 0.3, high: 0.7 } });
    } else {
      setGalaxyOverlay({ type, thresholds: { low: 0.3, high: 0.7 } });
    }
  };

  return (
    <div
      className="flex flex-col gap-1 rounded-xl p-2"
      style={{
        background: 'oklch(12% 0 0 / 0.85)',
        backdropFilter: 'blur(12px)',
        border: '1px solid oklch(100% 0 0 / 0.08)',
        boxShadow: 'var(--shadow-panel)',
      }}
      role="group"
      aria-label="Overlay controls"
    >
      {OVERLAY_BUTTONS.map(({ type, label, tooltip }) => {
        const isActive = galaxyOverlay.type === type;

        return (
          <div key={type} className="flex flex-col items-center gap-0.5">
            <Tooltip content={tooltip} side="right" delayDuration={500}>
              <motion.button
                layout
                onClick={() => handleToggle(type)}
                aria-pressed={isActive}
                aria-label={`${label} overlay${isActive ? ' (active)' : ''}`}
                className={[
                  'relative flex h-10 w-10 items-center justify-center rounded-lg',
                  'text-xs font-semibold transition-colors',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500',
                ].join(' ')}
                style={{
                  background: isActive
                    ? `var(--color-overlay-${type}, oklch(55% 0.2 220))`
                    : 'transparent',
                  color: isActive ? 'oklch(95% 0 0)' : 'oklch(60% 0 0)',
                  border: isActive
                    ? `1px solid var(--color-overlay-${type}, oklch(55% 0.2 220))`
                    : '1px solid oklch(100% 0 0 / 0.1)',
                }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                transition={{ duration: 0.15, ease: [0.0, 0, 0.2, 1] }}
              >
                <OverlayIcon type={type} />
              </motion.button>
            </Tooltip>

            <span
              className="text-[10px] leading-tight text-center"
              style={{ color: isActive ? 'oklch(75% 0 0)' : 'oklch(45% 0 0)' }}
            >
              {label}
            </span>
          </div>
        );
      })}
    </div>
  );
}

/** Compact icon per overlay type */
function OverlayIcon({ type }: { type: OverlayType }) {
  switch (type) {
    case 'load':
      return (
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
          <rect x="2" y="10" width="3" height="4" rx="0.5" />
          <rect x="6.5" y="7" width="3" height="7" rx="0.5" />
          <rect x="11" y="4" width="3" height="10" rx="0.5" />
        </svg>
      );
    case 'risk':
      return (
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
          <path d="M8 2L14.93 14H1.07L8 2z" />
          <rect x="7.25" y="7" width="1.5" height="3.5" rx="0.5" fill="oklch(8% 0 0)" />
          <circle cx="8" cy="12" r="0.75" fill="oklch(8% 0 0)" />
        </svg>
      );
    case 'autonomy':
      return (
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
          <circle cx="8" cy="8" r="5.5" stroke="currentColor" strokeWidth="1.5" fill="none" />
          <circle cx="8" cy="8" r="2" />
        </svg>
      );
    case 'ownership':
      return (
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
          <circle cx="8" cy="5.5" r="2.5" />
          <path d="M2.5 13c0-3.04 2.46-5.5 5.5-5.5s5.5 2.46 5.5 5.5" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" />
        </svg>
      );
  }
}
