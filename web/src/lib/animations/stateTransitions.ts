import gsap from 'gsap';

/**
 * GSAP set-piece entrance animation for view state changes.
 * Duration 500ms, power2.out easing — the "set-piece" motion token.
 * Only call this on container elements. Framer Motion owns component-level animations.
 */
export function animateStateEnter(element: Element): void {
  gsap.fromTo(
    element,
    { opacity: 0, scale: 0.96 },
    { opacity: 1, scale: 1, duration: 0.5, ease: 'power2.out', clearProps: 'transform' }
  );
}

/**
 * GSAP set-piece exit animation for view state changes.
 * Reverse of animateStateEnter.
 */
export function animateStateExit(element: Element): void {
  gsap.to(element, { opacity: 0, scale: 0.96, duration: 0.5, ease: 'power2.in' });
}
