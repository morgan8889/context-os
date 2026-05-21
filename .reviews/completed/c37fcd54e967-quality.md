# Code Quality Review: c37fcd54e967 (Phase 7)
**Verdict**: PASS WITH NOTES
**Reviewer**: inline review
**Date**: 2026-05-20

## Summary

Phase 7 completes the feature implementation across telemetry, inbox UX, responsive
breakpoints, design review documentation, and test/TypeScript hygiene. The OTEL module
is cleanly isolated with singleton state and a silent failure contract. The Inbox view
correctly separates optimistic local state from server state using a pattern consistent
with Phase 2 approval workflow design.

## Findings

### Minor

**QC-P7-001**: `InboxView.tsx` — The `useInfiniteQuery` pattern for inbox pagination is
correct but the optimistic update on approve/reject modifies Zustand store state rather
than TanStack Query cache. This is intentional for UI responsiveness but means a hard
refresh will re-show items until the next `invalidateQueries`. Acceptable for MVP but
worth noting for future work.

**QC-P7-002**: `otel.ts` module-level singleton (`_endpoint`, `_tenantId`) is not
reset between tests. In production this is fine (single-page lifetime), but unit tests
that import `otel.ts` after `initOtel` may see stale state. The module exports functions
not a class, so resetting requires re-importing. Not blocking since telemetry has no
unit tests in this PR.

**QC-P7-003**: `responsive.spec.ts` uses `page.setViewportSize` with hardcoded pixel
values (430, 768, 1024) that must match the CSS breakpoints in inline `<style>` blocks.
If breakpoints change in CSS, tests will need manual sync. Acceptable for now.

## GSAP / Framer Motion Partition (unchanged from Phase 5)

All partition rules maintained — no new violations.

## TypeScript Hygiene

`vi.hoisted()` fix for `animations.test.ts` is the idiomatic Vitest solution for
pre-hoisting mock objects. Using `vi.hoisted()` over restructuring the mock factory
avoids future regressions from the same pattern.

## Responsive Implementation Pattern

Using inline `<style>` JSX for breakpoint-specific overrides (rather than a CSS
module or Tailwind breakpoint utilities) is consistent with the established pattern
in this codebase for view-specific media queries that can't be expressed as utility
classes. No issues.
