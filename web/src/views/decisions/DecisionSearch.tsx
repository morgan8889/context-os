import { useEffect, useRef, useState } from 'react';
import { useGraphInteractionStore } from '@/lib/stores/graphInteraction';

/** Inline SVG spinner for the search-in-progress indicator */
function SearchSpinner() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 14 14"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className="animate-spin"
      style={{ color: 'oklch(50% 0 0)' }}
    >
      <circle
        cx="7"
        cy="7"
        r="5.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeOpacity="0.3"
      />
      <path
        d="M7 1.5A5.5 5.5 0 0 1 12.5 7"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

/** Inline SVG magnifying glass icon */
function SearchIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 14 14"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <circle cx="6" cy="6" r="4.5" stroke="oklch(65% 0 0)" strokeWidth="1.5" />
      <path
        d="M9.5 9.5L12.5 12.5"
        stroke="oklch(65% 0 0)"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

interface DecisionSearchProps {
  /** Whether a search query fetch is currently in-flight */
  isSearching: boolean;
  /** Total number of matching decisions (shown when query non-empty) */
  resultCount: number;
}

/**
 * DecisionSearch — controlled search input for the Decision Graph view.
 *
 * Maintains local state for instant UI feedback and debounces (300ms)
 * the dispatch to the Zustand store. Shows a spinner when isSearching,
 * a result-count badge when a query is active, and a clear button.
 */
export function DecisionSearch({ isSearching, resultCount }: DecisionSearchProps) {
  const setDecisionFilters = useGraphInteractionStore((s) => s.setDecisionFilters);
  const storedQuery = useGraphInteractionStore((s) => s.decisionFilters.query);

  // Local value for immediate UI updates
  const [localValue, setLocalValue] = useState(storedQuery);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Sync local value if store is cleared externally
  useEffect(() => {
    setLocalValue(storedQuery);
  }, [storedQuery]);

  function handleChange(value: string) {
    setLocalValue(value);
    if (debounceRef.current !== null) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setDecisionFilters({ query: value });
    }, 300);
  }

  function handleClear() {
    if (debounceRef.current !== null) clearTimeout(debounceRef.current);
    setLocalValue('');
    setDecisionFilters({ query: '' });
  }

  const hasQuery = localValue.length > 0;

  return (
    <div className="flex items-center gap-2">
      {/* Input wrapper */}
      <div
        className="relative flex items-center"
        style={{ minWidth: 240 }}
      >
        {/* Leading icon */}
        <span className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2">
          <SearchIcon />
        </span>

        <input
          type="search"
          role="searchbox"
          aria-label="Search decisions"
          placeholder="Search decisions…"
          value={localValue}
          onChange={(e) => handleChange(e.target.value)}
          className={[
            'w-full rounded-lg py-1.5 pl-8 pr-8 text-sm',
            'border transition-[border-color,box-shadow] duration-[var(--motion-duration-everyday)]',
            'focus:outline-none focus:ring-2',
          ].join(' ')}
          style={{
            borderColor: 'oklch(82% 0 0)',
            color: 'oklch(20% 0 0)',
            background: 'oklch(100% 0 0)',
            // focus styles via JS class
          }}
          onFocus={(e) => {
            e.currentTarget.style.borderColor = 'oklch(60% 0.15 220)';
            e.currentTarget.style.boxShadow = '0 0 0 3px oklch(60% 0.15 220 / 0.15)';
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = 'oklch(82% 0 0)';
            e.currentTarget.style.boxShadow = 'none';
          }}
        />

        {/* Trailing: spinner or clear button */}
        <span className="absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center">
          {isSearching ? (
            <SearchSpinner />
          ) : hasQuery ? (
            <button
              onClick={handleClear}
              aria-label="Clear search"
              className="flex items-center justify-center rounded p-px"
              style={{ color: 'oklch(55% 0 0)', lineHeight: 1 }}
            >
              <span style={{ fontSize: 14, lineHeight: 1 }}>&#215;</span>
            </button>
          ) : null}
        </span>
      </div>

      {/* Result count badge */}
      {hasQuery && !isSearching && (
        <span
          className="text-xs font-medium rounded-full px-2 py-0.5 shrink-0"
          style={{
            background: 'oklch(93% 0.02 220)',
            color: 'oklch(40% 0.08 220)',
            border: '1px solid oklch(85% 0.04 220)',
          }}
        >
          {resultCount} decision{resultCount !== 1 ? 's' : ''} match
        </span>
      )}
    </div>
  );
}
