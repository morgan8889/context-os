<!--
SYNC IMPACT REPORT
==================
Version change: 1.1.0 → 1.2.0
Rationale: MINOR bump. Adds a new NON-NEGOTIABLE principle VIII
(Test-Driven Development) mandating test-first development for
deterministic application and library code. Scoped to deterministic
code only: probabilistic agent and workflow behavior remains governed
by Principle V (Evaluation-First), with the two declared complementary.
Also adds a corresponding TDD quality gate to the Development Workflow &
Quality Gates section so the principle is enforced at merge time.

Principles (8, +1 new):
  I.    Intent Over Tasks
  II.   Persistent Semantic Memory (NON-NEGOTIABLE)
  III.  Human Governance, AI Execution (NON-NEGOTIABLE)
  IV.   Visualization as Cognition
  V.    Evaluation-First for Agents and Workflows (NON-NEGOTIABLE)
  VI.   Observable Autonomy (NON-NEGOTIABLE)
  VII.  Domain-Adapter Extensibility
  VIII. Test-Driven Development (NON-NEGOTIABLE)  ← NEW

Modified sections:
  - Core Principles — added Principle VIII (Test-Driven Development).
  - Development Workflow & Quality Gates — added a TDD gate bullet
    requiring evidence of test-first discipline before merge.

Unchanged sections:
  - Principles I–VII (verbatim)
  - Architectural Constraints
  - Governance

