# PRD Enrichment Design — Context-OS

**Date**: 2026-05-17
**Author**: Nick Morgan (with Claude)
**Status**: Approved (this session)
**Source PRD**: `/Users/nick/Vaults/AI Knowledge/AI Knowledge/00-INBOX/context-os.md`
**Target**: enriched PRD replacing the source, build-team-ready

---

## 1. Context

The source PRD is two documents stacked: sections 1–13 describe a generic
AI-native operational intelligence platform, followed by a parallel-numbered
seed-domain document (sections 2–10) about enterprise architecture / PMO.
The document is strong on conceptual model and design principles, weak on
specificity — MVP features lack acceptance criteria, technical architecture
is candidate lists rather than decisions, workflows are sketches, and there
are no personas, no quantified metrics, and no honest sizing.

The enrichment is for a **build team / cofounder** audience and must support
scoping, sequencing, and architectural decisions. Build context is **solo +
advanced LLM coding and design agents**. MVP target is **closed beta with
3–5 organizations**.

## 2. Goals of the enrichment

- Make every architectural decision explicit; eliminate candidate lists.
- Add acceptance criteria, evaluation criteria, and effort estimates to MVP
  features.
- Resolve the duplicate seed-domain structure by reframing it as the
  dogfooding/validation domain — not the commercial wedge.
- Commit to a falsifiable commercial hypothesis with explicit kill criteria.
- Connect every section to the constitution and to every other section so
  the doc reads end-to-end without internal contradictions.
- Surface open questions at section level and aggregate them into a single
  index a build-team reader can scan in one sitting.

## 3. Approach

**Approach A — Layered Platform Doc** (selected over Decision-Driven and
Three-Doc Split). Single coherent document, layered top-down, with each
section ending in a short Open Questions list. Borrows from the
decision-driven approach the discipline of naming what's decided vs deferred.

## 4. Target Table of Contents

```
1.  Executive Summary
2.  Vision & Thesis                                       [deepen]
    2.1 What this replaces
    2.2 Why AI-native, why now
    2.3 What "operational cognition" means concretely
3.  Conceptual Model                                      [reframe]
    3.1 Universal cognitive primitives
    3.2 Design principles
    3.3 Autonomy ladder (0–5)
    3.4 Open Questions
4.  User & Operator Personas                              [new]
    4.1 Strategic Operator
    4.2 Domain Practitioner
    4.3 Platform Operator (dogfooder)
    4.4 Open Questions
5.  Product Modules (7)                                   [deepen]
    Each: purpose, capabilities, owned data, AI/human boundary,
    MVP-vs-future cut
6.  Platform Architecture                                 [decisions]
    6.1 Stack decisions (one pick per role, with rationale)
    6.2 Data layer topology
    6.3 Visualization architecture
    6.4 Agent runtime
    6.5 Workflow orchestration
    6.6 Observability
    6.7 Open Questions
7.  AI-Native Workflow Model                              [reframe]
    7.1 Generic workflow contract
    7.2 Three canonical workflows specified (I/O, eval, failure modes)
    7.3 Agent role definitions with evaluation criteria
    7.4 Open Questions
8.  MVP Definition                                        [new]
    8.1 MVP success bar (closed beta, 3–5 orgs)
    8.2 Build Model (solo + advanced LLMs)
    8.3 In-scope features with acceptance criteria
    8.4 Explicitly out of scope
    8.5 Solo-build feasibility audit
    8.6 Kill criteria
    8.7 Open Questions
9.  Dogfooding Domain: Enterprise Architecture / PMO      [reframe]
    9.1 Why this is the validation domain
    9.2 Domain ontology mapped to core primitives
    9.3 Validation workflows
    9.4 Data sources
    9.5 Dogfood success metrics
    9.6 Commercial hypothesis (to falsify in closed beta)
    9.7 Open Questions
10. Phased Build Plan                                     [new]
    Phase 1–4: goal, scope, exit criteria, risks, kill criteria
11. Future Vision                                         [reframe]
12. Glossary                                              [new]
13. Open Questions Index                                  [new]
```

## 5. Key design decisions captured in the enriched PRD

### 5.1 Architectural decisions (replaces current §10 candidate lists)

