import { useEffect, useRef } from 'react';
import { useLoadGraph, useSigma } from '@react-sigma/core';
import { useWorkerLayoutForceAtlas2 } from '@react-sigma/layout-forceatlas2';
import { useGraphInteractionStore } from '@/lib/stores/graphInteraction';
import { buildGalaxyGraph } from '@/views/galaxy/buildGalaxyGraph';
import type Graph from 'graphology';

interface ForceLayoutProps {
  /** The graphology Graph instance to render */
  graph: Graph;
}

/**
 * ForceLayout — renderless component that manages ForceAtlas2 LayoutSupervisor.
 *
 * Must be rendered as a child of SigmaContainer.
 * Runs the layout supervisor in a Web Worker via useWorkerLayoutForceAtlas2.
 * Pauses the supervisor during time-travel scrub (when galaxyTimeCursor is set).
 * Resumes when time cursor resets to null.
 */
export function ForceLayout({ graph }: ForceLayoutProps) {
  const loadGraph = useLoadGraph();
  const sigma = useSigma();
  const galaxyTimeCursor = useGraphInteractionStore((s) => s.galaxyTimeCursor);
  const galaxySnapshots = useGraphInteractionStore((s) => s.galaxySnapshots);
  const prevCursorRef = useRef<string | null>(null);

  const { start, stop, isRunning } = useWorkerLayoutForceAtlas2({
    settings: {
      slowDown: 3,
      gravity: 0.05,
      scalingRatio: 2.0,
    },
  });

  // Load the graph when it changes
  useEffect(() => {
    loadGraph(graph, true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [graph]);

  // Start layout after graph loads (on first mount only)
  useEffect(() => {
    // Small delay to let Sigma process the loaded graph
    const timer = setTimeout(() => {
      if (!isRunning) {
        start();
      }
    }, 50);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Time-travel: pause during scrub, import snapshot, resume on reset
  useEffect(() => {
    const wasActive = prevCursorRef.current !== null;
    const isNowActive = galaxyTimeCursor !== null;

    if (isNowActive && !wasActive) {
      // Entering time-travel: stop layout
      stop();
    }

    if (isNowActive && galaxyTimeCursor) {
      // Import the snapshot for this cursor
      const snapshot = galaxySnapshots.find((s) => s.timestamp === galaxyTimeCursor);
      if (snapshot) {
        const snapshotGraph = buildGalaxyGraph(snapshot.nodes, snapshot.edges);
        loadGraph(snapshotGraph, true);
        sigma.getCamera().animate({ ratio: sigma.getCamera().ratio }, { duration: 300 });
      }
    }

    if (!isNowActive && wasActive) {
      // Leaving time-travel: restore live graph and restart layout
      loadGraph(graph, true);
      start();
    }

    prevCursorRef.current = galaxyTimeCursor;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [galaxyTimeCursor]);

  // Let layout converge, then stop it and fit the camera to frozen positions.
  useEffect(() => {
    const timer = setTimeout(() => {
      stop();

      const camera = sigma.getCamera();
      const cam = camera.getState();
      const { width, height } = sigma.getDimensions();
      const bbox = sigma.getBBox();

      const tl = sigma.graphToViewport({ x: bbox.x[0], y: bbox.y[0] });
      const br = sigma.graphToViewport({ x: bbox.x[1], y: bbox.y[1] });

      const bboxW = Math.abs(br.x - tl.x);
      const bboxH = Math.abs(br.y - tl.y);
      const vcx = (tl.x + br.x) / 2;
      const vcy = (tl.y + br.y) / 2;

      const normCx = ((vcx - width / 2) * cam.ratio) / width + cam.x;
      const normCy = ((vcy - height / 2) * cam.ratio) / height + cam.y;

      const fill = 0.85;
      const ratioX = (bboxW * cam.ratio) / (fill * width);
      const ratioY = (bboxH * cam.ratio) / (fill * height);
      const ratio = Math.max(ratioX, ratioY, 0.05);

      camera.animate({ x: normCx, y: normCy, ratio }, { duration: 600 });
    }, 5000);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Stop supervisor on unmount
  useEffect(() => {
    return () => {
      stop();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return null;
}
