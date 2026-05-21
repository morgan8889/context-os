# Spec Compliance Review: 0c2f33f03edc (Phase 3 Cognition Surface Specification)
**Verdict**: PASS WITH NOTES
**Reviewer**: code-reviewer agent
**Date**: 2026-05-19

---

## Scope

This is a spec-only commit. It adds the full specification bundle for Phase 3:
`specs/003-cognition-surface/spec.md`, `checklists/requirements.md`, `research.md`,
`data-model.md`, `contracts/api.yaml`, and `quickstart.md`. No implementation code is present.

The review checks whether the spec covers the feature described in the commit message —
"Phase 3 Cognition Surface: Initiative Galaxy, Workflow Topology, Decision Graph, shared
design system, motion language" — with reference to PRD §8.3.4, §8.3.5, §8.3.6, §8.3.10,
and §10 Phase 3 scope.

---

## User Story Coverage

All five user stories named in the commit message are present.

| # | User Story | Priority | PRD Source | Present | Scenarios |
|---|-----------|----------|------------|---------|-----------|
| US1 | Initiative Galaxy | P1 | §8.3.4 | YES | 10 |
| US2 | Workflow Topology | P2 | §8.3.5 | YES | 6 |
| US3 | Decision Graph | P3 | §8.3.6 | YES | 6 |
| US4 | Shared Design System and Motion Language | P1 (prereq) | §10, §6.3 | YES | 5 |
| US5 | Empty and Activating States (cross-cutting) | P2 | §8.3.10 | YES | 5 |

Total: 32 acceptance scenarios across 5 user stories.

The approval/inbox surface (§8.3.8) is treated as a Phase 2 carry-forward in Assumptions and
the API contract; it correctly has no user story of its own. The source header lists §8.3.7
(Executive Briefing E2E), but that feature belongs to Phase 2. §8.3.7 appears in the header
because the Out of Scope section references its scheduling UI as explicitly cut. This is a
minor traceability ambiguity in the header, not a coverage gap.

---

## Functional Requirements Coverage

All 33 functional requirements FR-001 through FR-033 are present.

| Group | FRs | Count |
|-------|-----|-------|
| Initiative Galaxy | FR-001 to FR-010 | 10 |
| Workflow Topology | FR-011 to FR-017 | 7 |
| Decision Graph | FR-018 to FR-024 | 7 |
| Shared Design System | FR-025 to FR-029 | 5 |
| Empty / Activating States | FR-030 to FR-033 | 4 |
| **Total** | | **33** |

---

## Success Criteria Coverage

All 10 success criteria SC-001 through SC-010 are present.

| SC | Criterion | Measurable | Confirmation Method |
|----|-----------|------------|-------------------|
| SC-001 | Galaxy ≥30fps at 10k/30k | YES | CI benchmark suite |
| SC-002 | Galaxy layout converges in 5s | YES | CI benchmark suite |
| SC-003 | Three design reviews, world-class bar | YES (w/ caveat) | Documented review notes |
| SC-004 | 60s zero-narration demo | YES (w/ caveat) | Recorded session |
| SC-005 | Topology 500 nodes sub-second | YES | Automated perf measurements |
| SC-006 | Decision search < 2s | YES | Automated timing test |
| SC-007 | 27 visual regression fixtures in CI | PARTIAL (see SP-002) | CI visual regression |
| SC-008 | Design reviews vs reference sets | YES (w/ caveat) | Design review notes |
| SC-009 | Cross-surface coherence confirmed | YES (w/ caveat) | Cross-surface design review |
| SC-010 | Empty states rated vs Linear/Notion | YES (w/ caveat) | Internal review notes |

"YES (w/ caveat)" indicates the criterion depends on human reviewer judgment; all such
cases have a documented confirmation method, which is appropriate for the qualitative tier
of this product.

---

## PRD Fidelity Check

