# PRD New-User Amendment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Amend `/Users/nick/Code/context-os/docs/prd.md` to specify new-user activation as workflow transformation, per the approved design at `docs/plans/2026-05-17-prd-new-user-amendment-design.md`.

**Architecture:** Section-by-section edits to a single file (`docs/prd.md`). Each task targets one PRD subsection, applies the content specified in the design doc's "Acceptance criteria for the amendment itself" list, self-reviews against the design's content, and commits with a single-purpose message. Final task: PR creation per the `main-protection` branch ruleset (PR required, linear history — squash or rebase merge only, admin self-merge).

**Tech Stack:** Markdown. No code, no tests. Verification is `grep` for structural integrity (cross-refs, OQ index two-way consistency, section anchor resolution).

**Source documents:**
- **DESIGN-DOC**: `/Users/nick/Code/context-os/docs/plans/2026-05-17-prd-new-user-amendment-design.md` (committed at `b2a96ed`)
- **TARGET**: `/Users/nick/Code/context-os/docs/prd.md` (canonical PRD, currently 1881 lines)
- **CONSTITUTION**: `/Users/nick/Code/context-os/.specify/memory/constitution.md` v1.1.0

**Working state at plan time:**
- Branch: `feature/prd-new-user-amendment-design` (already created off `main` at `5fd5b1a`)
- Design doc commit: `b2a96ed`
- Working tree: clean
- Main has `main-protection` ruleset (PR required, linear history, admin bypass via PR mode)

**Commit prefix convention:** `docs(prd):` for all amendment commits, matching the PRD rewrite history.

---

## Pre-flight orientation (no commit)

### Task 0: Confirm branch and capture section line ranges

**Files:**
- Read: `docs/prd.md` (no modifications)

**Step 1: Confirm branch state**

```bash
git -C /Users/nick/Code/context-os branch --show-current
git -C /Users/nick/Code/context-os status
git -C /Users/nick/Code/context-os log --oneline -3
```

Expected:
- Branch: `feature/prd-new-user-amendment-design`
- Working tree clean
- Last commit: `b2a96ed docs: design for PRD new-user amendment (workflow-first activation)`

**Step 2: Capture current section line ranges**

Run this once and save the output for reference during edits:

```bash
grep -nE "^##? [0-9]+\.|^### [0-9]+\.[0-9]+|^#### [0-9]+\.[0-9]+\.[0-9]+" /Users/nick/Code/context-os/docs/prd.md
```

Expected output: a list of every heading line. Use these line numbers when targeting `Edit` insertion points in subsequent tasks. If any task's named section anchor doesn't appear, stop and ask — the PRD may have drifted.

**No commit. This is orientation only.**

---

## Section edits (one task per amendment, one commit per task)

### Task 1: §4.1 — Add "Week 1 (activation)" sub-treatment

**Files:**
- Modify: `docs/prd.md` — end of §4.1 Strategic Operator (before `### 4.2` heading)

