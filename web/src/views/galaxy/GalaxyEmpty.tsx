import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { StateCTA } from '@/design-system/primitives/StateCTA';

/**
 * GalaxyEmpty — shown when the galaxy view state is 'empty'.
 *
 * Renders a dark canvas with a faint placeholder galaxy silhouette,
 * explanatory copy, and a CTA to configure data sources.
 */
export default function GalaxyEmpty() {
  const navigate = useNavigate();

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.0, 0, 0.2, 1] }}
      data-state="empty"
      className="relative flex h-full w-full flex-col items-center justify-center overflow-hidden"
      style={{ background: 'var(--color-galaxy-bg, oklch(8% 0 0))' }}
    >
      {/* Placeholder galaxy silhouette */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 flex items-center justify-center"
      >
        <svg
          width="600"
          height="600"
          viewBox="0 0 600 600"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          style={{ opacity: 0.15 }}
        >
          {/* Core glow */}
          <ellipse
            cx="300"
            cy="300"
            rx="18"
            ry="18"
            fill="var(--color-placeholder-grey)"
            style={{ filter: 'blur(6px)' }}
          />
          {/* Spiral arm 1 — sweeping left-up */}
          <path
            d="M 300 300 Q 240 250 160 180 Q 120 150 80 100"
            stroke="var(--color-placeholder-grey)"
            strokeWidth="28"
            strokeLinecap="round"
            fill="none"
            style={{ filter: 'blur(12px)' }}
          />
          {/* Spiral arm 2 — sweeping right-down */}
          <path
            d="M 300 300 Q 360 350 440 420 Q 480 450 520 500"
            stroke="var(--color-placeholder-grey)"
            strokeWidth="28"
            strokeLinecap="round"
            fill="none"
            style={{ filter: 'blur(12px)' }}
          />
          {/* Spiral arm 3 — sweeping right-up */}
          <path
            d="M 300 300 Q 370 240 440 160 Q 480 110 510 70"
            stroke="var(--color-placeholder-grey)"
            strokeWidth="20"
            strokeLinecap="round"
            fill="none"
            style={{ filter: 'blur(14px)' }}
          />
          {/* Spiral arm 4 — sweeping left-down */}
          <path
            d="M 300 300 Q 230 360 160 440 Q 120 490 90 530"
            stroke="var(--color-placeholder-grey)"
            strokeWidth="20"
            strokeLinecap="round"
            fill="none"
            style={{ filter: 'blur(14px)' }}
          />
          {/* Scatter nodes along arms */}
          {[
            [200, 220], [160, 185], [120, 150],
            [400, 380], [440, 415], [490, 460],
            [380, 200], [430, 155], [470, 110],
            [220, 380], [175, 430], [135, 475],
          ].map(([cx, cy], i) => (
            <circle
              key={i}
              cx={cx}
              cy={cy}
              r={3 + (i % 3)}
              fill="var(--color-placeholder-grey)"
              style={{ filter: 'blur(1px)' }}
            />
          ))}
        </svg>
      </div>

      {/* Content */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15, duration: 0.35, ease: [0.0, 0, 0.2, 1] }}
        className="relative z-10 flex flex-col items-center gap-6 px-6 text-center"
      >
        <div className="flex flex-col gap-2">
          <h1
            className="text-xl font-semibold tracking-tight"
            style={{ color: 'var(--color-placeholder-grey)' }}
          >
            Your organizational initiatives appear here as a living constellation.
          </h1>
          <p
            className="text-sm max-w-sm leading-relaxed"
            style={{ color: 'oklch(60% 0 0)' }}
          >
            Add your first initiative to activate the galaxy.
          </p>
        </div>

        <StateCTA
          label="Adjust source scope"
          onClick={() => navigate('/settings/sources')}
        />
      </motion.div>
    </motion.div>
  );
}