| Layer | Decision |
|---|---|
| Frontend framework | Next.js (App Router) + Zustand |
| Topology viz (large-scale) | **Sigma + Graphology + forceatlas2-worker**; **dagre** for hierarchical |
| Topology viz (structured) | **React Flow** with custom node/edge components |
| Charts / overlays | **Apache ECharts** primary, **Visx** for bespoke |
| Canvas (deferred) | TLDraw, only if a workflow demands it |
| 3D (deferred) | react-three-fiber, post-MVP |
| Motion | **Framer Motion** for everyday; **GSAP** for set-piece moments |
| Design system | Radix UI + Tailwind + custom motion/color tokens |
| Backend | Python + FastAPI |
| Data layer | **PostgreSQL + pgvector + Apache AGE** (single physical store, logically polyglot — requires constitution amendment) |
| Workflow orchestration | **LangGraph** (agents) + Postgres-backed queue |
| Agent runtime | Claude API primary, OpenAI fallback |
| Observability | Langfuse (LLM traces) + OpenTelemetry (app traces) + Postgres logs |
| Auth | Clerk |
| Deploy | Fly.io / Railway for backend, Vercel for frontend |

**Visualization deep-dive included in the PRD**: Sigma vs Cosmograph
trade-offs are documented (layout polymorphism, license, customization
ceiling, AI-agent ergonomics). G6 (AntV) noted as a half-day prototype
spike before committing. Cosmograph kept on the table as a deferred upgrade
for the Initiative Galaxy view if Sigma's force layout doesn't sing at
target scale.

**Substrate model**: M1 — one library per view type, unified by a shared
design system. M2 (unified WebGL substrate) deferred as solo-fatal for
MVP. M3 (canvas-first) rejected as wrong fit for ops cognition.

### 5.2 Visualization tiering rule

> MVP ships **one world-class surface** (Initiative Galaxy) plus
> **two "very good" surfaces** (Workflow Topology, Decision Graph).
> "Very good" means feature-complete, defensible against Linear/Notion,
> no compromises on data fidelity — but not the demo-moment surface
> that carries the product story.

This is the sequencing principle the PRD commits to. The world-class bar
is checkable (side-by-side reference comparison, demo-able in 60 seconds
with no narration).

### 5.3 Design references the PRD names

To prevent drift toward generic LLM-design aesthetics:

- **Motion / restraint / density**: Linear
- **Typography / dark-first**: Vercel, Arc
- **Large-graph rendering aesthetic**: Cosmograph demos, Kumu, GitHub Next
- **Canvas interaction**: Figma, TLDraw
- **Analytical overlays**: Observable, nivo

### 5.4 MVP feature surface

| Feature | Status | Tier |
|---|---|---|
| Organizational memory graph | MVP | Substrate |
| Ingestion: Jira + GitHub + Slack | MVP | — |
| 2 agents: Operational Synthesizer + Dependency Mapper | MVP | — |
| Initiative Galaxy (Sigma) | MVP | **World-class** |
| Workflow Topology view (React Flow) | MVP | Very good |
| Decision Graph view (dagre + Sigma or RF) | MVP | Very good |
| Executive Briefing workflow E2E | MVP | — |
| Human approval surface | MVP | — |
| Basic simulation engine | Post-beta | — |
| Agent Orchestration UI | Post-beta | — |
| Architecture Review workflow | Post-beta | — |

### 5.5 Acceptance criteria format

Every MVP feature gets four blocks: **Functional acceptance**, **Qualitative
bar**, **Evaluation**, **Out of scope for MVP**. Example for Initiative
Galaxy: ≥10k nodes / ≥30k edges at ≥30fps; force convergence ≤5s; lasso
on touch/mouse/keyboard; time-travel <500ms; overlays compose without
re-layout. Qualitative bar: side-by-side with Linear's graph view, no one
can tell which is production; demo-able for 60 seconds with zero
explanation.

### 5.6 Solo-build feasibility audit (with AI-assisted coding + design)

