import { describe, it, expect, vi, beforeEach } from 'vitest';

/**
 * T054 — Animation utility unit tests.
 * Verifies GSAP stateTransitions module and Framer Motion/GSAP coexistence constraints.
 */

// Mock GSAP before importing the module under test
const mockTimeline = {
  fromTo: vi.fn().mockReturnThis(),
  to: vi.fn().mockReturnThis(),
};

const gsapMock = {
  fromTo: vi.fn(),
  to: vi.fn(),
  timeline: vi.fn(() => mockTimeline),
};

vi.mock('gsap', () => ({ default: gsapMock }));

import { animateStateEnter, animateStateExit } from '@/lib/animations/stateTransitions';

describe('animateStateEnter', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls gsap.fromTo on the provided element', () => {
    const el = document.createElement('div');
    animateStateEnter(el);
    expect(gsapMock.fromTo).toHaveBeenCalledTimes(1);
    expect(gsapMock.fromTo).toHaveBeenCalledWith(el, expect.any(Object), expect.any(Object));
  });

  it('animates from opacity 0 scale 0.96 to opacity 1 scale 1', () => {
    const el = document.createElement('div');
    animateStateEnter(el);
    const [, fromVars, toVars] = gsapMock.fromTo.mock.calls[0] as [unknown, Record<string, unknown>, Record<string, unknown>];
    expect(fromVars.opacity).toBe(0);
    expect(fromVars.scale).toBe(0.96);
    expect(toVars.opacity).toBe(1);
    expect(toVars.scale).toBe(1);
  });

  it('uses 0.5s duration (500ms set-piece token)', () => {
    const el = document.createElement('div');
    animateStateEnter(el);
    const [, , toVars] = gsapMock.fromTo.mock.calls[0] as [unknown, unknown, Record<string, unknown>];
    expect(toVars.duration).toBe(0.5);
  });

  it('uses power2.out easing', () => {
    const el = document.createElement('div');
    animateStateEnter(el);
    const [, , toVars] = gsapMock.fromTo.mock.calls[0] as [unknown, unknown, Record<string, unknown>];
    expect(toVars.ease).toBe('power2.out');
  });
});

describe('animateStateExit', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls gsap.to on the provided element', () => {
    const el = document.createElement('div');
    animateStateExit(el);
    expect(gsapMock.to).toHaveBeenCalledTimes(1);
    expect(gsapMock.to).toHaveBeenCalledWith(el, expect.any(Object));
  });

  it('animates to opacity 0 and scale 0.96 (reverse of enter)', () => {
    const el = document.createElement('div');
    animateStateExit(el);
    const [, toVars] = gsapMock.to.mock.calls[0] as [unknown, Record<string, unknown>];
    expect(toVars.opacity).toBe(0);
    expect(toVars.scale).toBe(0.96);
  });

  it('uses 0.5s duration', () => {
    const el = document.createElement('div');
    animateStateExit(el);
    const [, toVars] = gsapMock.to.mock.calls[0] as [unknown, Record<string, unknown>];
    expect(toVars.duration).toBe(0.5);
  });

  it('uses power2.in easing (reverse direction)', () => {
    const el = document.createElement('div');
    animateStateExit(el);
    const [, toVars] = gsapMock.to.mock.calls[0] as [unknown, Record<string, unknown>];
    expect(toVars.ease).toBe('power2.in');
  });
});

describe('GSAP / Framer Motion coexistence — static analysis', () => {
  /**
   * These tests scan source files to verify that no DOM element is targeted by both
   * GSAP and Framer Motion animations in the same component.
   *
   * Rule: GSAP uses containerRef (wraps the whole view); Framer Motion uses motion.*
   * primitives for inner elements. They must not share the same ref.
   */
  it('GalaxyView — containerRef is passed to useGSAP scope, not to any motion.* element', async () => {
    const fs = await import('fs');
    const path = await import('path');
    const filePath = path.resolve(__dirname, '../../src/views/galaxy/GalaxyView.tsx');
    const content = fs.readFileSync(filePath, 'utf-8');

    // containerRef should appear in useGSAP scope
    expect(content).toMatch(/useGSAP.*scope.*containerRef/s);

    // containerRef should be on a plain div, not a motion.div
    const containerRefUsage = content.match(/ref={containerRef}/g) ?? [];
    expect(containerRefUsage.length).toBeGreaterThanOrEqual(1);

    // No motion.div should use containerRef
    expect(content).not.toMatch(/motion\.[a-z]+[^>]*ref={containerRef}/);
  });

  it('TopologyView — containerRef used in useGSAP scope, not in Framer Motion elements', async () => {
    const fs = await import('fs');
    const path = await import('path');
    const filePath = path.resolve(__dirname, '../../src/views/topology/TopologyView.tsx');
    const content = fs.readFileSync(filePath, 'utf-8');

    expect(content).toMatch(/useGSAP/);
    expect(content).toMatch(/animateStateEnter/);
    expect(content).not.toMatch(/motion\.[a-z]+[^>]*ref={containerRef}/);
  });

  it('DecisionView — containerRef used in useGSAP scope, not in Framer Motion elements', async () => {
    const fs = await import('fs');
    const path = await import('path');
    const filePath = path.resolve(__dirname, '../../src/views/decisions/DecisionView.tsx');
    const content = fs.readFileSync(filePath, 'utf-8');

    expect(content).toMatch(/useGSAP/);
    expect(content).toMatch(/animateStateEnter/);
    expect(content).not.toMatch(/motion\.[a-z]+[^>]*ref={containerRef}/);
  });

  it('TimeTravelBar — GSAP used for scrubber handle, Framer Motion not present', async () => {
    const fs = await import('fs');
    const path = await import('path');
    const filePath = path.resolve(__dirname, '../../src/views/galaxy/TimeTravelBar.tsx');
    const content = fs.readFileSync(filePath, 'utf-8');

    expect(content).toMatch(/useGSAP/);
    // TimeTravelBar should not import framer-motion
    expect(content).not.toMatch(/from ['"]framer-motion['"]/);
  });
});
