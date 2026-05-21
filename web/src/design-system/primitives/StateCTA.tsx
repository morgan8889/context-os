import { motion } from 'framer-motion';

interface StateCTAProps {
  label: string;
  onClick: () => void;
  description?: string;
}

export function StateCTA({ label, onClick, description }: StateCTAProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.15,
        ease: [0.0, 0, 0.2, 1], /* --motion-easing-everyday */
      }}
      className="flex flex-col items-center gap-3"
    >
      {description && (
        <p className="text-sm text-center text-[oklch(50%_0_0)] max-w-xs">{description}</p>
      )}
      <button
        data-cta="primary"
        onClick={onClick}
        className={[
          'inline-flex items-center justify-center rounded-lg px-6 py-3',
          'bg-blue-600 text-white text-sm font-medium',
          'hover:bg-blue-700 active:bg-blue-800',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2',
          'transition-colors duration-[var(--motion-duration-everyday)]',
          'shadow-sm',
        ].join(' ')}
      >
        {label}
      </button>
    </motion.div>
  );
}