| Feature | Estimate | Load-bearing risk |
|---|---|---|
| Memory graph (Postgres + AGE) | 3 wk | AGE maturity |
| Ingestion (3 sources) | 3 wk | OAuth per vendor |
| 2 agents + evals | 5 wk | Eval-data acquisition |
| Initiative Galaxy (world-class) | 5 wk | World-class bar |
| Workflow Topology view | 3 wk | Custom node design |
| Decision Graph view | 2 wk | Layout legibility |
| Briefing workflow E2E | 3 wk | Output quality variance |
| Approval surface | 1 wk | None significant |
| Auth + multi-tenant (Clerk) | 2 wk | None significant |
| Deploy / observability | 1 wk | None significant |
| Buffer (30%) | 8 wk | Unknown unknowns |
| **Total** | **36 weeks (~8.3 months)** | |

### 5.7 Kill criteria

- AGE proves immature on real query patterns → drop AGE, use plain Postgres
  + adjacency tables; +2 wk.
- Sigma can't hit world-class on Galaxy within 6 wk → prototype Cosmograph
  for Galaxy specifically; +2 wk plus license cost.
- LLM design output isn't at world-class bar on Galaxy by week 14 → hire
  contract designer for 4 wk on Galaxy direction-setting, OR demote Galaxy
  to "very good," replan demo around Workflow Topology + Briefing.
- Solo velocity below estimate by week 8 → cut to one ingestion source and
  one agent.
- If Workflow Topology consumes >5 wk despite "very good" tier → cut
  Decision Graph view from MVP.
- If both new structured views together push past 8 wk combined → revisit
  at week 12 with hard cut-or-keep decision.
- Closed-beta recruitment stalls → narrow to 1–2 orgs (limited beta);
  preserve as wedge-hypothesis test with smaller sample.

### 5.8 Build Model

> The MVP is built by one human leveraging advanced LLM coding agents
> and AI design tools across the stack. The human's load-bearing
> contributions are **direction-setting, taste, eval design, and
> integration coherence**. Everything else is LLM leverage. Architectural
> choices reflect this — libraries with strong AI training corpora are
> preferred (Sigma over Cosmograph partly for this reason); design tokens
> are iterated with AI assistance; component implementations are
> LLM-generated and human-reviewed.

### 5.9 Dogfooding domain reframing

The seed-domain content is reframed in §9 as the validation domain, not
the commercial wedge. Domain entities map 1:1 (or as adapters) onto core
primitives per Constitution Principle VII. Two validation workflows are
specified with I/O contracts and eval criteria: Executive Briefing (MVP)
and Architecture Review (post-MVP). Data sources cut to 3 for MVP
(Jira + GitHub + Slack), with five more deferred.

### 5.10 Commercial hypothesis (falsifiable)

> **Hypothesis**: The commercial wedge is engineering leadership at Series
> B–D companies (50–500 engineers) running architecture and PMO functions.

**ICP indicators**: 50–500 engineers across ≥3 teams; has EA function or
architecture-review ritual; uses Jira/Linear + GitHub + Slack; leadership
spends >2 hrs/week on operational synthesis.

**Falsification criteria**:
1. ICP fit fails — <2 of 5 beta orgs match ICP despite recruiting effort.
2. Value rejection — orgs love product, willingness-to-pay <$X/seat/month.
3. Function mismatch — most-used surfaces are non-engineering.
4. Buyer mismatch — buying authority sits outside engineering leadership.

**Plan-B candidates** (pre-named, not pre-ranked): consulting firms;
internal EA teams at large enterprises; engineering ops / DevEx at
adjacent sizing; cross-functional ops at PE-backed rollups.

**Decision artifact**: PRD commits to publishing a wedge decision memo at
end of closed beta referencing falsification evidence.

### 5.11 Phased Build Plan

Four phases sized in weeks against the 36-week total:

- **Phase 1 — Foundation** (wk 1–9): substrate, ingestion, auth, deploy
- **Phase 2 — Intelligence** (wk 10–18): agents, briefing E2E, approval
- **Phase 3 — Cognition Surface** (wk 19–28): Galaxy + Topology + Decision
- **Phase 4 — Closed Beta Readiness** (wk 29–36): multi-tenant hardening,
  onboarding, support, telemetry

Each phase has explicit exit criteria, risks, and kill triggers.

### 5.12 Open Questions Index (§13)

Aggregates section-level Open Questions into a single page:

