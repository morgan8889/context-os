# Code Quality Review: 0c2f33f03edc (Phase 3 Cognition Surface Specification)
**Verdict**: PASS WITH NOTES
**Reviewer**: code-reviewer agent
**Date**: 2026-05-19

---

## Scope

This review evaluates the quality of the spec artifacts as documents: requirement testability,
ambiguity, implementation detail leakage, and acceptance scenario structure. The primary target
is `specs/003-cognition-surface/spec.md`. Companion documents (`data-model.md`, `research.md`,
`contracts/api.yaml`, `quickstart.md`) are implementation-facing and reviewed for internal
consistency with `spec.md`.

---

## Requirement Testability

29 of 33 FRs are fully automatable. The remaining four require human review gates, all of
which are explicitly identified in Independent Test descriptions and Success Criteria
confirmation methods.

| FR | Testable? | Method |
|----|-----------|--------|
| FR-001 to FR-009 (Galaxy perf + interaction) | YES | CI benchmark + Playwright E2E |
| FR-010 (three design reviews) | Partially | File existence gate only |
| FR-011 to FR-015, FR-017 (Topology) | YES | Playwright + visual regression |
| FR-016 (Topology activating state) | PARTIAL — see QC-001 | CTA name cannot be verified from spec alone |
| FR-018 to FR-024 (Decision Graph) | YES | Playwright E2E + perf test |
| FR-025 (no hardcoded colors) | YES | Static analysis / AST scan |
| FR-026 to FR-028 | YES | Visual regression + snapshot analysis |
| FR-029 (cross-surface coherence) | Partially | Human design review |
| FR-030 to FR-032 | YES | Playwright assertions |
| FR-033 (18 pre-activated state fixtures) | YES | CI snapshot gate |

---

## Requirement Ambiguity

### Clear and Precise
Numeric thresholds are explicit and consistent with the PRD throughout: fps (≥30), seconds
(≤5, <2), milliseconds (<500, <1000), and node/decision count boundaries for state transitions
(0 = empty; 1–9 = Galaxy activating; 1–9 = Topology activating; 1–19 = Decision activating).

### Issues Found

**QC-001** — FR-016 omits the Topology activating CTA; FR-030 untestable for that state  
File: `specs/003-cognition-surface/spec.md`, FR-016  
Confidence: 88

FR-030 requires exactly one CTA per pre-activated state. FR-016 specifies the Topology
activating state but names no CTA, so a Playwright assertion cannot verify the correct CTA
text for this state without consulting the PRD. A test asserting `[data-cta="primary"]`
count = 1 would pass with any button text. (Also reported as SP-001 in spec review.)

**QC-002** — US1 scenarios 7 and 8 have subjective Then clauses with no pass protocol  
File: `specs/003-cognition-surface/spec.md`, US1 scenarios 7 and 8  
Confidence: 83

Scenario 7: "the reviewer can correctly describe what the view shows" — "correctly describe"
is undefined. No checklist of expected descriptions is provided.

Scenario 8: "no reviewer can correctly distinguish them" — requires 100% of reviewers to fail
identification, with no minimum reviewer count stated. A single correct identification with
any non-trivial reviewer group fails this criterion.

Both scenarios directly transcribe the PRD's qualitative bar for Galaxy's world-class tier,
which is intentionally high. The issue is not the ambition but the absence of a pass protocol.

Recommendation: Add a Reviewer Protocol note under US1 specifying: minimum reviewers (e.g.,
3), session format (blind comparison), definition of "correct description" (against a
pre-committed observable features checklist), and tiebreak authority.

**QC-003** — FR-033/US5 scenario 5 fixture count (18) inconsistent with SC-007 (27)  
File: `specs/003-cognition-surface/spec.md`, FR-033 and SC-007  
Confidence: 82

FR-033 and US5 scenario 5 protect 18 fixtures. SC-007 and the quickstart matrix require 27.
An implementer following FR-033 literally would commit 18 fixtures and satisfy the FR gate;
9 activated-state regressions have no FR enforcement. (Also reported as SP-002.)

---

## Implementation Detail Leakage into spec.md

The checklist item "[x] No implementation details" is evaluated against `spec.md` only.

**QC-004** — "GSAP-tier motion specification" in US4 scenario 3 names a specific library  
File: `specs/003-cognition-surface/spec.md`, US4 scenario 3  
Confidence: 80

The Then clause names GSAP, a specific JavaScript animation library. This couples the
acceptance criterion to a named technology. Mitigating factor: PRD §10 Phase 3 scope
explicitly names GSAP ("Motion language (set-piece transitions in GSAP)"), so the leakage
is PRD-inherited, not spec-introduced. FR-027 itself is technology-agnostic. The checklist
"PASS" is defensible given PRD provenance but is an overstatement for spec.md in isolation.

Recommendation: Restate as "it uses the set-piece timing from the shared motion language —
not arbitrary timing values." Preserve the library name in research.md only.

**QC-005** — "dagre layout" in US3 Independent Test and FR-023 names a specific algorithm  
File: `specs/003-cognition-surface/spec.md`, US3 Independent Test and line 196  
Confidence: 80

Same mitigation applies: PRD §8.3.6 uses "dagre layout" in its functional acceptance section.
PRD-inherited leakage. FR-018 and FR-019 are technology-agnostic; only the descriptive text
and one scenario use the term. Low severity.

