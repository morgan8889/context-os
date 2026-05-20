import { useRef, useState, useCallback, useEffect } from 'react';
import type { ChangeEvent } from 'react';
import { useGSAP } from '@gsap/react';
import gsap from 'gsap';
import { useTimeTravelScrub } from './hooks/useTimeTravelScrub';

/** Format an ISO timestamp as "MMM D HH:mm" */
function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  const month = date.toLocaleString('en-US', { month: 'short' });
  const day = date.getDate();
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${month} ${day} ${hours}:${minutes}`;
}

/**
 * TimeTravelBar — slider for scrubbing through historical galaxy snapshots.
 *
 * Only rendered when snapshots.length >= 2.
 * Uses GSAP (via useGSAP) to animate the visual handle position.
 * A play/pause button auto-advances the cursor at 1 step per second.
 * ForceAtlas2 supervisor is paused during scrub (handled by ForceLayout).
 */
export function TimeTravelBar() {
  const { timestamps, currentIndex, scrubTo, isActive } = useTimeTravelScrub();
  const handleRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const total = timestamps.length;

  // Don't render when fewer than 2 snapshots available
  if (total < 2) return null;

  const lastIndex = total - 1;
  // -1 means "Live" position
  const displayIndex = currentIndex === -1 ? lastIndex : currentIndex;
  const pct = lastIndex > 0 ? (displayIndex / lastIndex) * 100 : 0;

  // GSAP animates the handle position
  const { contextSafe } = useGSAP({ scope: containerRef });

  const animateHandle = contextSafe((targetPct: number) => {
    if (handleRef.current) {
      gsap.to(handleRef.current, {
        left: `${targetPct}%`,
        duration: 0.3,
        ease: 'power2.out',
      });
    }
  });

  // Animate handle whenever displayIndex changes
  useEffect(() => {
    const newPct = lastIndex > 0 ? (displayIndex / lastIndex) * 100 : 0;
    animateHandle(newPct);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [displayIndex]);

  // Track current index in a ref for use inside setInterval callback
  const currentIndexRef = useRef(currentIndex);
  currentIndexRef.current = currentIndex;

  // Auto-play: advance 1 step per second
  const startPlaying = useCallback(() => {
    setIsPlaying(true);
    intervalRef.current = setInterval(() => {
      const ci = currentIndexRef.current;
      const nextIdx = ci === -1 ? 0 : ci + 1;

      if (nextIdx >= lastIndex) {
        // Reached live — stop
        scrubTo(-1);
        setIsPlaying(false);
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      } else {
        scrubTo(nextIdx);
      }
    }, 1000);
  }, [lastIndex, scrubTo]);

  const stopPlaying = useCallback(() => {
    setIsPlaying(false);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const handlePlayPause = () => {
    if (isPlaying) {
      stopPlaying();
    } else {
      // If at live position, start from beginning
      if (currentIndex === -1) {
        scrubTo(0);
      }
      startPlaying();
    }
  };

  // Clean up interval on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const handleRangeChange = (e: ChangeEvent<HTMLInputElement>) => {
    const idx = parseInt(e.target.value, 10);
    if (isPlaying) stopPlaying();
    // At max value → go live
    if (idx >= lastIndex) {
      scrubTo(-1);
    } else {
      scrubTo(idx);
    }
  };

  const firstLabel = timestamps[0] ? formatTimestamp(timestamps[0]) : '';

  return (
    <div
      className="flex items-center gap-3 px-4 py-3"
      style={{
        background: 'oklch(10% 0 0 / 0.9)',
        backdropFilter: 'blur(12px)',
        borderTop: '1px solid oklch(100% 0 0 / 0.08)',
      }}
    >
      {/* Play / Pause button */}
      <button
        onClick={handlePlayPause}
        aria-label={isPlaying ? 'Pause time travel' : 'Play time travel'}
        className={[
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-lg',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500',
          'transition-colors duration-[var(--motion-duration-everyday)]',
        ].join(' ')}
        style={{
          background: 'oklch(22% 0 0)',
          color: 'oklch(75% 0 0)',
          border: '1px solid oklch(100% 0 0 / 0.1)',
        }}
      >
        {isPlaying ? (
          // Pause icon
          <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
            <rect x="2" y="1.5" width="3" height="9" rx="0.5" />
            <rect x="7" y="1.5" width="3" height="9" rx="0.5" />
          </svg>
        ) : (
          // Play icon
          <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
            <path d="M2.5 1.5L10.5 6L2.5 10.5V1.5Z" />
          </svg>
        )}
      </button>

      {/* Left timestamp label */}
      <span
        className="shrink-0 text-[11px] tabular-nums"
        style={{ color: 'oklch(50% 0 0)' }}
      >
        {firstLabel}
      </span>

      {/* Slider track */}
      <div ref={containerRef} className="relative flex-1">
        {/* Native range input (accessible, hidden visually but functional) */}
        <input
          type="range"
          min={0}
          max={lastIndex}
          step={1}
          value={displayIndex}
          onChange={handleRangeChange}
          aria-label="Time travel scrubber"
          className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
          style={{ zIndex: 2 }}
        />

        {/* Visual track */}
        <div
          className="relative h-1 w-full rounded-full"
          style={{ background: 'oklch(25% 0 0)' }}
        >
          {/* Filled portion */}
          <div
            className="absolute inset-y-0 left-0 rounded-full"
            style={{
              width: `${pct}%`,
              background: isActive
                ? 'var(--color-node-project, oklch(60% 0.2 220))'
                : 'oklch(40% 0 0)',
            }}
          />

          {/* Animated handle (GSAP target) */}
          <div
            ref={handleRef}
            className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2"
            style={{
              left: `${pct}%`,
              width: 12,
              height: 12,
              borderRadius: '50%',
              background: isActive
                ? 'var(--color-node-project, oklch(60% 0.2 220))'
                : 'oklch(65% 0 0)',
              border: '2px solid oklch(90% 0 0)',
              boxShadow: '0 1px 4px oklch(0% 0 0 / 0.3)',
              pointerEvents: 'none',
              zIndex: 1,
            }}
          />
        </div>
      </div>

      {/* Right label: "Live" */}
      <span
        className="shrink-0 text-[11px] font-semibold"
        style={{
          color: isActive ? 'oklch(50% 0 0)' : 'var(--color-status-active)',
        }}
      >
        Live
      </span>
    </div>
  );
}
