# PRD Amendment — New-User Activation as Workflow Transformation

**Date**: 2026-05-17
**Author**: Nick Morgan (with Claude, via `superpowers:brainstorming`)
**Status**: Approved design; ready for implementation planning
**Target file for amendment**: `/Users/nick/Code/context-os/docs/prd.md`
**Constitution**: This amendment is governed by `.specify/memory/constitution.md` v1.1.0+

## Context

The Context-OS PRD (v1.0, merged 2026-05-17) describes ongoing-user
features well but never specifies the activation experience. The
closed-beta target (3–5 orgs) makes this a load-bearing gap: without a
defined activation story, 1–2 of those orgs will likely be lost to
week-1 friction.

The reframe that drove this design — surfaced during brainstorming —
is that **the new-user gap is not a configuration problem; it is a
workflow-transformation problem**. Operators are not "setting up
software"; they are being introduced to a different way of working.
Onboarding must teach the new way, not just expose the tool.

The author chose **fully self-serve** activation (not founder-led),
accepting the +5–7 weeks of MVP timeline impact (~36 wk → ~42–43 wk)
because validating that the product can onboard without founder
intervention is part of the MVP thesis.

## Design decisions (locked through brainstorming dialogue)

| Decision | Choice |
|---|---|
| Activation model | Fully self-serve |
| Approach | **A — Workflow-First Activation** (one transformed workflow carries activation), with B's library framing and C's discovery survey embedded |
| Time-to-value frame | Reimagined workflows, not "minutes to dashboard" |
| Mismatch handling (operator picked non-briefing pain) | Proceed with briefing flow + gentle forward reference |
| Activation metrics visibility | Platform Operator only |
| Activation completion target | ≥ 80% of recruited beta cohort |

## The Workflow-First Activation journey (operator-facing)

Seven steps. **The activation moment is approval of the first briefing**,
not arrival at a populated view.

1. **Sign-up frame.** Sign-up page states the transformation thesis in
   plain language:
   *"Right now your weekly briefing takes ~60 minutes to write.
   Context-OS drafts it in 5 from your Jira / GitHub / Slack; you
   review and approve."*
   No feature list. The thesis is named on entry.
2. **Discovery survey.** One question after Clerk-mediated account
   creation:
   *"Which part of your week would you most want to change?"*
   Five options (briefings, dependencies, decision retrieval,
   architecture-review cycle time, something-else). Captured per-org;
   feeds §9.6 falsification criterion #3.
3. **Minimum integrations for the workflow.** Three OAuth cards
   (Jira, GitHub, Slack) framed as workflow-inputs, not "integration
   setup." Each card non-destructive; partial success acceptable.
4. **Scope selection in workflow terms.**
   *"Which initiatives should your briefing cover?"*
   Pre-selected projects/repos/channels with recent activity; operator
   confirms or trims.
5. **Ingest as workflow priming.** Progress bar with explicit framing:
   *"Reading your last 7 days of work."*
   Leave-and-return supported; completion notification by email. On
   complete, summary:
   *"Found {N} initiatives, {M} PRs, {K} active threads."*
6. **First briefing — the activation moment.** Briefing draft arrives
   end of day 1, honestly labeled *"first briefing, low signal."*
   Operator reviews, edits, approves. **Approval is the activation
   event.** Confirmation copy:
   *"You just did in 5 minutes what used to take 60. Scheduled for
   Fridays at 9am from now on; pause or change anytime."*
7. **Progressive disclosure of secondary surfaces.** After activation,
   Initiative Galaxy / Workflow Topology / Decision Graph become
   accessible via nav. No tour. Each surface has its own empty /
   activating / activated states (see "Empty states" below).

## Copy patterns

**Before/after as the activation primitive.** Every prompt and progress
moment is framed as *what the operator used to do* vs *what they're
doing now*.

| Moment | Copy |
|---|---|
| Sign-up | *"Right now your weekly briefing takes ~60 minutes. Context-OS drafts it in 5; you review and approve."* |
| Connect prompt | *"To draft your briefing, Context-OS needs to see what's happening. Three sources, OAuth — same way Slack connects."* |
| Ingest complete | *"Found 14 initiatives, 47 PRs, 23 active threads. Drafting your first briefing now."* |
| Briefing approved | *"You just did in 5 minutes what used to take 60. From now on Friday 9am; change or pause anytime."* |

**Workflow library framing.** The Executive Briefing workflow is named
on every surface — the operator learns Context-OS *runs workflows*, not
*is* one workflow. A `Workflows` nav item lists active workflows
(length-1 in MVP); empty-state copy:
*"Executive Briefing is your first. Architecture Review, Dependency
Discovery, and others arrive as the platform matures."*
One forward reference on the discovery-survey mismatch screen; no
list of future workflows with dates.

**Tone guardrails (every copy string passes three filters):**
1. **Operator language** — *"briefing", "review", "dependency"*. Not
   *"streamline", "unlock", "empower", "AI-powered"*.
2. **Specific, not generic** — *"60 minutes"* not *"a lot of time."*
3. **Honest about state** — *"first briefing, low signal"*, *"fills in
   as your team works."* No pretending.

