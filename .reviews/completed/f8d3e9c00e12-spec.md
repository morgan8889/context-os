# Spec Compliance Review: f8d3e9c00e12 (Phase 5 Goal-Driven UX — Specification Files)
**Verdict**: CONDITIONAL PASS
**Date**: 2026-05-21

## Summary

Commit adds 7 specification files for Phase 5 Goal-Driven UX. The review checks
whether plan.md, research.md, data-model.md, contracts/ui-components.md,
quickstart.md, and checklists/requirements.md correctly operationalize spec.md.

All 14 FRs are addressed with one exception: plan.md InboxView implementation
instructions omit the `ctx_os_visited_inbox` orientation callout, creating a gap
against FR-001.

## Critical Finding

### FR-001 Inbox Orientation Callout Missing from InboxView Implementation Instructions
**Confidence**: 85

`spec.md` FR-001 requires a one-time orientation message on first visit to Galaxy,
Topology, Decisions, OR Inbox. US1 acceptance scenario 4 confirms Inbox must receive
an orientation message explaining the approval workflow.

plan.md Callout Copy Reference table correctly defines two Inbox callouts:
- `ctx_os_visited_inbox` — "Your Approval Queue" (view orientation)
- `ctx_os_inbox_hint` — "Your first approval" (tactical first-item hint)

data-model.md Entity 1 also documents `ctx_os_visited_inbox` correctly.

However, plan.md InboxView modifications section only instructs mounting
`<FirstVisitCallout storageKey="ctx_os_inbox_hint" ...>`. The `ctx_os_visited_inbox`
callout has no corresponding mount instruction. quickstart.md Scenario 5 likewise
only exercises `ctx_os_inbox_hint`.

A developer following the InboxView modification instructions would produce an Inbox
view missing its orientation callout, partially violating FR-001.

**Fix**: Add a `<FirstVisitCallout storageKey="ctx_os_visited_inbox" title="Your
Approval Queue" ...>` mount instruction to the InboxView modifications section.

## FR Coverage

| FR  | Description                                           | Status  |
|-----|-------------------------------------------------------|---------|
| FR-001 | One-time orientation message for all four views    | PARTIAL |
| FR-002 | Message includes purpose, object type, primary action | PASS |
| FR-003 | Dismissal persistent per view                      | PASS    |
| FR-004 | Tooltip per Galaxy overlay control                 | PASS    |
| FR-005 | Galaxy legend maps node-type colours + status      | PASS    |
| FR-006 | Galaxy legend collapsible + persistent             | PASS    |
| FR-007 | Inbox type badge accessible explanation            | PASS    |
| FR-008 | Failure flag contextual explanation                | PASS    |
| FR-009 | Live pending count badge in nav                    | PASS    |
| FR-010 | Persistent help/docs link in nav                   | PASS    |
| FR-011 | Galaxy empty state honest + functional CTA         | PASS    |
| FR-012 | Decisions empty state honest + no broken CTA       | PASS    |
| FR-013 | Operator language in all copy                      | PASS    |
| FR-014 | WCAG AA contrast for new elements                  | PASS    |

## Notes

- tasks.md noted as "not yet created" — expected at this stage. Not a gap.
- Legend edge case (updating on active overlay) has no contract mechanism; spec
  frames this as an edge case. Below threshold.
