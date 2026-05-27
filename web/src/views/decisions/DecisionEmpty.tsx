import { motion } from 'framer-motion';
import { StateCTA } from '@/design-system/primitives/StateCTA';

/**
 * DecisionEmpty — shown when the decision graph view state is 'empty'.
 *
 * Renders a blank canvas with a centered organizational tree silhouette
 * and honest copy about how decisions enter the graph via briefing approvals.
 */
export default function DecisionEmpty() {

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.35, ease: [0.0, 0, 0.2, 1] }}
      data-state="empty"
      className="relative flex h-full w-full flex-col items-center justify-center overflow-hidden"
      style={{ background: 'var(--color-galaxy-bg, oklch(8% 0 0))' }}
    >
      {/* Organizational tree silhouette */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 flex items-center justify-center"
      >
        <svg
          width="320"
          height="280"
          viewBox="0 0 320 280"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          style={{ opacity: 0.35 }}
        >
          {/* Root node */}
          <rect
            x="120"
            y="16"
            width="80"
            height="36"
            rx="6"
            fill="var(--color-placeholder-grey)"
          />

          {/* Vertical trunk */}
          <line
            x1="160"
            y1="52"
            x2="160"
            y2="100"
            stroke="var(--color-placeholder-grey)"
            strokeWidth="3"
            strokeLinecap="round"
          />

          {/* Horizontal branch bar */}
          <line
            x1="60"
            y1="100"
            x2="260"
            y2="100"
            stroke="var(--color-placeholder-grey)"
            strokeWidth="3"
            strokeLinecap="round"
          />

          {/* Left branch drop */}
          <line
            x1="60"
            y1="100"
            x2="60"
            y2="130"
            stroke="var(--color-placeholder-grey)"
            strokeWidth="3"
            strokeLinecap="round"
          />
          {/* Center branch drop */}
          <line
            x1="160"
            y1="100"
            x2="160"
            y2="130"
            stroke="var(--color-placeholder-grey)"
            strokeWidth="3"
            strokeLinecap="round"
          />
          {/* Right branch drop */}
          <line
            x1="260"
            y1="100"
            x2="260"
            y2="130"
            stroke="var(--color-placeholder-grey)"
            strokeWidth="3"
            strokeLinecap="round"
          />

          {/* Level-2 left node */}
          <rect
            x="20"
            y="130"
            width="80"
            height="32"
            rx="5"
            fill="var(--color-placeholder-grey)"
          />
          {/* Level-2 center node */}
          <rect
            x="120"
            y="130"
            width="80"
            height="32"
            rx="5"
            fill="var(--color-placeholder-grey)"
          />
          {/* Level-2 right node */}
          <rect
            x="220"
            y="130"
            width="80"
            height="32"
            rx="5"
            fill="var(--color-placeholder-grey)"
          />

          {/* Second-level trunks from left node */}
          <line
            x1="60"
            y1="162"
            x2="60"
            y2="196"
            stroke="var(--color-placeholder-grey)"
            strokeWidth="2"
            strokeLinecap="round"
          />
          <line
            x1="36"
            y1="196"
            x2="84"
            y2="196"
            stroke="var(--color-placeholder-grey)"
            strokeWidth="2"
            strokeLinecap="round"
          />
          <line
            x1="36"
            y1="196"
            x2="36"
            y2="214"
            stroke="var(--color-placeholder-grey)"
            strokeWidth="2"
            strokeLinecap="round"
          />
          <line
            x1="84"
            y1="196"
            x2="84"
            y2="214"
            stroke="var(--color-placeholder-grey)"
            strokeWidth="2"
            strokeLinecap="round"
          />
          <rect
            x="12"
            y="214"
            width="48"
            height="24"
            rx="4"
            fill="var(--color-placeholder-grey)"
          />
          <rect
            x="60"
            y="214"
            width="48"
            height="24"
            rx="4"
            fill="var(--color-placeholder-grey)"
          />

          {/* Second-level trunk from right node */}
          <line
            x1="260"
            y1="162"
            x2="260"
            y2="196"
            stroke="var(--color-placeholder-grey)"
            strokeWidth="2"
            strokeLinecap="round"
          />
          <rect
            x="236"
            y="196"
            width="48"
            height="24"
            rx="4"
            fill="var(--color-placeholder-grey)"
          />
        </svg>
      </div>

      {/* Content */}
      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.18, duration: 0.32, ease: [0.0, 0, 0.2, 1] }}
        className="relative z-10 flex flex-col items-center gap-6 px-6 text-center"
      >
        <h1
          className="text-lg font-semibold"
          style={{ color: 'oklch(85% 0 0)' }}
        >
          Decisions accumulate over time
        </h1>
        <p
          className="text-sm leading-relaxed max-w-sm"
          style={{ color: 'oklch(65% 0 0)' }}
        >
          Context-OS proposes decisions from briefing reviews — each approval
          becomes a node here. After your first briefing cycle, decisions will
          appear automatically.
        </p>
        <StateCTA
          label="Capture a decision manually"
          onClick={() => {
            /* manual capture flow ships in a later phase */
          }}
        />
      </motion.div>
    </motion.div>
  );
}