**Aging strategy.** Activation-only copy lives in onboarding flow and
dismisses on completion. Persistent copy is written to age —
*"fills in as your team works"* still works at month 6.

## Empty / activating / activated view states

**Cross-view design system commitments (extends §6.3):**

- No spinners as primary feedback; loading scoped to elements (e.g.,
  ingest progress bars).
- Empty/activating states share the visual language of activated
  states — same typography, color tokens, canvas treatment. Difference
  is *content present*, not *rendering quality*.
- Every state surfaces **exactly one** primary action.
- Copy is honest about *why* empty — *"ingest still discovering"* vs
  *"your team hasn't captured decisions yet"* are different conditions
  with different next actions.
- "Placeholder-grey" treatment for example/anticipated content —
  visually clearly distinct from live data, structurally identical.

**Per-view state specs:**

### Initiative Galaxy (§8.3.4)
| State | Trigger | Visual | Copy | Primary action |
|---|---|---|---|---|
| Empty | 0 initiatives after ingest | Galaxy canvas with faint placeholder constellations, slowly animated | *"Your initiatives will appear here as Context-OS reads your work. If sources are connected and this is still empty, scope may need adjusting."* | "Adjust source scope" |
| Activating | 1–9 initiatives, ingest in progress | Initiatives render as discovered; placeholders resolve into them | *"Discovering your initiatives. {N} found so far. Estimated {time} remaining."* | "Notify me when done" |
| Activated | ≥10 initiatives | Per §8.3.4 functional acceptance | (none) | (none) |

### Workflow Topology (§8.3.5)
| State | Trigger | Visual | Copy | Primary action |
|---|---|---|---|---|
| Empty | 0 workflows | Executive Briefing rendered as dimmed seed node | *"Workflows derive from your team's coordination patterns. Executive Briefing is active by default; others appear as patterns emerge."* | "View Executive Briefing" |
| Activating | 1–9 workflows | No density-collapse; faint anticipated workflows hinted | *"{N} workflows mapped. More will be discovered."* | "See what's been discovered" |
| Activated | ≥10 workflows | Per §8.3.5 | (none) | (none) |

### Decision Graph (§8.3.6)
| State | Trigger | Visual | Copy | Primary action |
|---|---|---|---|---|
| Empty | 0 decisions | Two example decision nodes in placeholder-grey | *"Decisions accumulate as your team captures them. Context-OS proposes decisions from briefing reviews — each approval becomes a decision in your graph."* | "Capture a decision manually" |
| Activating | 1–19 decisions | Full dagre layout, no collapse | *"Your decision history is building. {N} captured so far."* | (none) |
| Activated | ≥20 decisions | Per §8.3.6 | (none) | (none) |

## Discovery survey signal + activation metrics + §9.6 feedback loop

**Discovery survey output.** One string per beta org. Surfaces in
three places:
1. **In the operator's own admin module** — *"You told us {X} when
   you signed up. We're starting with briefings; here's where {X}
   sits."*
2. **In the Platform Operator's admin view** — aggregated cohort
   table.
3. **In the §9.6 wedge decision memo** — one of three data sources at
   end of closed beta.

**Falsification feedback loop, explicit:**
- **Criterion #1 (ICP fit fails)** — survey result is a sanity check.
- **Criterion #3 (function mismatch)** — promoted from end-of-beta
  signal to week-1 signal:
  *"If < 30% of orgs name briefings as their top pain across the
  cohort, the function is wrong."*
  This is measurable as soon as the 3rd beta org signs up.

**Activation metrics block (new in §9.5):**

| Metric | Target |
|---|---|
| Sign-up email click → sign-up button click | observe, no target |
| Sign-up → integration-connect complete (active attention) | < 15 min |
| Connect-complete → ingest-complete (wall-clock) | < 30 min typical, < 24 hr worst |
| Ingest-complete → first-briefing approval (active attention) | < 15 min |
| Total wall-clock sign-up → activation | < 24 hr |
| Total active attention sign-up → activation | < 30 min |
| Activation completion rate (cohort) | ≥ 80% |
| Drop-off at any single step | < 10% |
| Day-1 support contact rate | < 30% of cohort |
| Time from activation to 2nd-week briefing | scheduled 7 days; measure attended / edited rate |
| Operator's first briefing accept-as-is rate | ≥ 30% (lower than ongoing ≥ 40%; cold-start is real) |

Visible to Platform Operator only.

## Phase impact and audit adjustments

**Timeline distribution** (the +5–7 wk is *distributed*, not
concentrated in Phase 4):

| Phase | Original | Added work | New estimate |
|---|---|---|---|
| Phase 1 — Foundation | 9 wk | — | 9 wk |
| Phase 2 — Intelligence | 9 wk | + first-briefing low-signal handling, eval baseline, partial-data recovery | +1 wk → **10 wk** |
| Phase 3 — Cognition Surface | 10 wk | + empty/activating states; placeholder-grey design system | +2 wk → **12 wk** |
| Phase 4 — Closed Beta Readiness | 8 wk | + Workflow-First Activation (§8.3.9); discovery survey; activation telemetry; admin surfaces; copy authoring; recovery paths | +3–4 wk → **11–12 wk** |
| **Total** | **36 wk** | **+6–7 wk** | **42–43 wk (~10 months)** |

