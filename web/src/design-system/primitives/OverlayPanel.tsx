import { type ReactNode, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface OverlayPanelProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}

export function OverlayPanel({ open, onClose, title, children }: OverlayPanelProps) {
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15, ease: [0.0, 0, 0.2, 1] }}
            className="fixed inset-0 z-40 bg-[var(--color-backdrop)]"
            onClick={onClose}
          />
          {/* Panel */}
          <motion.div
            key="panel"
            initial={{ x: 320 }}
            animate={{ x: 0 }}
            exit={{ x: 320 }}
            transition={{ duration: 0.15, ease: [0.0, 0, 0.2, 1] }}
            className={[
              'fixed right-0 top-0 z-50 h-full',
              'w-[var(--overlay-panel-width)] max-w-full',
              'bg-[var(--color-overlay-panel-bg)] shadow-[var(--shadow-panel)]',
              'flex flex-col overflow-hidden',
            ].join(' ')}
            role="dialog"
            aria-modal="true"
            aria-label={title}
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-black/10 px-4 py-3 shrink-0">
              <h2 className="text-sm font-semibold">{title}</h2>
              <button
                onClick={onClose}
                className={[
                  'rounded p-1 text-[oklch(50%_0_0)]',
                  'hover:bg-black/5 hover:text-[oklch(20%_0_0)]',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500',
                  'transition-colors duration-[var(--motion-duration-everyday)]',
                ].join(' ')}
                aria-label="Close panel"
              >
                ✕
              </button>
            </div>
            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4">{children}</div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
