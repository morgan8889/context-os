# Context-OS — Project Instructions

This repo is the home of **Context-OS**, an AI-native operational intelligence
platform: cognitive OS + workflow orchestration + organizational memory graph +
AI-human coordination surface.

## Authoritative sources

- **Constitution**: `.specify/memory/constitution.md` — supersedes all other
  guidance in this repo. In any conflict between this file and the
  constitution, the constitution wins.
- **PRD**: `docs/prd.md` — canonical product spec.
- **Plans**: `docs/plans/` — design and enrichment plans (dated).

## Non-negotiable principles (from constitution)

Before any change that touches the core ontology, agents, autonomy controls,
governance, or telemetry — re-read the relevant principle:

- **II. Persistent Semantic Memory** — every decision/artifact/edge captured
  in the memory graph; no transient state is authoritative.
- **III. Human Governance, AI Execution** — every AI action declares an
  explicit autonomy level (0–5); ≤3 must be reversible/auditable/gated; 4–5
  must publish escalation criteria and remain interruptible at any time.
- **V. Evaluation-First** — agents and workflows ship with eval suites before
  any non-dev deployment.
- **VI. Observable Autonomy** — every action emits OTEL-compatible traces
  with agent identity, autonomy level, inputs, outputs, rationale, latency,
  cost, and governance markers.

## Workflow

- **Spec-first**: non-trivial work goes through `/speckit.specify` →
  `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`. Specs live under
  `specs/[###-feature-name]/spec.md`. No implementation without a committed
  spec for anything touching the core ontology, agents, autonomy, or
  governance.
- **Constitution Check gate**: every plan runs it before Phase 0 and again
  after Phase 1.
- **Feature branches only**, never main/master. Incremental, reviewable
  commits. Verify with `git diff` before staging.
- **Evidence over assertion**: claims about performance, accuracy, or
  quality cite traces, eval results, or benchmarks.

## Architectural constraints (binding)

- Persistence: logically polyglot is required; physical single-store
  (Postgres + pgvector + Apache AGE) is the sanctioned MVP option until
  sunset triggers fire (see constitution).
- Workflow orchestration must be durable (Temporal / LangGraph), not
  in-memory beyond prototype.
- Telemetry: OpenTelemetry-compatible. Langfuse permitted in addition, not
  instead.
- Integration ingestion must normalize to core ontology at ingest time; raw
  vendor schemas must not leak into core graph queries.
