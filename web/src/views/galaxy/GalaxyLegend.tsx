import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const STORAGE_KEY = 'ctx_os_legend_galaxy';

const NODE_ENTRIES = [
  { token: '--color-node-goal', label: 'Goal' },
  { token: '--color-node-project', label: 'Project' },
  { token: '--color-node-signal', label: 'Signal' },
  { token: '--color-node-artifact', label: 'Artifact' },
] as const;

const STATUS_ENTRIES = [
  { token: '--color-status-active', label: 'Active' },
  { token: '--color-status-at-risk', label: 'At risk' },
  { token: '--color-status-paused', label: 'Paused' },
  { token: '--color-status-complete', label: 'Complete' },
] as const;

function getCSSToken(token: string): string {
  if (typeof window === 'undefined') return 'oklch(60% 0 0)';
  return getComputedStyle(document.documentElement).getPropertyValue(token).trim();
}

function ColorRow({ token, label }: { token: string; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <span
        aria-hidden="true"
        style={{
          width: 10,
          height: 10,
          borderRadius: '50%',
          background: getCSSToken(token),
          flexShrink: 0,
        }}
      />
      <span className="text-[11px]" style={{ color: 'oklch(70% 0 0)' }}>
        {label}
      </span>
    </div>
  );
}

export function GalaxyLegend() {
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    setExpanded(localStorage.getItem(STORAGE_KEY) === 'expanded');
  }, []);

  function toggle() {
    const next = !expanded;
    setExpanded(next);
    if (next) {
      localStorage.setItem(STORAGE_KEY, 'expanded');
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }

  const panelStyle = {
    background: 'oklch(12% 0 0 / 0.90)',
    backdropFilter: 'blur(12px)',
    border: '1px solid oklch(100% 0 0 / 0.08)',
    borderRadius: 10,
    boxShadow: 'var(--shadow-panel)',
  } as const;

  return (
    <div style={{ position: 'fixed', bottom: 24, right: 24, zIndex: 20 }}>
      <button
        type="button"
        onClick={toggle}
        aria-label="Toggle legend"
        aria-expanded={expanded}
        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 rounded-lg"
        style={{
          ...panelStyle,
          color: 'oklch(70% 0 0)',
          display: expanded ? 'none' : 'flex',
        }}
      >
        <span aria-hidden="true" style={{ fontSize: 11 }}>◈</span>
        Legend
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 4 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 4 }}
            transition={{ duration: 0.15, ease: [0.0, 0, 0.2, 1] }}
            style={{ ...panelStyle, width: 160, padding: '12px 14px' }}
          >
            {/* Header with collapse button */}
            <div className="flex items-center justify-between mb-2.5">
              <span className="text-[11px] font-semibold" style={{ color: 'oklch(70% 0 0)' }}>
                ◈ Legend
              </span>
              <button
                type="button"
                onClick={toggle}
                aria-label="Collapse legend"
                className="focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-500 rounded"
                style={{ color: 'oklch(50% 0 0)', lineHeight: 1 }}
              >
                <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true">
                  <path d="M2 4l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none" />
                </svg>
              </button>
            </div>

            {/* Node types */}
            <p className="text-[10px] font-semibold uppercase tracking-wide mb-1.5" style={{ color: 'oklch(45% 0 0)' }}>
              Nodes
            </p>
            <div className="flex flex-col gap-1 mb-3">
              {NODE_ENTRIES.map(({ token, label }) => (
                <ColorRow key={token} token={token} label={label} />
              ))}
            </div>

            {/* Status */}
            <p className="text-[10px] font-semibold uppercase tracking-wide mb-1.5" style={{ color: 'oklch(45% 0 0)' }}>
              Status
            </p>
            <div className="flex flex-col gap-1">
              {STATUS_ENTRIES.map(({ token, label }) => (
                <ColorRow key={token} token={token} label={label} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
