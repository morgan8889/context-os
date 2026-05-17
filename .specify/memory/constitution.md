<!--
SYNC IMPACT REPORT
==================
Version change: TEMPLATE (uninitialized) → 1.0.0
Rationale: Initial ratification. Establishes the first governed version of
the constitution from the placeholder template.

Principles defined (7):
  I.   Intent Over Tasks
  II.  Persistent Semantic Memory (NON-NEGOTIABLE)
  III. Human Governance, AI Execution (NON-NEGOTIABLE)
  IV.  Visualization as Cognition
  V.   Evaluation-First for Agents and Workflows (NON-NEGOTIABLE)
  VI.  Observable Autonomy (NON-NEGOTIABLE)
  VII. Domain-Adapter Extensibility

Sections defined:
  - Core Principles
  - Architectural Constraints
  - Development Workflow & Quality Gates
  - Governance

Templates status:
  ✅ .specify/templates/plan-template.md      — Constitution Check gate is
       principle-agnostic; pulls from this file at plan-time. No edits needed.
  ✅ .specify/templates/spec-template.md      — No principle-name references;
       compatible as-is.
  ✅ .specify/templates/tasks-template.md     — No principle-name references;
       task categorization remains compatible.
  ✅ .specify/templates/checklist-template.md — Generic; no edits required.
  ⚠ .specify/templates/commands/*.md          — Pending review; verify no
       outdated principle references when commands are next exercised.
  ⚠ README.md / docs/quickstart.md            — Not yet present in repo; will
       be authored against this constitution.

Deferred items:
  - None. RATIFICATION_DATE set to first authoring date.
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

## Architectural Constraints

The following constraints are binding on all implementation work:

- **Polyglot persistence is required**. Structured operational data lives in
  a relational store (PostgreSQL); the organizational memory graph lives in a
  graph store (Neo4j or TypeDB); semantic retrieval lives in a vector store
  (pgvector, Qdrant, or Weaviate). No single store MAY be load-bearing for
  all three roles.
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

**Version**: 1.0.0 | **Ratified**: 2026-05-17 | **Last Amended**: 2026-05-17
