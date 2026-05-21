import { motion } from 'framer-motion';

export interface FilterOption {
  value: string;
  label: string;
}

export interface FilterGroup {
  key: string;
  label: string;
  options: FilterOption[];
}

interface FilterBarProps {
  filters: FilterGroup[];
  activeFilters: Record<string, string>;
  onChange: (key: string, value: string) => void;
  onClear?: () => void;
}

export function FilterBar({ filters, activeFilters, onChange, onClear }: FilterBarProps) {
  const hasActive = Object.values(activeFilters).some(Boolean);

  return (
    <>
      {/*
       * Responsive styles for FilterBar:
       *  ≤430px (portrait mobile / landscape mobile):
       *    - filter labels are hidden, only chips remain visible
       *    - the row scrolls horizontally rather than wrapping
       */}
      <style>{`
        @media (max-width: 430px) {
          [data-filter-bar] .filter-label { display: none; }
          [data-filter-bar] { flex-wrap: nowrap; overflow-x: auto; -webkit-overflow-scrolling: touch; scrollbar-width: none; }
          [data-filter-bar]::-webkit-scrollbar { display: none; }
        }
      `}</style>

      <div
        data-filter-bar
        role="group"
        aria-label="Filters"
        className="flex items-center gap-3 flex-wrap px-3 py-2 border-b border-black/10 bg-white"
      >
        {filters.map((group) => (
          <div key={group.key} className="flex items-center gap-1 shrink-0">
            <span className="filter-label text-xs text-[oklch(50%_0_0)] font-medium shrink-0">
              {group.label}:
            </span>
            <div className="flex gap-1 flex-wrap">
              {group.options.map((option) => {
                const isActive = activeFilters[group.key] === option.value;
                return (
                  <motion.button
                    key={option.value}
                    onClick={() => onChange(group.key, isActive ? '' : option.value)}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className={[
                      'rounded-full px-2.5 py-0.5 text-xs font-medium',
                      'border transition-colors duration-[var(--motion-duration-everyday)]',
                      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500',
                      isActive
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-white text-[oklch(40%_0_0)] border-black/20 hover:border-blue-400',
                    ].join(' ')}
                    aria-pressed={isActive}
                  >
                    {option.label}
                  </motion.button>
                );
              })}
            </div>
          </div>
        ))}

        {hasActive && onClear && (
          <button
            onClick={onClear}
            className="text-xs text-blue-600 hover:text-blue-800 focus-visible:outline-none focus-visible:underline ml-1 shrink-0"
          >
            Clear all
          </button>
        )}
      </div>
    </>
  );
}
