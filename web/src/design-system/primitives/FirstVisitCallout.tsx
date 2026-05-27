import { useState, useEffect, useCallback, type CSSProperties } from 'react';
import { AnimatePresence, motion } from 'framer-motion';

interface FirstVisitCalloutProps {
  storageKey: string;
  title: string;
  description: string;
  dismissLabel?: string;
  position?: 'bottom-left' | 'bottom-center';
}

export function FirstVisitCallout({
  storageKey,
  title,
  description,
  dismissLabel = 'Got it',
  position = 'bottom-left',
}: FirstVisitCalloutProps) {
  const [visible, setVisible] = useState(
    () => localStorage.getItem(storageKey) !== 'true'
  );

  const dismiss = useCallback(() => {
    localStorage.setItem(storageKey, 'true');
    setVisible(false);
  }, [storageKey]);

  useEffect(() => {
    if (!visible) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') dismiss();
    }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [visible, dismiss]);

  const positionStyle: CSSProperties =
    position === 'bottom-left'
      ? { position: 'fixed', bottom: 24, left: 'calc(56px + 24px)', zIndex: 30 }
      : { position: 'relative', zIndex: 30 };

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 8 }}
          transition={{ duration: 0.15, ease: [0.0, 0, 0.2, 1] }}
          style={{
            ...positionStyle,
            width: 280,
            background: 'oklch(100% 0 0)',
            border: '1px solid oklch(90% 0 0)',
            borderRadius: 12,
            boxShadow: 'var(--shadow-panel)',
            padding: '16px',
          }}
          role="complementary"
          aria-label={title}
        >
          <p
            className="text-sm font-semibold mb-1"
            style={{ color: 'oklch(15% 0 0)' }}
          >
            {title}
          </p>
          <p className="text-xs leading-relaxed mb-3" style={{ color: 'oklch(42% 0 0)' }}>
            {description}
          </p>
          <button
            type="button"
            onClick={dismiss}
            aria-label="Dismiss orientation message"
            className="rounded-md px-3 py-1.5 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            style={{
              background: 'oklch(96% 0 0)',
              color: 'oklch(35% 0 0)',
              border: '1px solid oklch(88% 0 0)',
            }}
          >
            {dismissLabel}
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