Distribution beats concentration because empty/activating viz states
need to be designed together with activated states (Phase 3), not as a
Phase 4 retrofit that risks rebuilding what Phase 3 just shipped.

**§8.5 audit table additions:**
- First-briefing low-signal handling: +1 wk
- Empty / activating view states (3 views): +2 wk
- First-run experience (Workflow-First Activation): +3 wk
- Activation telemetry + admin surfaces: +1 wk
- Buffer reduced 8 → 6 wk (some absorbed)

## New / updated kill criteria (§8.6)

- **Activation completion rate < 60% by week 36** (mid-Phase 4) →
  drop fully-self-serve aspiration; fallback to founder-led with
  minimal first-run safety; replan Phase 4 around manual onboarding
  workflows.
- **Activation median time > 60 min active attention by week 38** →
  journey is wrong OR bar is unrealistic; explicit replan decision
  with operator.
- **Discovery survey reveals function mismatch by 3rd beta org**
  (briefing-pain < 30% of answers across first 3 orgs) → trigger early
  wedge memo (§9.6 criterion #3 confirmed); pause recruiting; consider
  pivot before completing cohort.

## New Open Questions (§13)

| OQ | Question | Section |
|---|---|---|
| OQ-023 | What's the right time-to-first-useful-briefing target — 1 day, 3 days, 7 days? | §8.7 |
| OQ-024 | When does the Workflows library become more than length-1? Threshold: feature-completeness of Architecture Review or Dependency Discovery. | §5.8 / §7.4 |
| OQ-025 | If activation completion lags 50–80%, is that a leading indicator that triggers schedule extension, or a fixed gate? | §8.7 |
| OQ-026 | What do we do about operators who activate but don't return for scheduled second briefing? Retention work or accept as week-1 signal? | §9.7 |

## Acceptance criteria for the amendment itself

What lands in `/Users/nick/Code/context-os/docs/prd.md` when execution
completes:

- **§4.1** — "Week 1 (activation)" sub-treatment added at end of
  Strategic Operator persona.
- **§5.7** — Three-state model (empty/activating/activated)
  acknowledged as cross-cutting concern; references §8.3.10.
- **§6.3** — Empty-state design system commitments added
  (placeholder-grey, one primary action per state, no spinners as
  primary feedback).
- **§7.2.1** — First-run variant of Executive Briefing specified
  (low-signal labeling, cold-start eval framing).
- **§8.3.9** — New First-run experience (Workflow-First Activation)
  feature with full Functional / Qualitative / Evaluation /
  Out-of-scope AC blocks.
- **§8.3.10** — New cross-view feature: Empty / activating view
  states, with per-view AC blocks.
- **§8.3.4–6** — Empty/activating-state ACs appended to each existing
  view spec.
- **§8.5** — Audit table refactored per "Phase impact" above; total =
  41 wk raw / 42–43 wk phased.
- **§8.6** — Three new kill criteria added.
- **§8.7** — OQ-023, OQ-025 added.
- **§9.5** — New "Activation metrics" block (Platform-Operator-only
  visibility noted).
- **§9.6** — Criterion #3 (function mismatch) becomes measurable in
  week 1 via discovery survey threshold.
- **§9.7** — OQ-026 added.
- **§10** — Phase 2, 3, 4 scope and exit criteria updated per
  timeline distribution; Phase 4 onboarding-flow bullet expanded into
  sub-bullet structure.
- **§13** — OQ-023, 024, 025, 026 added; index resorted; resolution
  discipline note unchanged.
- **Header** — `Last updated` bumped.

## Critical files

- `/Users/nick/Code/context-os/docs/prd.md` — single file edited by
  the amendment.
- `/Users/nick/Code/context-os/.specify/memory/constitution.md`
  (v1.1.0) — no changes; Principles III (Human Governance, AI
  Execution) and IV (Visualization as Cognition) inform the framing.

## Next steps

1. Commit this design doc on the current feature branch.
2. Invoke `superpowers:writing-plans` against this design to produce
   the implementation plan with exact line-range targets in `prd.md`,
   commit sequence, and verification steps.
3. Execute via `superpowers:executing-plans` (separate session) or
   `superpowers:subagent-driven-development` (this session).
4. PR + squash-merge per the `main-protection` branch ruleset (PR
   required, linear history, no merge commits, admin can self-merge).

## When to revisit

- Once Phase 4 design begins, refine §8.3.9 against actual Clerk +
  OAuth flow timings; tighten time-to-value targets based on prototype
  data.
- If activation completion lags during closed beta, reopen OQ-025
  (leading indicator vs fixed gate).
- If the discovery survey clusters strongly on a non-briefing pain in
  the first 2–3 orgs, trigger the kill criterion before completing
  the cohort.
