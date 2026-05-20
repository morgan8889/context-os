import { useState, useCallback } from 'react';
import { useGraphInteractionStore } from '@/lib/stores/graphInteraction';

interface UseTimeTravelScrubResult {
  /** ISO timestamp strings for each available snapshot */
  timestamps: string[];
  /** Index of the currently displayed snapshot (-1 means live) */
  currentIndex: number;
  /** Navigate to snapshot at the given index */
  scrubTo: (index: number) => void;
  /** True when time travel is active (cursor is not at live position) */
  isActive: boolean;
}

/**
 * useTimeTravelScrub — manages time-travel state for the galaxy.
 *
 * Reads snapshots from the Zustand store.
 * scrubTo(index) pauses ForceAtlas2 (via setGalaxyTimeCursor) and
 * imports the snapshot at that index.
 * Calling scrubTo with the last index (or index = -1) resets to live.
 */
export function useTimeTravelScrub(): UseTimeTravelScrubResult {
  const galaxySnapshots = useGraphInteractionStore((s) => s.galaxySnapshots);
  const setGalaxyTimeCursor = useGraphInteractionStore((s) => s.setGalaxyTimeCursor);
  const galaxyTimeCursor = useGraphInteractionStore((s) => s.galaxyTimeCursor);

  const [currentIndex, setCurrentIndex] = useState<number>(-1);

  const timestamps = galaxySnapshots.map((s) => s.timestamp);
  const lastIndex = timestamps.length - 1;

  const isActive = galaxyTimeCursor !== null;

  const scrubTo = useCallback(
    (index: number) => {
      // Clamp to valid range
      const clamped = Math.max(0, Math.min(index, lastIndex));

      if (clamped === lastIndex || index === -1) {
        // Reset to live
        setCurrentIndex(-1);
        setGalaxyTimeCursor(null);
        return;
      }

      const timestamp = timestamps[clamped];
      if (!timestamp) return;

      setCurrentIndex(clamped);
      setGalaxyTimeCursor(timestamp);
    },
    [timestamps, lastIndex, setGalaxyTimeCursor]
  );

  return {
    timestamps,
    currentIndex,
    scrubTo,
    isActive,
  };
}