---

## Acceptance Scenario Coverage Gaps

**QC-006** — Initiative-filter and status-filter paths (FR-013) have no acceptance scenario  
File: `specs/003-cognition-surface/spec.md`, FR-013  
Confidence: 81

US2 covers team filter (scenario 3) but not initiative-filter or status-filter. FR-013 names
all three. An implementer could satisfy all US2 acceptance scenarios while implementing only
team filtering.

Recommendation: Add US2 scenario 3a: "Given multiple workflows with different statuses, When
the operator applies a 'blocked' status filter, Then only blocked workflows are shown within
500ms."

**QC-007** — No acceptance scenario verifies typed edge visual distinctiveness (FR-021)  
File: `specs/003-cognition-surface/spec.md`, FR-021  
Confidence: 80

FR-021 requires predecessor, alternative, and dependent edges to be visually distinguishable.
No US3 scenario tests this. A visual regression snapshot would capture current rendering but
would not fail if all edge types were drawn identically on the first commit.

Recommendation: Add US3 scenario 3a: "Given a decision with predecessor and alternative edges,
When the operator views the Decision Graph, Then predecessor edges and alternative edges are
rendered with distinct visual styles (e.g., different stroke patterns)."

---

## Companion Document Quality

### data-model.md

**QC-008** — `DecisionViewState` is missing the `'activating'` variant  
File: `specs/003-cognition-surface/data-model.md`, DecisionViewState type definition  
Confidence: 90

`type DecisionViewState = 'activated' | 'placeholder'` — no `'activating'` variant.
`NodeViewState` (Galaxy) and `StepViewState` (Topology) both include `'activating'`.
FR-023 and US3 scenario 6 require an activating state for Decision Graph (1–19 decisions).
This missing variant will produce a TypeScript strict-mode type error when implementing
the activating-state rendering path for Decision Graph.

Fix: `type DecisionViewState = 'activated' | 'activating' | 'placeholder'`

### contracts/api.yaml

**QC-009** — `GET /api/v1/graph/snapshots` returns an unbounded array; no pagination defined  
File: `specs/003-cognition-surface/contracts/api.yaml`, snapshot list endpoint  
Confidence: 80

The snapshot list returns `{ timestamps: string[] }` with no limit parameter or pagination
envelope. At MVP scale this is acceptable, but it should be documented as a known limitation
in the endpoint description to prevent future callers from assuming pagination support.

**QC-010** — Inconsistent 401 response referencing: `/api/v1/views/state` is inline, all others use `$ref`  
File: `specs/003-cognition-surface/contracts/api.yaml`  
Confidence: 80

`/api/v1/views/state` defines its 401 response inline rather than using
`$ref: "#/components/responses/Unauthorized"`. All other paths use the `$ref`. A generated
client or mock server may produce different schemas for the 401 response from that endpoint.

Fix: Convert the inline 401 on `/api/v1/views/state` to
`$ref: "#/components/responses/Unauthorized"`.

### research.md

SC-001 claims the CI benchmark suite confirms ≥30fps, but Decision 7 in research.md states
"FPS in headless CI is not reliable for absolute values" and proposes CDP timing traces as a
proxy. The quickstart benchmark section correctly notes "Do not rely on headless CI FPS values
for absolute benchmarks." These statements are in tension with SC-001's wording.

The resolution (dedicated GPU runner for absolute benchmarks, CDP traces for regressions in
standard CI) is correct and documented. SC-001 should clarify that the CI benchmark suite
confirms absence of regression relative to a baseline, not absolute fps. No change required
before implementation; this is a documentation clarity note for the plan.md to address.

### quickstart.md

Seed scripts (`seed-graph.ts`, `seed-workflows.ts`, `seed-decisions.ts`, `seed-snapshots.ts`,
`trigger-ingest-batch.ts`) and the `benchmarks/` output directory are referenced but not yet
committed. This is expected at the spec stage. The plan.md scaffold task list should include
creation of `web/scripts/` and `benchmarks/` as part of the Phase 1 Foundations tasks.

---

## Summary of Issues

| ID | Severity | File | Description |
|----|----------|------|-------------|
| QC-001 | Important | spec.md FR-016 | Topology activating CTA name missing; FR-030 untestable for that state |
| QC-002 | Important | spec.md US1 S7,S8 | No pass protocol for qualitative design review scenarios |
| QC-003 | Important | spec.md FR-033/SC-007 | 18 vs 27 fixture count; activated-state regressions have no FR gate |
| QC-004 | Minor | spec.md US4 S3 | "GSAP-tier" names a library (PRD-inherited; checklist overstatement) |
| QC-005 | Minor | spec.md US3 | "dagre layout" names an algorithm (PRD-inherited; low severity) |
| QC-006 | Minor | spec.md FR-013 | Initiative-filter and status-filter have no acceptance scenario |
| QC-007 | Minor | spec.md FR-021 | Typed edge visual distinctiveness has no acceptance scenario |
| QC-008 | Important | data-model.md | `DecisionViewState` missing `'activating'` — TypeScript compile error |
| QC-009 | Minor | contracts/api.yaml | Snapshot list endpoint unbounded; no pagination noted |
| QC-010 | Minor | contracts/api.yaml | Inconsistent 401 inline vs `$ref` on `/api/v1/views/state` |