Templates status:
  ✅ .specify/templates/plan-template.md      — Constitution Check gate
       principle-agnostic; no edits needed.
  ✅ .specify/templates/spec-template.md      — Compatible.
  ✅ .specify/templates/tasks-template.md     — Compatible; "Tests are
       OPTIONAL" guidance now overridden by Principle VIII for
       deterministic code (eval/test tasks no longer optional there).
  ✅ .specify/templates/checklist-template.md — Compatible.
  ⚠ .specify/templates/commands/*.md          — Pending review at next use.
  ⚠ README.md / docs/quickstart.md            — Not yet present in repo.

Prior-version note:
  Initial ratification 2026-05-17 at v1.0.0 (constitution from template).
  v1.1.0 amended 2026-05-17 (single-store persistence relaxation).
  v1.2.0 amended 2026-05-20 (added Test-Driven Development principle);
  no policy in force between versions required a migration plan.

Deferred items:
  - None. RATIFICATION_DATE remains 2026-05-17 (immutable).
-->

# Context-OS Constitution

Context-OS is an AI-native operational intelligence platform: a cognitive
operating system, a workflow orchestration layer, an organizational memory
graph, and an AI-human coordination surface. This constitution defines the
non-negotiable principles and architectural commitments that govern every
feature, workflow, agent, and visualization built on the platform.

## Core Principles

### I. Intent Over Tasks

The system MUST model goals, outcomes, and strategic intent as first-class
primitives. Tasks, tickets, and work items are derived artifacts — they exist
only as projections of intent through workflows. Every feature MUST be
traceable to a Goal or Initiative in the intent graph; orphan tasks are a
modeling defect, not a valid state.

**Rationale**: Traditional tools optimize for tracking units of work; this
platform optimizes for coordinating outcomes. Modeling tasks as primary leads
back to siloed records and manual coordination — the failure mode Context-OS
exists to eliminate.

### II. Persistent Semantic Memory (NON-NEGOTIABLE)

Every decision, artifact, dependency, and relationship MUST be captured as
typed nodes and edges in the organizational memory graph, with rationale and
provenance attached. Workflows MUST NOT lose semantic context across steps,
sessions, or agents. State changes MUST be recorded as facts in the memory
layer before being considered complete; in-memory or transient state is not
authoritative.

**Rationale**: The product thesis is that organizations operate poorly because
context is fragmented across humans, tools, and time. A platform whose own
internal state is ephemeral or unstructured cannot deliver organizational
memory to its users.

### III. Human Governance, AI Execution (NON-NEGOTIABLE)

AI agents MAY orchestrate, execute, synthesize, and recommend. Humans MUST
retain authority over autonomy levels, approvals, escalation policies, trust
boundaries, and strategic priorities. Every AI action MUST declare an explicit
autonomy level (0–5 per the platform model) and MUST be reversible, auditable,
or gated by human approval at levels ≤ 3. Autonomy levels 4 and 5 MUST publish
escalation criteria and remain interruptible at any time.

**Rationale**: AI-native does not mean AI-unsupervised. The platform's
legitimacy with users, operators, and regulators depends on humans being
provably in charge of consequence-bearing decisions.

### IV. Visualization as Cognition

User-facing surfaces MUST be topology-first: graphs, flow maps, scenario
overlays, and living systems views. Static dashboards, CRUD forms, and
spreadsheet-style tables are NOT acceptable as primary interfaces; they MAY
appear only as secondary detail panes invoked from a topology surface.
Visualizations MUST be interactive, navigable, and capable of expressing
multi-dimensional state (load, risk, ownership, time, autonomy).

**Rationale**: The platform's value is operational cognition, not record
display. Reverting to traditional UI paradigms collapses the product into
just another project-management tool and erases its differentiation.

### V. Evaluation-First for Agents and Workflows (NON-NEGOTIABLE)

Every AI agent role and every workflow orchestration MUST have an evaluation
suite committed before it is deployed to any non-development environment. The
suite MUST cover representative inputs, golden outputs, failure modes, and
governance-relevant edge cases (low-confidence outputs, conflicting signals,
escalation triggers). Agents MUST NOT be promoted past development without
their evaluations passing; suites MUST NOT be skipped, weakened, or deleted
to unblock a release.

**Rationale**: Probabilistic systems that act on organizational state require
the same rigor as production code plus behavioral guarantees that code-level
tests alone cannot provide. Without evaluations, autonomy is unsafe at any
level above 1.

### VI. Observable Autonomy (NON-NEGOTIABLE)

Every agent action, prompt, tool invocation, decision, retrieval, and
recommendation MUST emit structured traces conforming to the platform's
telemetry schema. Traces MUST include: agent identity, autonomy level,
inputs, outputs, rationale where applicable, latency, cost, and governance
markers (approvals, escalations, overrides). Operators MUST be able to
reconstruct any AI-driven outcome end-to-end from telemetry alone.

**Rationale**: Trust in autonomous systems is earned through inspectability.
Telemetry is also the substrate for the Cognitive Load Engine, Simulation
Engine, and operational health visualizations — features that fail silently
if observability is treated as optional.

### VII. Domain-Adapter Extensibility

The core ontology (Goal, Initiative, Workflow, Signal, Agent, Artifact,
Decision, Constraint, Dependency, Capability, Risk, Context, Memory, Autonomy,
Simulation) MUST remain domain-agnostic. Domain-specific concepts (e.g.,
Architecture Review, ADR, Portfolio, Capability map) MUST be expressed as
adapters that map onto the core primitives — not as forks, special cases, or
hardcoded fields in the core model. New domains MUST be addable without
schema migrations of the core graph.

**Rationale**: The platform's long-term thesis spans enterprise architecture,
PMO, engineering, consulting, personal productivity, health, and investment
research. Domain coupling in the core would foreclose that future and trap
the system in its seed domain.

### VIII. Test-Driven Development (NON-NEGOTIABLE)

All deterministic application and library code MUST be developed test-first:
a failing test that specifies the desired behavior MUST be written and
observed to fail before the implementation that satisfies it. The
red-green-refactor cycle is mandatory — write a failing test (red), write the
minimum code to pass it (green), then refactor under a green suite. Tests MUST
NOT be backfilled to retroactively rubber-stamp existing code, weakened, or
skipped to unblock a release. Every bug fix MUST begin with a failing
regression test that reproduces the defect before the fix is written.

Probabilistic agent and workflow behavior remains governed by Principle V
(Evaluation-First). TDD and evaluation-first are complementary: TDD guarantees
deterministic correctness at the unit and integration level, while evaluation
suites guarantee behavioral safety that code-level tests cannot provide. The
deterministic scaffolding around an agent (tool wiring, parsers, transforms,
state reducers, API handlers) is subject to this principle; the agent's
probabilistic outputs are subject to Principle V.

**Rationale**: Test-first development keeps deterministic code correct,
designed for testability, and safe to change. Writing the test first forces a
specification of intent before implementation, prevents tests that merely
confirm whatever the code happens to do, and produces a regression net that
makes the continuous, AI-assisted refactoring this platform depends on safe
rather than reckless.

## Architectural Constraints

The following constraints are binding on all implementation work:

- **Logically polyglot persistence is required; physical polyglotism is
  optional below sunset triggers.** The three persistence roles — structured
  operational data, organizational memory graph, and semantic retrieval —
  MUST remain logically distinct (separate schemas, separate query paths,
  separate access modules). They MAY be served by a single physical store
  during MVP if that store provides first-class capability for each role.
  PostgreSQL with `pgvector` (vector role) and Apache AGE (graph role) is
  the sanctioned single-store option. Each role MUST be addressable through
  its own module so that splitting to dedicated stores later is a deployment
  change, not a rewrite. **Sunset triggers** that REQUIRE splitting at least
  one role onto a dedicated store: (a) graph query p95 latency exceeds 500ms
  on representative production workloads despite tuning; (b) vector
  retrieval recall@k falls below 70% on the canonical eval set; (c) the
  organizational memory graph exceeds ~5M nodes or ~25M edges in a single
  tenant; (d) any of pgvector or AGE proves unmaintained or incompatible
  with a required Postgres version upgrade. When a trigger fires, the role
  involved MUST migrate to a dedicated store (Neo4j/TypeDB for graph,
  Qdrant/Weaviate for vector) before the next non-trivial feature ships
  against the affected surface.
- **Workflow orchestration MUST be durable**. Long-running AI and human
  workflows MUST survive process restarts and partial failures via a durable
  orchestrator (e.g., Temporal, LangGraph). Ad-hoc in-memory orchestration
  is not acceptable beyond prototype scope.
- **Autonomy levels 0–5 are the only sanctioned model** for AI authority.
  Features MUST NOT invent parallel autonomy taxonomies; if the 0–5 model is
  insufficient, the constitution MUST be amended before extension.
- **Telemetry stack** MUST be OpenTelemetry-compatible. Agent-specific
  telemetry (e.g., Langfuse) is permitted in addition to, not in place of,
  OTEL traces.
- **Integration ingestion** (Jira, GitHub, Drive, Confluence, Slack, Calendar,
  etc.) MUST normalize external data into the core ontology at ingest time;
  raw vendor schemas MUST NOT leak into core graph queries.

## Development Workflow & Quality Gates

- **Spec-first**: All non-trivial features MUST originate from a spec under
  `specs/[###-feature-name]/spec.md`, produced via the `/speckit.specify`
  workflow. Implementation without a committed spec is prohibited for any
  change touching the core ontology, agent definitions, autonomy controls,
  or governance surfaces.
- **Constitution Check gate**: Every implementation plan MUST run the
  Constitution Check in `plan-template.md` before Phase 0 research and again
  after Phase 1 design. Violations MUST be either resolved or documented in
  the plan's Complexity Tracking table with explicit justification.
- **Agent / workflow promotion gate**: No AI agent role or workflow may be
  enabled in staging or production without (a) a committed evaluation suite
  per Principle V, (b) telemetry conforming to Principle VI, and (c) a
  documented autonomy-level declaration per Principle III.
- **Test-first gate**: Per Principle VIII, deterministic application and
  library code MUST be accompanied by tests written test-first. PRs MUST
  evidence test-first discipline (e.g., a failing test committed before or
  alongside its implementation, or a regression test for a bug fix); code
  merged without test coverage of its deterministic behavior is a violation,
  not a follow-up.
- **Visualization review**: UI work introducing a new primary surface MUST
  pass a topology-first review against Principle IV before merge.
- **Branching & commits**: Feature branches only; never main/master. Commits
  MUST be incremental and reviewable; verify with `git diff` before staging.
- **Evidence over assertion**: Performance, accuracy, and quality claims in
  reviews MUST cite traces, evaluation results, or benchmarks — not author
  assurance.

## Governance

This constitution supersedes ad-hoc practices, individual preferences, and
prior informal conventions within the Context-OS project. In any conflict
between this document and other guidance (READMEs, comments, chat decisions,
agent system prompts), this constitution wins.

**Amendment procedure**:

1. Propose the amendment as a PR modifying `.specify/memory/constitution.md`
   with a Sync Impact Report at the top describing the change.
2. Classify the version bump per semantic versioning:
   - **MAJOR**: Removal or backward-incompatible redefinition of a principle
     or governance rule.
   - **MINOR**: New principle or materially expanded section.
   - **PATCH**: Clarifications, wording, typo fixes, non-semantic refinements.
3. Update all dependent templates and documents flagged in the Sync Impact
   Report; unresolved ⚠ items block merge.
4. On merge, update `LAST_AMENDED_DATE`; `RATIFICATION_DATE` is immutable.

**Compliance review**:

- Every PR description MUST state whether the change touches any principle's
  surface area and, if so, confirm compliance or link to the justified
  exception in the plan's Complexity Tracking.
- Quarterly, maintainers MUST audit a sample of merged features for
  principle adherence and file follow-up issues for drift.
- Runtime agent and workflow behavior MUST be re-evaluated against this
  constitution whenever a NON-NEGOTIABLE principle is amended.

**Version**: 1.2.0 | **Ratified**: 2026-05-17 | **Last Amended**: 2026-05-20