- **OQ-001** Does Postgres+AGE handle our graph query patterns at scale, or migrate to Neo4j post-beta? *(§6)*
- **OQ-002** Sigma sufficient at >50k nodes, or license Cosmograph for Galaxy? *(§6)*
- **OQ-003** Does the commercial-wedge hypothesis survive closed-beta evidence? *(§9)*
- **OQ-004** Is the author's day-to-day representative of broader market thesis? *(§9)*
- **OQ-005** How long does "validate, don't sell" hold before commercial pressure forces a wedge call? *(§9)*
- **OQ-006** Do LLM design agents reach the world-class bar unaided? *(§8)*
- **OQ-007** Does 2-agent MVP carry the demo, or need a third? *(§7)*
- **OQ-008** Normalize ingestion at ingest time, or store raw and project at query? *(§6)*
- **OQ-009** Is "very good" Workflow Topology + Decision Graph defensible against Linear/Notion, or do we promote one? *(§5)*
- **OQ-010** Pricing model and target price per seat? *(§9, required for falsification criterion 2)*

## 6. Constitution implications

The enrichment requires **one constitution amendment** (drafted as a
follow-up commit in this session):

- **Principle II / Architectural Constraint** — current text mandates
  polyglot persistence across three physical stores. Amend to allow
  PostgreSQL with `pgvector` and Apache AGE as a single-store option for
  MVP, with a sunset clause that revisits at scale thresholds. Bump:
  **MINOR (1.0.0 → 1.1.0)** — relaxation of an existing constraint, not
  removal of a principle.

All other principles are preserved unchanged:
- I (Intent Over Tasks) — enforced throughout §3, §5, §7.
- III (Human Governance, AI Execution) — §7 workflows, §8 approval
  surface, autonomy declarations on every agent.
- IV (Visualization as Cognition) — §6 viz architecture, world-class/very-
  good tiering rule, design references named.
- V (Evaluation-First) — §7 agent specs require eval suites; Phase 2 exit
  criteria depend on eval results.
- VI (Observable Autonomy) — Langfuse + OTEL stack; Phase 4 deliverable.
- VII (Domain-Adapter Extensibility) — §9.2 ontology-mapping table is the
  enforcement artifact.

## 7. What gets cut from the current PRD

| Current content | Disposition |
|---|---|
| Seed Domain §1 (EA-as-wedge framing) | Deleted (replaced by §9.1 dogfooding reframe) |
| Seed Domain §5 (visualization concepts) | Deleted (subsumed by §6 architecture and §5 modules) |
| Seed Domain §6 agents 3–4 (Architecture Analyst, Governance Coordinator) | Moved to post-MVP §11 |
| Current §10 candidate technology lists | Replaced by §6 decisions |
| Current §11 MVP scope (feature-name bullet list) | Replaced by §8 with acceptance criteria |
| Duplicate numbering across the two stacked docs | Eliminated — one coherent flow |

Nothing material is deleted; everything finds a new home, is replaced by
something specific, or moves to post-beta.

## 8. Deliverables

1. **Enriched PRD** — replaces source PRD content in
   `/Users/nick/Vaults/AI Knowledge/AI Knowledge/00-INBOX/context-os.md`
   (or moved to a tracked location in this repo if preferred).
2. **Constitution amendment** — `.specify/memory/constitution.md` v1.1.0
   with updated Sync Impact Report.
3. **Implementation plan** — produced by `superpowers:writing-plans` skill
   in the next step, sequencing the PRD-rewrite work itself.

## 9. Out of scope for this design

- Choosing pricing model or target seat price (OQ-010; deferred to
  closed-beta evidence).
- Recruiting / sourcing closed-beta participants (operational work, not
  product design).
- Detailed visual design specs (Figma / tokens) — these come during
  Phase 3 build, not in the PRD itself.
- Pre-emptive constitution amendments for Neo4j / Cosmograph / Temporal
  (only triggered by kill criteria firing).

## 10. Open questions about this design

- **OQ-A**: Should the enriched PRD live in the vault inbox or move into
  this repo at `docs/prd.md` for version control? (Author preference.)
- **OQ-B**: Glossary scope — definitions of core primitives only, or also
  domain terms (ADR, ICP, etc.)? Default: core primitives only.
- **OQ-C**: Does the author want the PRD to include a one-page executive
  summary suitable for a cofounder pitch read, or strictly build-team
  oriented? Default: build-team only; summary is a separate artifact.
