import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { StateCTA } from '@/design-system/primitives/StateCTA';

/**
 * TopologyEmpty — shown when the topology view state is 'empty'.
 *
 * Renders a faint workflow-graph SVG placeholder behind a centered CTA card.
 * Replacing the prior React Flow canvas avoids viewport-clipping and z-index
 * issues across breakpoints.
 */
export default function TopologyEmpty() {
  const navigate = useNavigate();

  return (
    <motion.div
      data-view="topology-empty"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3, ease: [0.0, 0, 0.2, 1] }}
      style={{
        height: '100%',
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--color-galaxy-bg, oklch(8% 0 0))',
        overflow: 'hidden',
      }}
    >
      {/* Placeholder workflow-graph silhouette */}
      <div
        aria-hidden="true"
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          pointerEvents: 'none',
        }}
      >
        <svg
          width="100%"
          height="400"
          viewBox="0 0 640 400"
          style={{ maxWidth: 640, opacity: 0.12 }}
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Edges */}
          <line x1="100" y1="200" x2="220" y2="120" stroke="var(--color-placeholder-grey)" strokeWidth="2" />
          <line x1="100" y1="200" x2="220" y2="200" stroke="var(--color-placeholder-grey)" strokeWidth="2" />
          <line x1="100" y1="200" x2="220" y2="280" stroke="var(--color-placeholder-grey)" strokeWidth="2" />
          <line x1="260" y1="120" x2="380" y2="160" stroke="var(--color-placeholder-grey)" strokeWidth="2" />
          <line x1="260" y1="200" x2="380" y2="160" stroke="var(--color-placeholder-grey)" strokeWidth="2" />
          <line x1="260" y1="200" x2="380" y2="240" stroke="var(--color-placeholder-grey)" strokeWidth="2" />
          <line x1="260" y1="280" x2="380" y2="240" stroke="var(--color-placeholder-grey)" strokeWidth="2" />
          <line x1="420" y1="160" x2="540" y2="200" stroke="var(--color-placeholder-grey)" strokeWidth="2" />
          <line x1="420" y1="240" x2="540" y2="200" stroke="var(--color-placeholder-grey)" strokeWidth="2" />
          {/* Nodes — rounded rects */}
          <rect x="60" y="175" width="80" height="50" rx="8" fill="var(--color-placeholder-grey)" />
          <rect x="220" y="95" width="80" height="50" rx="8" fill="var(--color-placeholder-grey)" />
          <rect x="220" y="175" width="80" height="50" rx="8" fill="var(--color-placeholder-grey)" />
          <rect x="220" y="255" width="80" height="50" rx="8" fill="var(--color-placeholder-grey)" />
          <rect x="380" y="135" width="80" height="50" rx="8" fill="var(--color-placeholder-grey)" />
          <rect x="380" y="215" width="80" height="50" rx="8" fill="var(--color-placeholder-grey)" />
          <rect x="500" y="175" width="80" height="50" rx="8" fill="var(--color-placeholder-grey)" />
        </svg>
      </div>

      {/* CTA card */}
      <div
        style={{
          position: 'relative',
          zIndex: 10,
          maxWidth: 440,
          textAlign: 'center',
          background: 'oklch(12% 0.005 250 / 0.95)',
          borderRadius: '0.75rem',
          padding: '1.5rem',
          border: '1px solid oklch(22% 0 0)',
        }}
      >
        <p
          className="text-sm text-[oklch(65%_0_0)] leading-relaxed mb-4"
          style={{ padding: '0 0.25rem' }}
        >
          Workflows derive from your team's coordination patterns. Executive Briefing
          is active by default; others appear as patterns emerge.
        </p>
        <StateCTA
          label="View Executive Briefing"
          onClick={() => navigate('/inbox?filter=briefing')}
        />
      </div>
    </motion.div>
  );
}