**Source content (verbatim from DESIGN-DOC, embedded earlier in this PRD's content lifecycle):**

Insert after the existing "How MVP serves them" paragraph and before `### 4.2 Domain Practitioner`:

```markdown
**Week 1 (activation).** Same persona, distinct context. In their first
seven days the operator has no platform-built mental model yet, no
historical state, and limited patience: friction beyond value early kills
adoption. Day-1 pain points are different from ongoing pain — uncertainty
about what the platform does day-to-day, indecision about which sources
to connect first, impatience for first useful output, anxiety about
exposing org data to a new system.

What they need in week 1 (distinct from ongoing wants in the main bullet
list above):
- An obvious next action at every step of onboarding
- A defined time-to-value promise ("first useful briefing within 7 days")
- Visible progress during initial ingest
- Empty-state surfaces that teach, not just display blank canvas
- Reassurance that data scope, retention, and access are what they
  configured

How MVP serves week-1 Strategic Operators: see the First-run experience
feature spec at §8.3.9 and the Onboarding flow detail in §10 Phase 4.
```

**Self-review checklist:**
- [ ] Insertion is between the existing "How MVP serves them" paragraph and `### 4.2 Domain Practitioner` heading
- [ ] No existing §4.1 content was modified, only appended
- [ ] Forward references to §8.3.9 and §10 are intentional (those sections will exist after Tasks 7 and 13)

**Step: Edit, verify, commit**

```bash
# After Edit, verify the section grew without breaking adjacent sections
grep -nE "^### 4\." /Users/nick/Code/context-os/docs/prd.md
# Expected: §4.1, §4.2, §4.3, §4.4 still present, in order
```

```bash
git add docs/prd.md
git commit -m "docs(prd): §4.1 add Week 1 (activation) sub-treatment to Strategic Operator

Adds a distinct treatment for the operator in their first 7 days,
since day-1 pain points differ from ongoing pain. Forward-refs
§8.3.9 (First-run experience) and §10 Phase 4 (Onboarding flow).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 2: §5.7 — Acknowledge three-state model as cross-cutting concern

**Files:**
- Modify: `docs/prd.md` — within §5.7 Visualization Layer "Capabilities" or "AI/human boundary" area

**Insertion point:** At the end of §5.7's introductory description (before the MVP cut table). Add a short paragraph:

```markdown
**View states.** Every primary view (Initiative Galaxy, Workflow
Topology, Decision Graph) has three states: empty, activating, and
activated. State design — including the "placeholder-grey" treatment
for example/anticipated content and the one-primary-action rule — is
cross-cutting. See §6.3 for the design system commitments and §8.3.10
for the cross-view feature spec.
```

**Self-review checklist:**
- [ ] Paragraph appears in §5.7 (Visualization Layer), not §5.1–5.6
- [ ] Forward references to §6.3 and §8.3.10 land in subsequent tasks (3 and 8 respectively)
- [ ] No other §5.7 content modified

**Commit:**

```bash
git add docs/prd.md
git commit -m "docs(prd): §5.7 acknowledge three-state model as cross-cutting

Empty / activating / activated state model surfaces in §6.3 design
commitments and §8.3.10 cross-view feature.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 3: §6.3 — Add empty-state design system commitments

**Files:**
- Modify: `docs/prd.md` — within §6.3 Visualization architecture, in the "Design system commitments" block

**Insertion point:** Locate the bullet list under "Design system commitments" that currently includes Type / Color / Component primitives / Iconography / Motion tokens / Density modes / Accessibility. Append two new bullets:

```markdown
- **View states**: every primary view has three states (empty,
  activating, activated). Empty/activating states use a "placeholder-
  grey" treatment for example/anticipated content — visually distinct
  from live data, structurally identical. Every state surfaces exactly
  one primary action. Loading is scoped to elements (e.g., ingest
  progress bars), never as view-blocking overlays. Per-view AC
  specifications in §8.3.10.
- **Copy in topology**: state copy is honest about why empty — *"ingest
  still discovering"* vs *"your team hasn't captured decisions yet"* are
  distinct conditions with distinct next actions. Operator-language
  guardrails per §8.3.9 apply.
```

**Self-review checklist:**
- [ ] Appended to the existing "Design system commitments" bullet list, not as a new subsection
- [ ] Forward reference to §8.3.10 will resolve (Task 8 creates that section)
- [ ] Forward reference to §8.3.9 will resolve (Task 7 creates that section)

**Commit:**

```bash
git add docs/prd.md
git commit -m "docs(prd): §6.3 add view-state and copy commitments to design system

Two new commitments in the design system list: three-state model
(empty/activating/activated) with placeholder-grey treatment, and
operator-language copy guardrails for state surfaces.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 4: §7.2.1 — Add first-run variant of Executive Briefing

**Files:**
- Modify: `docs/prd.md` — at the end of §7.2.1 Executive Briefing (before §7.2.2 begins)

**Insertion content:** Append a sub-block titled "First-run variant" inside §7.2.1:

```markdown
**First-run variant (week 1 only).** The first briefing for a newly-
activated operator runs under modified contracts:

- **Inputs**: same shape but smaller window — last 7 days of ingestion
  only (one ingest cycle's worth), not the rolling 7-day window an
  ongoing briefing receives
- **Outputs**: briefing markdown carries an explicit header label
  *"First briefing — low signal. Data accumulates over the week."*
- **Eval**: accept-as-is target is ≥ 30%, not the ongoing ≥ 40%.
  Cold-start is real; the bar accommodates it without abandoning quality
  expectations
- **Telemetry**: first-run briefings emit a `first_run: true` field on
  their trace; activation metrics (§9.5) join against this for analysis
- **Failure mode added**: "claims about week-over-week trends" — week 1
  has no prior week to compare against. Detected by prompt-side
  constraint and by output filter.
```

**Self-review checklist:**
- [ ] Block appended inside §7.2.1, before `#### 7.2.2 Architecture Review`
- [ ] Numbers align with §9.5 (≥ 30% accept-as-is) and §9.5's ongoing rate (≥ 40%) referenced via §8.3.3 telemetry
- [ ] `first_run: true` telemetry field is novel; flagged for ingest into telemetry schema (no schema doc edit needed in this PRD)

**Commit:**

```bash
git add docs/prd.md
git commit -m "docs(prd): §7.2.1 add first-run variant of Executive Briefing

Modified eval bar (≥30% accept-as-is, not ≥40%) and explicit cold-start
labeling. Adds first_run telemetry field and a week-1-specific failure
mode (claims about week-over-week trends with no prior week).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 5: §8.3.4 / §8.3.5 / §8.3.6 — Append empty-state ACs to each view

**Files:**
- Modify: `docs/prd.md` — within Functional acceptance blocks of three view specs

This is one task with three parallel insertions because the structure is identical.

**Per-view insertion**: Append to the Functional acceptance bullet list of each view spec the bullets specified in DESIGN-DOC § "Empty / activating / activated view states". Specifically:

**§8.3.4 Initiative Galaxy — append to Functional acceptance:**
```markdown
- Empty state (0 initiatives): renders a placeholder-grey constellation
  surface with copy *"Your initiatives will appear here as Context-OS
  reads your work. If sources are connected and this is still empty,
  scope may need adjusting."* and primary action "Adjust source scope";
  not a blank canvas
- Activating state (1–9 initiatives during ingest): renders initiatives
  as discovered; placeholder constellations resolve into real nodes as
  they arrive; copy *"Discovering your initiatives. {N} found so far.
  Estimated {time} remaining."* with primary action "Notify me when
  done"
```

**§8.3.5 Workflow Topology view — append:**
```markdown
- Empty state (0 workflows): renders Executive Briefing workflow as a
  dimmed seed node; copy *"Workflows derive from your team's
  coordination patterns. Executive Briefing is active by default;
  others appear as patterns emerge."*; primary action "View Executive
  Briefing"
- Activating state (1–9 workflows): renders without density-collapse
  thresholds; faint anticipated workflows hinted; copy *"{N} workflows
  mapped. More will be discovered."*; primary action "See what's been
  discovered"
```

**§8.3.6 Decision Graph view — append:**
```markdown
- Empty state (0 decisions): renders two example decision nodes in
  placeholder-grey; copy *"Decisions accumulate as your team captures
  them. Context-OS proposes decisions from briefing reviews — each
  approval becomes a decision in your graph."*; primary action "Capture
  a decision manually"
- Activating state (1–19 decisions): full dagre layout, no cluster
  collapse; copy *"Your decision history is building. {N} captured so
  far."*
```

**Self-review checklist:**
- [ ] All three views received parallel-structured insertions
- [ ] No existing Functional acceptance bullets modified
- [ ] Copy strings match DESIGN-DOC verbatim (operator-language tone preserved)
- [ ] Each state names exactly one primary action (Decision Graph activating has none — confirmed deliberate)

**Commit:**

```bash
git add docs/prd.md
git commit -m "docs(prd): §8.3.4-6 append empty/activating state ACs

Each of Initiative Galaxy, Workflow Topology, and Decision Graph gets
two new bullets in Functional acceptance: empty state and activating
state. Copy and primary action specified per the design's tone
guardrails.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 6: §8.3.9 — Add First-run experience feature (Workflow-First Activation)

**Files:**
- Modify: `docs/prd.md` — insert as new subsection between §8.3.8 (Human approval surface) and §8.4 (Explicitly out of scope)

**Insertion content:** Full feature spec following the AC block format used throughout §8.3:

```markdown
#### 8.3.9 First-run experience (Workflow-First Activation)

The new operator's activation surface. Implements the seven-step
journey from DESIGN at `docs/plans/2026-05-17-prd-new-user-amendment-design.md`.
The activation moment is **approval of the first briefing**, not arrival
at a populated view (per §3.2 product principle Intent Over Tasks).

**Functional acceptance.**
- Sign-up frame: lands the operator on a screen that states the
  transformation thesis in plain language (before/after format per
  §6.3 copy guardrails); no feature list
- Discovery survey: one question after Clerk-mediated account creation,
  five options (briefings, dependencies, decision retrieval,
  architecture-review cycle time, something-else free-text); answer
  captured per-org, feeds §9.6 falsification criterion #3
- Integration connect wizard: three OAuth cards (Jira, GitHub, Slack)
  framed as workflow-inputs; each card non-destructive; partial success
  acceptable (skip-able per source with explicit warning)
- Scope selection in workflow terms: *"Which initiatives should your
  briefing cover?"* — projects (Jira) / repos (GitHub) / channels
  (Slack) with active-in-last-90-days pre-checked
- Ingest UX as workflow priming: progress bar with estimated time,
  leave-and-return supported, completion notification by email;
  completion summary copy *"Found {N} initiatives, {M} PRs, {K} active
  threads. Drafting your first briefing now."*
- First-briefing scheduling: triggered automatically at end of
  ingest-completion day; uses the first-run variant of Executive
  Briefing (per §7.2.1)
- Activation moment: first-briefing approval emits an `activation_event`
  trace; subsequent sessions present Initiative Galaxy / Workflow
  Topology / Decision Graph in the nav (per §8.3.10 progressive
  disclosure)
- Mismatch handling: operators who picked a non-briefing pain in the
  survey proceed with briefing flow + gentle forward-reference copy
  *"You picked {X}. We're starting with briefings. Here's where {X}
  sits."* with a single-line roadmap reference
- Recovery paths: each step (OAuth failure, ingest stall, briefing
  generation failure) has a documented recovery flow; total path
  branching ≤ 1 layer per step
- Time-to-completion: a new operator completes sign-up → integration
  connect → first populated view in < 30 minutes active attention,
  < 24 hours wall-clock

**Qualitative bar.**
- A new Strategic Operator completes onboarding without contacting
  support
- The activation moment (first briefing approval) feels earned, not
  empty — the operator immediately sees something specific to their org
- Empty intermediate states (during ingest) feel like progress, not
  failure
- The transformation thesis is named on entry and validated on exit
  ("you just did in 5 minutes what used to take 60")

**Evaluation.**
- End-to-end timing test: sign-up email click → first populated view,
  on representative source-data shapes; < 24 hours wall-clock,
  < 30 minutes active attention
- Dogfood-operator re-onboarding calibration: once during Phase 4 the
  Platform Operator onboards themselves to a fresh tenant as if a new
  operator; timings captured against §9.5 activation metrics block
- Beta-cohort completion rate: ≥ 80% of recruited orgs activate

**Out of scope for MVP.**
- SSO / SAML
- White-label or custom-domain onboarding
- Team invitations beyond a single operator per org (additional
  teammates added via Clerk admin only)
- Custom integration adapters beyond Jira / GitHub / Slack
- Bulk-import historical onboarding (e.g., "import last year's Jira"
  as a backfill — only forward sync is supported)
- Per-feature tours or in-product walkthroughs (the static doc-site
  getting-started page is the documentation surface)
```

**Self-review checklist:**
- [ ] Inserted as `#### 8.3.9`, between `#### 8.3.8` and `### 8.4`
- [ ] Forward references to §3.2, §6.3, §7.2.1, §8.3.10, §9.5, §9.6 all land in real sections (some after this task — Task 8 creates §8.3.10)
- [ ] AC block format matches §8.3.1–8 (Functional / Qualitative / Evaluation / Out of scope)
- [ ] References the design doc explicitly, with path

**Commit:**

```bash
git add docs/prd.md
git commit -m "docs(prd): §8.3.9 add First-run experience (Workflow-First Activation)

New MVP feature spec implementing the seven-step activation journey
designed in docs/plans/2026-05-17-prd-new-user-amendment-design.md.
Activation moment = approval of first briefing. Includes discovery
survey, mismatch handling, recovery paths, and dogfood-calibration eval.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 7: §8.3.10 — Add Empty / activating view states (cross-view feature)

**Files:**
- Modify: `docs/prd.md` — insert as new subsection between §8.3.9 (Task 6 just created) and §8.4

**Insertion content:**

```markdown
#### 8.3.10 Empty / activating view states (cross-view)

A cross-cutting feature spanning Initiative Galaxy (§8.3.4), Workflow
Topology (§8.3.5), and Decision Graph (§8.3.6). Per-view ACs were
appended to each view spec; this section specifies the cross-cutting
contract.

**Functional acceptance.**
- Three states per view: empty (zero data), activating (partial data
  during ingest or initial accumulation), activated (full data per
  view's own acceptance criteria)
- Placeholder-grey treatment: example/anticipated content rendered at
  a defined neutral lightness level, structurally identical to live
  content; clear visual delineation from live data without being a
  blank canvas
- One primary action per state: every state surfaces exactly one CTA;
  never zero, never two
- Honest copy: state copy names the specific reason for the state
  ("ingest still discovering" vs "your team hasn't captured decisions
  yet")
- Loading scoped to elements: progress bars on ingest/sync operations
  only; no view-blocking spinners
- State transitions: graceful animation between empty → activating →
  activated as data arrives; no flash-of-blank-content

**Qualitative bar.**
- Side-by-side with Linear or Notion empty states at internal review,
  the Context-OS state surfaces communicate more about *what will be
  here* and *what the operator can do*
- Empty states feel like *the surface is ready for content*, not *the
  surface is broken*

**Evaluation.**
- Visual regression tests for empty + activating states on each of the
  three views at three viewports (mobile-landscape, laptop, large
  display)
- Copy review against §6.3 tone guardrails (operator-language,
  specific not generic, honest about state)

**Out of scope for MVP.**
- State customization by operator (e.g., custom empty-state copy)
- A/B testing of state copy or actions
```

**Self-review checklist:**
- [ ] Inserted as `#### 8.3.10`, between `#### 8.3.9` (Task 6) and `### 8.4`
- [ ] References to per-view ACs (§8.3.4, .5, .6) all resolve — Task 5 added them
- [ ] Reference to §6.3 tone guardrails resolves — Task 3 added them

**Commit:**

```bash
git add docs/prd.md
git commit -m "docs(prd): §8.3.10 add cross-view Empty/activating state feature

Cross-cutting contract for the three-state model implemented in
§8.3.4-6. Specifies placeholder-grey treatment, one-primary-action
rule, honest copy, scoped loading, and graceful transitions. References
§6.3 design commitments for tone and §8.3.4-6 for per-view ACs.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 8: §8.5 — Adjust feasibility audit table

**Files:**
- Modify: `docs/prd.md` — within §8.5 Solo-build feasibility audit table

**Changes:**

1. Insert four new rows in the audit table (between "Briefing workflow E2E" and "Human approval surface"):

```markdown
| First-briefing low-signal handling (§7.2.1 variant) | 1 wk   | Cold-start eval framing |
| Empty / activating view states (3 views, §8.3.10) | 2 wk   | Placeholder-grey consistency |
| First-run experience (Workflow-First Activation, §8.3.9) | 3 wk   | Copy + journey UX bar |
| Activation telemetry + admin surfaces | 1 wk   | Plumbing across services |
```

2. Update the buffer row: change `Buffer (30%) | 8 wk` to `Buffer (~17%) | 6 wk`.

3. Update the total row: change `Total | 36 weeks (~8.3 months)` to `Total | 41 weeks (~9.5 months raw audit; ~42–43 wk phased per §10)`.

**Self-review checklist:**
- [ ] Four new rows inserted before "Human approval surface" row
- [ ] Buffer reduced 8 → 6 weeks
- [ ] Total updated to 41 wk raw / 42–43 wk phased, with note explaining the discrepancy
- [ ] Math: 3+3+5+5+3+2+3+1+2+3+1+1+2+1+6 = 41 ✓

**Commit:**

```bash
git add docs/prd.md
git commit -m "docs(prd): §8.5 expand feasibility audit for new-user amendment

Adds 4 new line items (first-briefing variant, empty/activating states,
First-run experience, activation telemetry). Buffer reduced 8→6 wk
(some absorbed). Total goes 36 → 41 wk raw audit; 42-43 wk phased
per §10 distribution.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 9: §8.6 — Add new kill criteria

**Files:**
- Modify: `docs/prd.md` — within §8.6 Kill criteria, append three new bullets

**Insertion content (append to the existing bullet list):**

```markdown
- **Activation completion rate < 60% by week 36** (mid-Phase 4) →
  drop fully-self-serve aspiration; fallback to founder-led + minimal
  first-run safety (sensible empty states only); replan Phase 4 around
  manual onboarding workflows. Saves ~3 wk on Phase 4.
- **Activation median time > 60 min active attention by week 38** →
  either the journey is wrong (tighten copy/steps) or the bar is
  unrealistic; explicit replan decision with operator.
- **Discovery survey reveals function mismatch by 3rd beta org**
  (briefing-pain < 30% of answers across first 3 orgs) → trigger
  early wedge memo (§9.6 falsification criterion #3 confirmed early);
  pause recruiting until wedge decision is published; consider pivot
  before completing the cohort.
```

**Self-review checklist:**
- [ ] Three new bullets appended to existing kill criteria list
- [ ] Each names a measurable trigger and a specific replan action
- [ ] References to weeks (36, 38) align with Phase 4 timeline updated in Task 13

**Commit:**

```bash
git add docs/prd.md
git commit -m "docs(prd): §8.6 add activation-related kill criteria

Three new triggers: completion rate <60% by wk 36, median activation
time >60 min by wk 38, function mismatch detected by 3rd beta org via
discovery survey. Each names specific replan action.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 10: §8.7 + §9.7 — Add new Open Questions

**Files:**
- Modify: `docs/prd.md` — within §8.7 Open Questions and §9.7 Open Questions

**Per §8.7 Open Questions, append:**

```markdown
- **OQ-023** What's the right time-to-first-useful-briefing target —
  1 day, 3 days, 7 days? Currently set to < 7 days (§9.5) but could be
  tightened to < 3 days if cold-start agent quality permits.
- **OQ-025** If activation completion lags (50–80% of cohort), is that
  a leading indicator that triggers schedule extension, or a fixed
  gate? Decision rule needs to be set before Phase 4 begins.
```

**Per §9.7 Open Questions, append:**

```markdown
- **OQ-026** What do we do about operators who activate but don't
  return for their scheduled second briefing? Retention work post-MVP,
  or accept as week-1-only signal?
```

**Note on OQ-024**: lives in §5.8 or §7.4 per the DESIGN-DOC. Decision: place it in §5.8 because the Workflows library is most directly a Module-5 (Modules) concept. Append to §5.8 Open Questions:

```markdown
- **OQ-024** When does the Workflows library become more than length-1?
  Threshold: feature-completeness of either Architecture Review (§7.2.2)
  or Portfolio Dependency Intelligence (§7.2.3) — both currently
  post-beta.
```

**Self-review checklist:**
- [ ] OQ-023, OQ-025 appended to §8.7
- [ ] OQ-024 appended to §5.8
- [ ] OQ-026 appended to §9.7
- [ ] Numbering continues from 022 (last OQ in current PRD); index integrity verified in Task 14

**Commit:**

```bash
git add docs/prd.md
git commit -m "docs(prd): §5.8/§8.7/§9.7 add OQ-023 through OQ-026

OQ-023: time-to-first-useful-briefing target. §8.7
OQ-024: Workflows library length-1 threshold. §5.8
OQ-025: activation completion as leading indicator vs gate. §8.7
OQ-026: retention for second-briefing no-show. §9.7

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 11: §9.5 — Add Activation metrics block

**Files:**
- Modify: `docs/prd.md` — within §9.5 Dogfood success metrics, insert as a new block after the Experience metrics block

**Insertion content:**

```markdown
**Activation metrics** — measured against beta orgs during Phase 4 and
against the Platform Operator's dogfood re-onboarding calibration.
Visible to Platform Operator only.

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
| Time from activation to 2nd-week briefing | scheduled 7 days; measure attended/edited rate at arrival |
| Operator's first briefing accept-as-is rate | ≥ 30% (lower than ongoing ≥ 40%; cold-start is real) |
```

**Self-review checklist:**
- [ ] Block placed after Experience metrics block
- [ ] Visibility note ("Platform Operator only") explicit
- [ ] Table format matches Operational / Intelligence / Experience blocks
- [ ] Cold-start ≥ 30% rate aligns with §7.2.1 first-run variant added in Task 4

**Commit:**

```bash
git add docs/prd.md
git commit -m "docs(prd): §9.5 add Activation metrics block

Eleven metrics tracking the activation journey from sign-up to first
briefing approval. Visible to Platform Operator only. Aligns with
§7.2.1 first-run variant and §8.3.9 First-run experience eval criteria.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 12: §9.6 — Update falsification criterion #3

**Files:**
- Modify: `docs/prd.md` — within §9.6 Commercial hypothesis falsification criteria

**Locate the existing criterion #3 and modify it:**

Existing text (criterion 3):
> 3. **Function mismatch** — Orgs engage but the most-used surfaces are
>    non-engineering (e.g., they ask for sales-pipeline or marketing-
>    operations views, not architecture reviews). (The function is
>    wrong, even if the company size is right.)

Replace with:
```markdown
3. **Function mismatch** — Two signals, either of which fires the
   criterion:
   (a) **Week-1 signal** (new, via §8.3.9 discovery survey): across
   the first 3 beta orgs, < 30% name briefings as their top pain.
   Pause recruiting; trigger early wedge memo.
   (b) **End-of-beta signal** (original): orgs engage but the
   most-used surfaces are non-engineering (e.g., sales-pipeline or
   marketing-operations views, not architecture reviews). The function
   is wrong, even if company size is right.
```

**Self-review checklist:**
- [ ] Existing criterion #3 text replaced (not appended), with both signals captured
- [ ] References §8.3.9 (added in Task 6) and aligns with §8.6 kill criterion added in Task 9
- [ ] Criteria #1, #2, and #4 in the surrounding list left untouched

**Commit:**

```bash
git add docs/prd.md
git commit -m "docs(prd): §9.6 promote criterion #3 to week-1 measurable

Function-mismatch falsification gains a week-1 signal via the discovery
survey added in §8.3.9: if <30% of first 3 orgs name briefings as top
pain, criterion fires. Original end-of-beta signal preserved.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 13: §10 — Update Phase 2, 3, 4 scope and exit criteria

**Files:**
- Modify: `docs/prd.md` — within §10 Phased Build Plan, three phase blocks

**Phase 2 changes:**
- Update header from `(weeks 10–18, ~25%)` to `(weeks 10–19, ~24%)` (now 10 wk, total 42-43)
- Append to Scope: `- First-run variant of Executive Briefing (per §7.2.1); partial-data recovery paths in briefing generation`
- Append to Exit criteria: `- First-run briefing variant produces output meeting §7.2.1 cold-start eval bar (≥30% accept-as-is on representative low-signal test inputs)`

**Phase 3 changes:**
- Update header from `(weeks 19–28, ~28%)` to `(weeks 20–31, ~29%)`
- Append to Scope: `- Empty / activating state design across Galaxy, Topology, Decision Graph (per §8.3.10); placeholder-grey design system tokens; state transition motion language`
- Append to Exit criteria: `- All three views ship with empty + activating + activated state specs passing visual regression and copy review (per §8.3.10 evaluation)`

**Phase 4 changes:**
- Update header from `(weeks 29–36, ~22%)` to `(weeks 32–43, ~27%)`
- Replace the single line `- Onboarding flow (org setup, integration connect, first briefing)` with:

```markdown
- Onboarding flow (per §8.3.9 First-run experience):
  - Sign-up frame copy (before/after transformation thesis)
  - Discovery survey (one question, five options, feeds §9.6)
  - Integration-connect wizard (3 OAuth cards, scope selection)
  - Initial-ingest progress UX (leave-and-return supported)
  - First-briefing scheduler (end-of-day-1, first-run variant)
  - Activation moment detection + telemetry (`activation_event` trace)
  - Mismatch handling for non-briefing-pain operators
  - Recovery paths for OAuth/ingest/briefing failures
- Activation telemetry plumbing (per §9.5 metrics block;
  Platform-Operator-only visibility surface)
- Admin module: aggregated discovery-survey table, activation funnel
  cohort view (Platform-Operator-only)
```

- Append to Exit criteria:
```markdown
- Dogfood-operator re-onboarding calibration completed; metrics
  captured per §9.5 activation block; results documented
- First beta org activates end-to-end without contacting support
- §8.6 activation kill criteria all stay un-fired through Phase 4
```

**Update §10 phase totals header** (if there's a summary line at the top of §10) to reflect new total: 42-43 wk.

**Self-review checklist:**
- [ ] All three phase week-range headers updated consistently
- [ ] Sum check: 9 + 10 + 12 + 12 = 43 wk (matches phased total)
- [ ] Phase 4 onboarding flow now references §8.3.9, §9.5, §9.6 — all real targets
- [ ] No content removed from existing scope or exit criteria

**Commit:**

```bash
git add docs/prd.md
git commit -m "docs(prd): §10 update Phase 2/3/4 for new-user amendment

Phase 2 +1 wk (first-run variant, partial-data recovery)
Phase 3 +2 wk (empty/activating states, placeholder-grey tokens)
Phase 4 +3-4 wk (Workflow-First Activation, telemetry, admin)
Total 36 → 42-43 wk. Phase 4 onboarding bullet expanded into specified
sub-scope tree.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 14: §13 — Add new OQs to index

**Files:**
- Modify: `docs/prd.md` — within §13 Open Questions Index table

**Insertion content (in numeric order, preserving alphabetic/numeric sort):**

```markdown
| OQ-023 | What's the right time-to-first-useful-briefing target — 1 day, 3 days, 7 days? | §8.7 | Open |
| OQ-024 | When does the Workflows library become more than length-1? Threshold: feature-completeness of Architecture Review or Portfolio Dependency Intelligence | §5.8 | Open |
| OQ-025 | If activation completion lags 50–80% of cohort, is it a leading indicator triggering schedule extension, or a fixed gate? | §8.7 | Open |
| OQ-026 | What do we do about operators who activate but don't return for scheduled second briefing? Retention work or accept as week-1 signal? | §9.7 | Open |
```

**Self-review checklist:**
- [ ] Four new rows added to the §13 table in numeric order
- [ ] Each row points to its source section (§5.8, §8.7, §9.7)
- [ ] All entries have Status: Open
- [ ] Two-way consistency: every OQ in source section appears in index, every OQ in index appears in source

```bash
# Verify two-way consistency
grep -nE "OQ-0(2[3-6])" /Users/nick/Code/context-os/docs/prd.md
# Expected: each OQ appears at least twice — once in source section,
# once in §13 index
```

**Commit:**

```bash
git add docs/prd.md
git commit -m "docs(prd): §13 add OQ-023 through OQ-026 to index

Four new Open Questions from the new-user amendment indexed in numeric
order. Two-way consistency with source sections (§5.8, §8.7, §9.7)
verified.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 15: Cross-cutting consistency pass

**Files:**
- Modify: `docs/prd.md` — header `Last updated` date + final structural validation

**Step 1: Bump `Last updated`**

Locate the PRD header. Change `**Last updated:** 2026-05-17` to the actual execution date (if different from 2026-05-17, otherwise leave unchanged).

**Step 2: Structural integrity verifications**

```bash
# All section anchors still resolve
grep -nE "^## [0-9]+\." /Users/nick/Code/context-os/docs/prd.md
# Expected: 13 sections, §1 through §13

# All subsection anchors
grep -nE "^### [0-9]+\.[0-9]+" /Users/nick/Code/context-os/docs/prd.md
# Expected: §4.1-4.4, §5.1-5.8, §6.1-6.7, §7.1-7.4, §8.1-8.7, §9.1-9.7, §10 phase blocks

# All MVP feature subsections
grep -nE "^#### 8\.3\.[0-9]+" /Users/nick/Code/context-os/docs/prd.md
# Expected: §8.3.1 through §8.3.10 (was 1-8, added .9 and .10)

# OQ count
grep -cE "^\| OQ-[0-9]+" /Users/nick/Code/context-os/docs/prd.md
# Expected: 26 entries in §13 index (was 22, added 4)

# Every OQ in index has a source mention
for n in 023 024 025 026; do
  echo "OQ-$n appears $(grep -c "OQ-$n" /Users/nick/Code/context-os/docs/prd.md) times"
done
# Each expected: ≥ 2 (once in source, once in index)

# Cross-references resolve
grep -nE "§8\.3\.9|§8\.3\.10" /Users/nick/Code/context-os/docs/prd.md
# Expected: references in §4.1 (Task 1), §5.7 (Task 2), §6.3 (Task 3),
# §10 Phase 4 (Task 13), and the subsections themselves (Tasks 6, 7)

# Phase week math
grep -E "weeks [0-9]+–[0-9]+" /Users/nick/Code/context-os/docs/prd.md
# Expected: 1-9, 10-19, 20-31, 32-43 (totals 43 wk)

# Word count sanity
wc -w /Users/nick/Code/context-os/docs/prd.md
# Expected: 14000-16000 words (was ~12250 + ~2000-3000 new)
```

**Step 3: Fix anything broken; commit**

If any check fails, edit and re-verify before commit.

**Self-review checklist:**
- [ ] All structural checks pass
- [ ] No phantom cross-references
- [ ] Header date current
- [ ] PRD reads end-to-end without contradictions introduced by the amendment

**Commit:**

```bash
git add docs/prd.md
git commit -m "docs(prd): consistency pass for new-user amendment

Header date bumped. Structural integrity verified:
- 26 OQs in §13 index, all with two-way consistency
- All §X.Y and §X.Y.Z cross-refs resolve
- Phase totals 9+10+12+12 = 43 wk (matches §8.5 phased)
- §8.3.1-10 all present in MVP feature list

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 16: Push and create PR

**Files:** none.

**Step 1: Push branch**

```bash
git -C /Users/nick/Code/context-os push -u origin feature/prd-new-user-amendment-design
```

Expected: pushed successfully, new remote branch created.

**Step 2: Create PR**

```bash
gh -R morgan8889/context-os pr create \
  --title "docs(prd): amend for new-user activation as workflow transformation" \
  --body "$(cat <<'EOF'
## Summary

Amends Context-OS PRD v1.0 to specify the new-user activation experience as a workflow-transformation problem, not a configuration problem.

The reframe (surfaced during brainstorming): operators are not "setting up software"; they are being introduced to a different way of working. Onboarding must teach the new workflow, not just expose the tool.

## What changed

- New §4.1 "Week 1 (activation)" sub-treatment of Strategic Operator persona
- New §8.3.9 First-run experience (Workflow-First Activation) — 7-step journey, activation moment = first briefing approval
- New §8.3.10 Empty / activating view states (cross-cutting feature)
- §8.3.4-6 view specs gained empty + activating state ACs
- §6.3 design system grew view-state and copy commitments
- §7.2.1 Executive Briefing gained a first-run variant (modified eval bar, cold-start labeling)
- §9.5 new Activation metrics block (Platform-Operator-only)
- §9.6 falsification criterion #3 promoted to week-1 measurable
- §8.5 audit grew by +5–7 wk; §10 phases redistributed (9+10+12+12 = 43 wk)
- §8.6 three new kill criteria for activation underperformance
- §13 OQ index gained OQ-023, 024, 025, 026

## Design source

`docs/plans/2026-05-17-prd-new-user-amendment-design.md` (committed b2a96ed) — output of \`superpowers:brainstorming\`.

## Test plan
- [x] Structural integrity (\`§X.Y\` cross-refs, OQ two-way consistency, phase math) verified in Task 15
- [x] Each amendment section committed separately for clean diff readability
- [ ] Author end-to-end re-read after merge
- [ ] OQs entered into resolution tracking (post-merge)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

Expected: PR created on `morgan8889/context-os`; returns a URL.

**Step 3: Self-merge (squash or rebase per ruleset)**

```bash
gh -R morgan8889/context-os pr merge --squash --delete-branch
```

Expected: PR merged via squash; remote branch deleted; local branch can be deleted next.

**Step 4: Local cleanup**

```bash
git -C /Users/nick/Code/context-os checkout main
git -C /Users/nick/Code/context-os pull
git -C /Users/nick/Code/context-os branch -d feature/prd-new-user-amendment-design
```

Expected: on main with merge applied; local feature branch removed.

**Step 5: Verify ruleset behavior worked**

```bash
git -C /Users/nick/Code/context-os log --oneline main -3
```

Expected: a squash commit at the top with the PR title, followed by the prior main HEAD (`5fd5b1a`).

---

## Skills referenced

- `superpowers:executing-plans` — runs this plan task-by-task
- `superpowers:subagent-driven-development` — alternative execution mode (one subagent per task in this session)
- `superpowers:verification-before-completion` — applies before claiming each task's commit is correct

## Estimated total effort

| Task group | Effort |
|---|---|
| Task 0 orientation | 10 min |
| Tasks 1–14 section edits | 4–6 hr (avg 20–30 min each, Tasks 6/13 longer) |
| Task 15 consistency pass | 30 min |
| Task 16 push + PR + merge | 15 min |
| **Total** | **~5–7 hours of focused work** |

Realistic in one focused session; can be split if author wants per-task review checkpoints.

---

## Plan complete

Saved to `docs/plans/2026-05-17-prd-new-user-amendment-plan.md`. Two execution options:

**1. Subagent-Driven (this session)** — I dispatch a fresh subagent per Task 1–15, review between tasks, commit per task. Author stays in the loop at Task 15 (consistency) and Task 16 (PR).

**2. Parallel Session (separate)** — Open a new session in this repo, invoke `superpowers:executing-plans`, batch execution with checkpoints.

**Which approach?**
