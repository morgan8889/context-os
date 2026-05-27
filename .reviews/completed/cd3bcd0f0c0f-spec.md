# Spec Review — cd3bcd0f0c0f

**Commit**: fix(topology): replace React Flow ghost canvas with SVG placeholder in empty state
**Branch**: 4-closed-beta-readiness
**Spec**: specs/005-goal-driven-ux/spec.md (Phase 5 spec covers TopologyEmpty)

---

## Spec Coverage Assessment

This is a bug-fix commit that replaces a broken React Flow canvas with an SVG
placeholder. The Phase 5 spec does not prescribe the internal implementation of
TopologyEmpty — only the user-facing requirements (empty state with explanatory copy
and a CTA to the Executive Briefing workflow).

| # | Criterion | Status | Test? | Evidence |
|---|-----------|--------|-------|----------|
| 1 | TopologyEmpty shows explanatory copy about workflow patterns | YES | NO | TopologyEmpty.tsx:23–27 |
| 2 | CTA "View Executive Briefing" navigates to inbox?filter=briefing | YES | NO | TopologyEmpty.tsx:29–32 |
| 3 | Empty state renders without viewport clipping at 768px/1440px | YES (commit intent) | NO visual reg | commit msg |
| 4 | SVG placeholder is marked aria-hidden | YES | NO | TopologyEmpty.tsx:45 |
| 5 | React Flow and WorkflowNode imports removed (no dead bundle weight) | YES | N/A | diff hunk |

## Deviations

None. The copy and CTA are preserved exactly. The implementation change is transparent
to users. The prior React Flow canvas was not a spec requirement — it was an
implementation choice that caused regressions.

## Missing Test Coverage

- No visual regression snapshot updated for this change.
- The commit message cites viewport failures at 768px and 1440px but no Playwright
  fixture is added or updated to guard against regression.