| PRD Requirement | Spec Coverage | Gap |
|----------------|---------------|-----|
| §8.3.4: ≥30fps at 10k/30k | FR-001, SC-001 | None |
| §8.3.4: Force layout ≤5s | FR-002, SC-002 | None |
| §8.3.4: Lasso (touch, mouse, keyboard) | FR-003 | None |
| §8.3.4: Time-travel scrub < 500ms | FR-004 | None |
| §8.3.4: Overlays compose without re-layout | FR-005 | None |
| §8.3.4: Empty state with "Adjust source scope" CTA | FR-007 | None |
| §8.3.4: Activating state with "Notify me when done" CTA | FR-008 | None |
| §8.3.4: Performance benchmark suite in CI | FR-009 | None |
| §8.3.4: Three design reviews before closed beta | FR-010 | None |
| §8.3.5: 500 nodes sub-second interaction | FR-011 | None |
| §8.3.5: Bottleneck and latency overlays | FR-012 | None |
| §8.3.5: Filter by team, initiative, status | FR-013 | None |
| §8.3.5: Status, ownership, autonomy markers per node | FR-014 | None |
| §8.3.5: Empty state — "View Executive Briefing" CTA | FR-015 | None |
| §8.3.5: Activating state — "See what's been discovered" CTA | FR-016, US2 S5 | **GAP — see SP-001** |
| §8.3.5: Visual regression at three viewports | FR-017 | None |
| §8.3.6: 1000 decisions, cluster collapse/expand | FR-018 | None |
| §8.3.6: Search < 2s | FR-019, SC-006 | None |
| §8.3.6: Rationale/alternatives on hover or pane | FR-020 | None |
| §8.3.6: Typed edges rendered and distinguishable | FR-021 | None |
| §8.3.6: Empty state — "Capture a decision manually" CTA | FR-022 | None |
| §8.3.6: Activating state (1–19 decisions) | FR-023 | None |
| §8.3.10: Exactly one CTA per pre-activated state | FR-030 | Partially undermined by SP-001 |
| §8.3.10: Specific copy | FR-031 | None |
| §8.3.10: Animated transitions | FR-032 | None |
| §8.3.10: Visual regression for pre-activated states | FR-033 | None (see SP-002) |
| §10: Design system (Radix + Tailwind + tokens) | FR-025 to FR-028, US4 | None |
| §10: Motion language (two tiers) | FR-027, US4 S3 | None |
| §10: Design reviews vs named references | FR-010, SC-003, SC-008 | None |

---

## Bundle Completeness

The Phase 1 and Phase 2 spec bundles each include `plan.md` and `tasks.md`. The Phase 3
bundle committed here does not include either. This is expected — the commit is a specification
commit; `plan.md` and `tasks.md` are generated by subsequent `/speckit.plan` and
`/speckit.tasks` steps. The checklist status is marked "Draft", which is consistent.
Noting for traceability only.

---

## Issues Found

### Important

**SP-001** — Topology activating state is missing the named CTA  
File: `specs/003-cognition-surface/spec.md`, US2 scenario 5 and FR-016  
Confidence: 88

PRD §8.3.5 specifies the activating state primary action as "See what's been discovered".
US2 scenario 5 says copy "invites exploration" but names no CTA. FR-016 lists discovery-
progress copy but states no CTA requirement. This creates a gap against FR-030 (exactly one
CTA per pre-activated state) because an implementer reading spec.md alone cannot determine
what CTA to show for the Topology activating state.

Fix: US2 scenario 5 — add "a 'See what's been discovered' primary action is present" to the
Then clause. FR-016 — add "and a 'See what's been discovered' CTA" after "discovery-progress
copy".

### Minor

**SP-002** — FR-033 fixture count (18) is inconsistent with SC-007 (27)  
File: `specs/003-cognition-surface/spec.md`, FR-033 and SC-007  
Confidence: 82

FR-033 specifies "9 test fixtures total for empty states, 9 for activating states" (18 total).
SC-007 requires "27 test fixtures" (3 views × 3 viewports × 3 states, including activated
states). The quickstart fixture matrix confirms 27 are intended. An implementer following
FR-033 would commit 18 fixtures and satisfy the FR gate; 9 activated-state snapshots have no
FR enforcement.

Fix: Extend FR-033 to add: "Regression tests for activated states MUST also be committed for
all three views at all three viewports (9 additional fixtures, 27 total)."

**SP-003** — §8.3.7 listed as source in spec header but not explained in body  
File: `specs/003-cognition-surface/spec.md`, line 6  
Confidence: 80

The Input field includes "§8.3.7" but the spec body does not reference it in requirements.
The Out of Scope section mentions only one element of §8.3.7 (recurring briefing scheduling).
A reader tracing §8.3.7 from the header finds no corresponding spec section or assumption
explaining its disposition.

Fix: Either remove §8.3.7 from the Input field, or add to Assumptions: "The Executive Briefing
workflow (§8.3.7) is implemented end-to-end in Phase 2; Phase 3 adds no new requirements for
the briefing engine — only a UI skin over the approval surface (§8.3.8)."
