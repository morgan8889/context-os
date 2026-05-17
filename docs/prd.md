# Context-OS — Product Requirements Document

> **Status:** Draft (rewrite in progress). Source: see `docs/plans/2026-05-17-prd-enrichment-design.md`.
> **Constitution:** This PRD is governed by `.specify/memory/constitution.md` v1.1.0+.
> **Last updated:** 2026-05-17

## Table of Contents

1. Executive Summary
2. Vision & Thesis
3. Conceptual Model
4. User & Operator Personas
5. Product Modules
6. Platform Architecture
7. AI-Native Workflow Model
8. MVP Definition
9. Dogfooding Domain: Enterprise Architecture / PMO
10. Phased Build Plan
11. Future Vision
12. Glossary
13. Open Questions Index

---

## 1. Executive Summary

Context-OS is an AI-native operational intelligence platform. It is a single
system that holds an organization's goals, workflows, decisions, agents, and
dependencies as a living graph; uses AI agents to synthesize, route, and
recommend on top of that graph; and presents the result through interactive
topology surfaces designed for operational cognition rather than record
display. The platform's job is to compress the coordination overhead that
sits between strategic intent and execution — the manual synthesis, the
status gathering, the dependency surprises, the architecture decisions
that disappear from memory the moment they are made.

It serves three audiences. The **Strategic Operator** — a VP or Head of
Engineering, Head of Architecture, or similar — sets intent, governs
autonomy, approves consequential decisions, and reads briefings the
platform drafts on their behalf. The **Domain Practitioner** — a staff or
principal engineer, an architect, an initiative owner — submits work,
participates in reviews, and reaches into organizational memory for
rationale and prior decisions. The **Platform Operator** — at MVP, the
author dogfooding the system — directs the product, designs evaluations,
and curates the closed beta.

Three commitments separate this from conventional ops, PM, and EA tools.
First, the platform models **intent**, not tasks: goals and outcomes are
first-class, tasks are derived. Second, AI is the **operational layer**,
not a feature: agents orchestrate work, draft synthesis, surface risks,
and execute under explicit autonomy levels — humans retain governance.
Third, **visualization is cognition**: the primary interface is topology
(graphs, flow maps, scenario overlays), not dashboards or CRUD forms.

The product is pre-revenue and in initial build. MVP scope targets a
**closed beta with three to five organizations** over roughly eight
months, built by one human leveraging advanced LLM coding and design
agents. The dogfooding domain is enterprise architecture and PMO
leadership — the author's own work — used as a validation surface, not
as a commercial commitment. The commercial wedge is a hypothesis (see
§9.6) to be falsified or confirmed against closed-beta evidence.

## 2. Vision & Thesis

### 2.1 What this replaces

Conventional operational tooling was built around five failure modes the
platform exists to retire.

**Manual coordination** — status meetings whose purpose is to extract what
Jira and Slack already contain, weekly executive briefings that take an
afternoon to write by hand, follow-up loops on decisions that nobody can
find in writing. The coordination tax compounds with org size and pulls
operators away from judgment work into clerical work.

**Static records** — Jira tickets, Confluence pages, Notion docs, ADR
markdown. Each is correct on the day it was written and decays from then
on. Nothing in the tooling notices when a ticket's stated dependency no
longer matches the code, when an ADR contradicts a newer one, or when a
roadmap commitment is invalidated by a staffing change three teams over.

**Siloed systems** — engineering work in Jira, code in GitHub, decisions
in Confluence, conversations in Slack, calendars elsewhere. No single
surface reflects organizational state; humans become the integration
layer, paying the cost in attention.

**Fragmented human memory** — architecture decisions that nobody re-reads,
the rationale for an old "we picked Postgres because X" lost when the
person who picked it leaves, the same conflict surfacing every quarter
because nobody remembers it was already resolved.

**Explicit, brittle workflows** — pre-defined approval chains, hand-rolled
routing rules, ticket templates that don't adapt to context. Every
process exception becomes a coordination ticket of its own.

The platform's premise is that these are not separate problems. They are
the same problem — the absence of a persistent, semantically-aware,
agent-native operational layer — and they will not be solved by adding
more dashboards or another ticket type to the existing tools.

### 2.2 Why AI-native, why now

**AI-native** means designed *around* AI as the operational layer, not
*with* AI features bolted onto a record-keeping system. The distinction
is structural. An AI-native platform routes work to agents and humans
under explicit autonomy controls, holds context in a form agents can
reason over directly, and treats AI output as governed state rather than
suggestion text in a panel.

Three capability shifts make this newly viable. **Persistent semantic
context** — vector retrieval combined with structured graph state lets
agents recover the relevant slice of organizational history for any
query, where two years ago context was lost between sessions. **Dynamic
workflow orchestration** — agent frameworks (LangGraph, Temporal-style
durable workflows, tool-use protocols) make long-running multi-step AI
behavior reliable enough to put in production paths. **Continuous
reasoning over organizational state** — modern LLM agents can synthesize,
compare, and propose against tens of thousands of tokens of operational
context per call, with cost curves that make weekly briefings and daily
risk scans economically routine.

The moment is now and not earlier because reliable agentic execution is
new — twelve months ago, agents hallucinated tools and lost state across
turns; today, properly evaluated agents complete multi-step operational
tasks at quality that survives external review. The moment is now and
not later because category-defining platforms get built in the eighteen
months after a capability becomes reliable, before incumbents retrofit.

What the platform does **not** claim: it is not AGI, it does not propose
autonomy without governance, and it does not replace judgment. Every
agent operates under a declared autonomy level (Constitution Principle
III); every consequence-bearing action is reversible, auditable, or
human-gated.

### 2.3 What "operational cognition" means concretely

Operational cognition is the capacity to perceive, reason about, and act
on the state of an operating organization with the same fluency a senior
operator brings to a domain they know cold. It is the opposite of
reading reports.

Three concrete moments show what this looks like in use. **Pre-meeting
briefing** — five minutes before a leadership review, the platform
surfaces the three risks that have moved since last week, the two
decisions waiting on the operator, and the one dependency that just
became newly load-bearing. The operator walks in with context, not
homework. **Dependency discovery before the blocker** — a roadmap change
on team A triggers an agent's pass over the dependency graph; team C's
Q3 commitment is now at risk because of a contract they didn't know
existed, and they hear about it the same day, not in week 8. **ADR
retrieval grounded in current state** — an architect raising a proposal
sees, surfaced next to the design doc, the three prior ADRs that
constrain or contradict the proposal, with their rationale and the
people who made them — without searching, without hoping.

Operational cognition is distinct from dashboards in three ways: it is
*push* not pull (the platform brings the relevant slice to the operator,
not the operator to a query interface); it is *living* not static (state
updates continuously, not on refresh); and it is *reasoning* not record
(the surface presents conclusions and proposals, not raw rows). This is
the rationale behind Constitution Principle IV (Visualization as
Cognition) and the topology-first interface commitments in §6.3.

## 3. Conceptual Model

### 3.1 Universal cognitive primitives

The platform models everything an organization does, decides, owns, and
worries about with a small set of universal primitives. Domain-specific
concepts — ADRs, capability maps, OKRs, sprints — are adapters onto
these primitives, not parallel schemas (Constitution Principle VII).
This is the move that makes one platform serve multiple domains; the
core graph stays domain-agnostic.

| Primitive    | Description                                  | MVP-relevant? |
|--------------|----------------------------------------------|---------------|
| Goal         | Desired outcome                              | Yes           |
| Initiative   | Coordinated effort against one or more goals | Yes           |
| Workflow     | Execution sequence with agents and gates     | Yes           |
| Signal       | Incoming information or event                | Yes           |
| Agent        | Human or AI actor                            | Yes           |
| Artifact     | Output or generated content                  | Yes           |
| Decision     | Choice with rationale, alternatives, consequences | Yes      |
| Constraint   | Governance or limitation                     | Yes           |
| Dependency   | Typed relationship between entities          | Yes           |
| Capability   | Organizational function                      | Yes           |
| Risk         | Predicted or active issue                    | Yes           |
| Context      | Dynamic semantic state attached to anything  | Yes           |
| Memory       | Persistent organizational knowledge          | Yes           |
| Autonomy     | Declared AI authority level on a workflow    | Yes           |
| Simulation   | Predicted future operational state           | Post-beta     |

Domain mappings (Architecture Review → Workflow + Decision, ADR →
Decision, Portfolio → Initiative grouping, etc.) are listed in §9.2.

### 3.2 Design principles

These are the *product* principles that guide what the platform does and
refuses to do. They sit alongside the seven *engineering* principles in
the constitution — the constitution governs how the system is built;
these principles govern what it is.

**Intent Over Tasks.** Goals and outcomes are first-class. Tasks are
derived projections of intent through workflows. No orphan tasks exist
in the graph. *Forbids*: ticket-first thinking, work items without a
traceable parent goal.

**Dynamic Context.** Context evolves continuously as signals arrive,
workflows run, decisions land, and AI reasoning updates state. Context
is a live attribute, not a snapshot. *Forbids*: stale-by-design
documents, weekly refreshes as the primary update model.

**Human Governance.** Humans govern autonomy levels, approval policies,
escalation, trust boundaries, and strategic priorities. AI never
acquires governance authority. *Forbids*: autonomy escalation without
explicit human declaration; agents that grant themselves permissions.

**AI as Operational Layer.** AI is the orchestrator, analyst,
synthesizer, monitor, planner, and recommender — not a feature panel
beside the real product. Workflows route to agents by default and to
humans by exception. *Forbids*: "AI assistant" framing that treats
agents as advisory peripherals.

**Visualization as Cognition.** Primary surfaces are topology, flow
maps, and scenario overlays — designed for spatial reasoning and
multi-dimensional state perception. Dashboards and CRUD forms are not
primary. *Forbids*: spreadsheet-style listings as headline interfaces;
read-only KPI dashboards as the operator's main view.

Each product principle has an engineering counterpart in the
constitution: Intent Over Tasks ↔ Principle I; Dynamic Context ↔
Principle II (Persistent Semantic Memory); Human Governance ↔ Principle
III; AI as Operational Layer ↔ Principle V (Evaluation-First) and VI
(Observable Autonomy); Visualization as Cognition ↔ Principle IV.

### 3.3 Autonomy ladder (0–5)

Every AI-driven action declares an autonomy level. The level determines
who decides, who reviews, and what telemetry is required. The ladder is
canonical — features must not invent parallel taxonomies (per
constitutional Architectural Constraint).

| Level | Name             | Example action                              | Human gate                  | Telemetry required          |
|-------|------------------|---------------------------------------------|-----------------------------|-----------------------------|
| 0     | Human only       | Drafting an executive memo by hand          | N/A                         | Standard app traces         |
| 1     | AI recommendation | Surface "this might be a risk" inline      | Operator reads, ignores or acts | Recommendation rationale + retrieval |
| 2     | AI drafts, human approves | Generate briefing for review        | Operator approves before send | Draft + edit distance      |
| 3     | AI executes with review  | Route an approval request, post a Slack DM | Human reviews post-execution  | Action log + reversal path |
| 4     | AI autonomous with escalation | Reassign a task, update a roadmap field | Escalation rule fires on edge cases | Action + escalation criteria + tripwire log |
| 5     | Fully autonomous | Background monitoring jobs, scheduled syncs | None during run; periodic audit | Full trace; interruptible at any time |

Constitutional commitments: levels 0–3 must be reversible, auditable, or
human-gated (Principle III); levels 4–5 must publish escalation
criteria and remain interruptible. **MVP uses levels 1–3 only**; level 4
appears in post-beta for non-consequential automation; level 5 is
reserved for ambient monitoring and is not on the MVP roadmap.

### 3.4 Open Questions

- **OQ-011** Is the 0–5 ladder granular enough, or do we need sub-levels
  (e.g., 2a for AI drafts that send unless rejected within N hours)?
- **OQ-012** Can a single workflow span multiple autonomy levels, or
  must each step declare its own level discretely?
- **OQ-013** Should "Context" be a primitive or an attribute of other
  primitives? Current design treats it as a primitive because context
  itself has provenance, ownership, and decay.

## 4. User & Operator Personas

### 4.1 Strategic Operator

**Profile.** VP or Head of Engineering, Head of Architecture, or
EA-reporting-to-CTO at a Series B–D company (50–500 engineers, ≥3
teams). Owns delivery, governance, and cross-functional coordination.

**Day-to-day.**
- 1:1s with team leads and peer executives
- Architecture and design reviews (chairing or attending)
- Weekly or biweekly executive briefings to peers
- Roadmap reconciliation across initiatives and quarters
- Escalation handling and exception governance

**Cognitive load.** High and context-switching. They hold 5–10 active
initiatives, 20–50 in-flight decisions, and a constantly-shifting model
of who-owns-what across teams. The bottleneck is attention, not effort.

**Pain points.**
- Synthesis is manual: each briefing is an afternoon of grep + memory
- Dependencies surface late, often as crisis tickets in week 6
- Architecture decisions evaporate; the same conflict resurfaces yearly
- Follow-up is constant clerical work that pulls them out of judgment
- Tools don't talk; they are the integration layer

**What they want.**
- Briefings drafted *for* them, not *by* them
- Dependencies surfaced before they become blockers
- Memory of *why* decisions were made, retrievable in context
- A governance surface that adds visibility without adding ceremony

**How MVP serves them.** Executive Briefing workflow + Initiative Galaxy
+ organizational memory graph cover the primary daily-driver use case.
They are the central beta-user persona.

### 4.2 Domain Practitioner

**Profile.** Staff or principal engineer, architect, or initiative owner
inside the Strategic Operator's organization. Authors design docs,
participates in reviews, owns systems.

**Day-to-day.**
- Authoring or reviewing design docs and ADRs
- Submitting work for architecture review
- Reconciling implementation against architectural intent
- Owning one or more systems and the decisions that touch them

**Pain points.**
- Reviews are slow and ceremony-heavy
- Prior decisions are unfindable; standards drift goes unchecked
- Implementation diverges from intent and no one notices until late
- Search across Jira, Confluence, and Slack is inadequate

**What they want.**
- Faster, lower-ceremony architecture review
- Searchable, semantically-linked decision history with rationale
- AI pre-review that catches the easy stuff so humans focus on judgment
- Surfacing of prior ADRs and constraints relevant to current work

**How MVP serves them.** Decision Graph view + memory retrieval +
Dependency Mapper agent are the primary surfaces. The Architecture
Review workflow is post-MVP; Domain Practitioners get partial coverage
in MVP via the briefing workflow and memory retrieval.

### 4.3 Platform Operator (dogfooder)

**Profile.** The author of this PRD. Architecture/PMO leadership role;
runs the platform on their own organization first.

**Role at MVP.** Dogfood user, product director, eval designer,
closed-beta curator. Distinct from Strategic Operator only in
relationship to the platform itself — they have privileged access,
debugging surfaces, and the burden of getting product direction right.

**What they need that real users don't.**
- Direct database and graph access for debugging
- Verbose telemetry surfaces and trace inspection
- Eval-suite run UI and result diffing
- Ability to ship experiments per-tenant for own org
- A way to record, in the system, why product decisions were made
  (the platform must eat its own dog food on Decision storage)

**How MVP serves them.** Same product surfaces as Strategic Operator,
plus an admin module gated behind a feature flag. The Platform Operator
persona collapses into Strategic Operator at scale; it exists during
MVP because the burden of dogfooding requires capabilities production
users don't need.

### 4.4 Open Questions

- **OQ-014** Is the Domain Practitioner an MVP target or post-beta?
  Current scope serves them partially; full coverage waits on
  Architecture Review workflow.
- **OQ-015** Does the Platform Operator persona persist past MVP, or is
  it strictly a build-time construct that gets absorbed into Strategic
  Operator once the product is stable?
- **OQ-016** What additional persona may surface in closed beta (e.g.,
  "Reviewer-Only" stakeholders who consume briefings but don't act in
  the platform)?

## 5. Product Modules

The platform is composed of seven engines. Each owns a slice of the
graph, exposes a set of capabilities, and declares its AI-vs-human
ownership boundary. MVP ships a deliberate subset; the rest is deferred
to post-beta or future.

### 5.1 Intent Engine

**Purpose.** Capture and maintain strategic intent — what the
organization is trying to do, and how that decomposes into initiatives.

**Capabilities.** Goal hierarchy, initiative mapping, outcome tracking,
priority modeling, constraints management, intent decomposition,
goal-to-workflow linkage.

**Owned data.** `Goal`, `Initiative`, `Capability` (organizational
function), `Constraint`. Read-only references to `Workflow` and
`Decision`.

**AI/human boundary.** Goal setting and prioritization are human-only
(Constitution Principle III; product principle Intent Over Tasks). AI
proposes decomposition, surfaces alignment gaps, flags conflicting
priorities — never enacts them.

**MVP cut.**

| Capability                  | Status     |
|-----------------------------|------------|
| Goal hierarchy + initiative graph | MVP   |
| Outcome tracking            | MVP        |
| Priority modeling           | MVP (basic — score field per item) |
| Constraints management      | MVP        |
| AI-driven intent decomposition | Post-beta |
| Strategy map visualization  | Post-beta  |

### 5.2 Operational Flow Engine

**Purpose.** Model how work moves through the organization — workflow
topology, ownership, latency, bottlenecks.

**Capabilities.** Workflow topology mapping, human-vs-AI ownership
tracking, latency analysis, approval bottleneck detection, operational
telemetry, flow health scoring, escalation path tracking.

**Owned data.** `Workflow`, workflow step state, `Signal` ingestion
queue, telemetry attached to flow nodes.

**AI/human boundary.** AI runs the workflows under declared autonomy
levels (§3.3); humans gate at the autonomy boundary. AI proposes flow
optimizations; humans approve structural workflow changes.

**MVP cut.**

| Capability                  | Status     |
|-----------------------------|------------|
| Workflow topology view ("very good" tier, per §6.3) | MVP |
| Human-vs-AI ownership tracking | MVP     |
| Latency + bottleneck telemetry  | MVP    |
| Escalation path tracking    | MVP        |
| Flow health scoring         | Post-beta  |
| Workflow river visualization | Post-beta |

### 5.3 Organizational Memory Engine

**Purpose.** Persistent, semantically-aware organizational knowledge —
the substrate every other engine reads from.

**Capabilities.** Decision graph, rationale capture, semantic linking,
historical context retrieval, relationship modeling, knowledge
evolution tracking, pattern recognition, architecture memory.

**Owned data.** `Decision`, `Memory`, `Context`, `Dependency`,
`Artifact`. All other engines reference this engine for historical
state.

**AI/human boundary.** Humans create decisions and rationale; AI
embeds, links, and retrieves. AI proposes pattern matches and
historical analogs; humans validate before acceptance into the
canonical graph.

**MVP cut.**

| Capability                  | Status     |
|-----------------------------|------------|
| Memory graph substrate (Postgres + AGE + pgvector) | MVP |
| Decision Graph view ("very good" tier, per §6.3) | MVP |
| Rationale capture + alternatives field | MVP |
| Semantic retrieval (vector + graph) | MVP |
| Pattern recognition surfaces | Post-beta |
| Knowledge evolution timeline | Post-beta |

### 5.4 Agent Orchestration Engine

**Purpose.** Coordinate AI and human agents — routing, autonomy
enforcement, tool permissions, agent telemetry.

**Capabilities.** Multi-agent coordination, role-based AI systems,
agent routing, autonomy controls, tool permissions, workflow
delegation, agent telemetry, agent communication graph.

**Owned data.** `Agent` (identity, role, tool permissions, autonomy
declaration), agent action log, agent communication edges.

**AI/human boundary.** Routing logic is rule-based with AI proposals
allowed. Autonomy levels are human-declared and human-modifiable;
agents cannot self-elevate (Constitution Principle III).

**MVP cut.**

| Capability                  | Status     |
|-----------------------------|------------|
| Two agents (Operational Synthesizer, Dependency Mapper) | MVP |
| Tool permissions per agent  | MVP        |
| Autonomy declaration per agent | MVP     |
| Action log + reversal paths | MVP        |
| Agent orchestration UI      | Post-beta (agents configured in code in MVP) |
| Multi-agent coordination graph | Post-beta |

### 5.5 Simulation Engine

**Purpose.** Predict downstream operational impact of changes.

**Capabilities.** Dependency simulation, staffing impact analysis,
roadmap impact forecasting, delivery risk prediction, organizational
overload modeling, architecture drift prediction, capacity simulation,
escalation forecasting.

**Owned data.** `Simulation` runs and their inputs, scenario snapshots.

**AI/human boundary.** AI runs simulations on operator request; humans
interpret and act. Autonomy level 1 (recommendation) only.

**MVP cut.**

| Capability                  | Status     |
|-----------------------------|------------|
| Engine hooks (graph queryable for simulation inputs) | MVP |
| All simulation capabilities | Post-beta  |

The Simulation Engine is intentionally MVP-light. Its value depends on
data depth that only accumulates after closed beta runs for several
months; shipping it in MVP would mean shipping a feature that can't be
evaluated honestly.

### 5.6 Cognitive Load Engine

**Purpose.** Understand organizational attention and mental overhead —
where humans are saturated, where coordination is breaking down.

**Capabilities.** Attention tracking, context fragmentation detection,
coordination overhead scoring, decision fatigue indicators,
organizational load balancing, meeting burden analysis, cognitive
bottleneck detection.

**Owned data.** Derived metrics from telemetry across other engines; no
new primitives owned exclusively.

**AI/human boundary.** AI surfaces patterns; humans decide
interventions.

**MVP cut.**

| Capability                  | Status     |
|-----------------------------|------------|
| All capabilities            | Post-beta  |

Like Simulation, Cognitive Load is data-hungry. The engine ships
post-beta with a clear analytics surface; MVP collects the telemetry
that will feed it.

### 5.7 Visualization Layer

**Purpose.** Render the platform's state as topology, flow, and
overlay — the primary user surface (Constitution Principle IV).

**Capabilities.** Initiative Galaxy, Workflow Topology, Decision Graph,
strategy maps, scenario overlays, cognitive heatmaps, agent activity
streams, architecture topology views.

**Owned data.** No graph data; reads from every other engine. Owns
view-state (layout positions, user-specific filters, overlay
preferences).

**AI/human boundary.** AI proposes layouts and groupings; humans
direct the view. Visualization is read-mostly in MVP; later phases
allow inline editing of graph state.

**MVP cut.**

| Capability                  | Status     |
|-----------------------------|------------|
| Initiative Galaxy ("world-class" tier, per §6.3) | MVP |
| Workflow Topology view ("very good" tier) | MVP |
| Decision Graph view ("very good" tier) | MVP  |
| Strategy maps, scenario overlays, heatmaps, agent streams | Post-beta |

### 5.8 Open Questions

- **OQ-017** Should the Cognitive Load Engine sit beside the other
  engines or be a presentation layer over them? Current design treats
  it as a peer engine because it has its own retention/decay logic.
- **OQ-018** Does the Visualization Layer warrant its own engine, or
  should view-state live with the engines whose data it renders?

## 6. Platform Architecture

This section commits to decisions. Where the source PRD listed
candidates, this section names a single pick per layer with a "When
we'd revisit" trigger. Decisions are biased by three constraints: solo
build, advanced-LLM coding and design leverage, and closed-beta as the
MVP bar (§8.1).

### 6.1 Stack decisions

| Layer                | Decided                                          |
|----------------------|--------------------------------------------------|
| Frontend framework   | Next.js (App Router) + Zustand                   |
| Topology viz (large) | Sigma + Graphology + forceatlas2-worker          |
| Topology viz (hierarchical) | dagre layout via Graphology              |
| Topology viz (structured)   | React Flow with custom node/edge components |
| Charts / overlays    | Apache ECharts primary, Visx for bespoke         |
| Canvas (deferred)    | TLDraw — only if a workflow demands it           |
| 3D (deferred)        | react-three-fiber + drei — post-MVP              |
| Motion (everyday)    | Framer Motion                                    |
| Motion (set-piece)   | GSAP                                             |
| Design system        | Radix UI + Tailwind + custom motion/color tokens |
| Backend              | Python + FastAPI                                 |
| Data layer           | PostgreSQL + pgvector + Apache AGE (single store) |
| Workflow orchestration | LangGraph (agents) + Postgres-backed queue (durable workflows) |
| Agent runtime        | Claude API primary, OpenAI API fallback          |
| Observability (LLM)  | Langfuse                                         |
| Observability (app)  | OpenTelemetry → managed collector                |
| Auth + multi-tenant  | Clerk                                            |
| Deploy (backend)     | Fly.io or Railway                                |
| Deploy (frontend)    | Vercel                                           |

Per-pick rationale (Decided / Why / When we'd revisit) for the most
load-bearing choices follows in §6.2–§6.6.

### 6.2 Data layer topology

**Decided.** PostgreSQL as the single physical store, extended with
`pgvector` (semantic retrieval) and Apache AGE (graph queries). Three
logical roles — relational, graph, vector — addressed through separate
schemas and separate access modules. Splitting to dedicated stores is a
deployment change, not a rewrite.

**Why over alternatives.** Solo build cannot operate Postgres + Neo4j +
Qdrant at closed-beta quality. The most defensible architectural move
is to consolidate the persistence surface and pay the polyglot tax
*if* and *when* sunset triggers fire — not before. The constitution
was amended to v1.1.0 to permit this; see Architectural Constraints,
first bullet.

**When we'd revisit (per constitution sunset triggers).**
- Graph query p95 > 500ms on representative workloads despite tuning
- Vector recall@k < 70% on the canonical eval set
- Single-tenant graph exceeds ~5M nodes or ~25M edges
- `pgvector` or AGE proves unmaintained or blocks a Postgres upgrade

When a trigger fires, the affected role migrates to a dedicated store
(Neo4j or TypeDB for graph; Qdrant or Weaviate for vector) before the
next non-trivial feature ships against that surface.

**Module shape.** Three Python modules — `memory.relational`,
`memory.graph`, `memory.vector` — each exposing a query interface
independent of underlying engine. Adapters live behind these
interfaces.

**Open Question OQ-008**: normalize ingestion to the ontology at ingest
time vs. store raw vendor payloads and project at query time. Current
design: normalize at ingest (constitutional Architectural Constraint
on integration ingestion). Raw payloads retained as `Artifact` records
for audit; queries hit normalized state.

### 6.3 Visualization architecture

The Visualization Layer is the single most distinguishing surface of
the platform (Constitution Principle IV; product principle
Visualization as Cognition). Architecturally it is also the highest-
risk surface for a solo build. This subsection details the strategy.

**Substrate model: M1 (one library per view type).** Three substrate
models were considered:
- M1: best-in-class library per view type, unified by a shared design system
- M2: one unified WebGL substrate (react-three-fiber or PixiJS) under all views
- M3: canvas-first (TLDraw-style infinite canvas) as the primary paradigm

M1 was picked. M2 would consume the entire solo MVP budget on
foundation work before any feature shipped. M3 fits ops cognition
poorly because analytical overlays require first-class chart and
table affordances M3 fights. M1 trades unified rendering for unified
*design language* — coherence achieved through tokens and motion
discipline, not engine.

**Per view type:**

| View type                          | Substrate                              | Rationale |
|------------------------------------|----------------------------------------|-----------|
| Initiative Galaxy (large, force)   | Sigma + Graphology + forceatlas2-worker | Layout polymorphism, MIT, strong AI training corpus, customization ceiling |
| Workflow Topology (structured)     | React Flow + custom nodes              | Best DX for declarative graphs; status/ownership rendering is native |
| Decision Graph (hierarchical/temporal) | dagre via Graphology, rendered with Sigma or React Flow | Decisions have predecessors and alternatives — dagre fits |
| Analytical overlays (charts)       | Apache ECharts                         | World-class chart variety, dark-mode native, GPU options |
| 3D / spatial (deferred)            | react-three-fiber + drei               | Real 3D ops UX rarely beats 2D + depth cues — defer |
| Free-form canvas (deferred)        | TLDraw                                 | Adds a paradigm users must learn; defer until needed |

**Design system commitments.** A "world-class" claim is checkable. The
platform commits to:
- **Type**: variable-font hierarchy (Inter Variable or Geist); tabular
  numerics; explicit scale 12 / 13 / 14 / 16 / 20 / 24 / 32 / 48
- **Color**: dark-first; semantic palette for severity, autonomy,
  status, ownership; WCAG AA contrast; OKLCH-based scales
- **Component primitives**: Radix UI + Tailwind + thin custom layer
  (the Linear / Vercel playbook). No generic component kits.
- **Iconography**: Lucide as base + custom set for primitives (Goal,
  Autonomy, Risk, Signal)
- **Motion tokens**: duration scale, easing curves, choreography rules
  ("topology pans before overlays fade")
- **Density modes**: comfortable / dense / focus, explicitly switchable
- **Accessibility**: keyboard-first graph navigation; screen-reader
  narration of topology state

**Design references (named, to resist generic LLM defaults):**
- Motion / restraint / density: **Linear**
- Typography / dark-first: **Vercel**, **Arc**
- Large-graph rendering aesthetic: **Cosmograph demos**, **Kumu**, **GitHub Next**
- Canvas interaction: **Figma**, **TLDraw**
- Analytical overlays: **Observable**, **nivo**

**Visualization tiering rule.** MVP ships **one world-class surface**
(Initiative Galaxy) plus **two "very good" surfaces** (Workflow
Topology, Decision Graph). "Very good" means feature-complete,
defensible against Linear and Notion, no compromises on data fidelity
— but not the demo-moment surface that carries the product story.
World-class means: side-by-side with the named references at internal
design review, no one can tell which is production; demo-able for 60
seconds with zero narration.

**Sigma vs Cosmograph trade-off.** Cosmograph (GPU-accelerated, force-
only, polished out of the box) is the most natural Initiative Galaxy
choice. Sigma + Graphology (more code, more customization, MIT, large
training corpus) was picked instead. Four trade-offs decide it:
- **Layout polymorphism**: Cosmograph does only force-directed; our
  view set includes hierarchical (Decision Graph) and structured
  (Workflow Topology) — one library cannot serve all
- **License**: Cosmograph requires a commercial license for closed-
  beta SaaS; Sigma is MIT
- **Customization ceiling for "interaction and detail"**: Sigma allows
  custom node "programs" (shaders), lasso, marquee, edge bundling;
  Cosmograph styling is prop-driven only
- **AI-agent ergonomics**: Sigma has a large training corpus; LLM
  agents complete Sigma tasks more reliably

**G6 (AntV)** is documented as a half-day prototype spike before final
commit. If its built-in behaviors (lasso, minimap, edge bundling,
hierarchical layouts) save weeks of custom work, the decision may flip
to G6. **Cosmograph** remains on the table as a deferred upgrade
specifically for Initiative Galaxy if Sigma's force layout does not
sing at target scale (>50k nodes); documented as a Phase 3 spike (§10).

### 6.4 Agent runtime

**Decided.** Claude API as primary; OpenAI API as fallback for failover
and comparison evals. Single primary keeps the eval surface manageable
(Constitution Principle V).

**Why over alternatives.** Multi-provider in primary path doubles
prompt engineering, eval suite size, and tool-use compatibility work.
A single primary with a tested fallback gives operational resilience
without doubling cost.

**When we'd revisit.** Provider failure on a critical capability that
the fallback handles meaningfully better; a third provider releases a
capability we cannot match through the primary.

### 6.5 Workflow orchestration

**Decided.** **LangGraph** for agent orchestration (stateful,
programmable graphs of agent + tool calls). **Postgres-backed queue**
for durable workflow execution (delayed retries, schedule, exactly-
once semantics).

**Why over alternatives.** Temporal is the correct long-term choice
for durable workflows but is ops-heavy for solo MVP. n8n / OpenClaw /
CrewAI overlap with LangGraph for our use case; LangGraph wins on
programmability and state inspection. A Postgres queue (Apache
`pgmq`-style) is sufficient at MVP scale and aligns with the single-
store data decision (§6.2).

**When we'd revisit.** Workflow durability needs exceed what Postgres
queue + LangGraph can offer reliably (sub-second retry-budget
guarantees, cross-region replication, complex saga patterns). Trigger:
operational pain at closed beta or evidence of message loss.

**Constitutional requirement honored.** Workflows must be durable
across process restarts (Architectural Constraint). Postgres-backed
queue satisfies this.

### 6.6 Observability

**Decided.**
- **Langfuse** for LLM-specific traces (prompts, tool calls, retrieval,
  agent decisions, cost, latency, eval results)
- **OpenTelemetry** for application traces (HTTP, DB, queue) → managed
  collector (Grafana Cloud, Honeycomb, or similar — final choice
  deferred to Phase 4)
- **Postgres** for structured action logs and audit trails

**Why.** Constitutional Principle VI (Observable Autonomy) requires
that every agent action emit structured traces with: agent identity,
autonomy level, inputs, outputs, rationale, latency, cost, and
governance markers. Langfuse covers the LLM-specific fields; OTEL
covers everything else. Operators must reconstruct any AI-driven
outcome from telemetry alone.

**When we'd revisit.** If trace volume exceeds Langfuse's
self-hosted tier capacity, evaluate Phoenix (Arize) or roll a Postgres-
backed trace store ourselves.

**Architectural Constraint honored.** Telemetry stack is OTEL-
compatible. Agent-specific telemetry (Langfuse) is in addition to, not
in place of, OTEL.

### 6.7 Open Questions

- **OQ-001** Does Postgres + AGE handle our graph query patterns at
  org-scale, or do we migrate to Neo4j post-beta?
- **OQ-002** Sigma sufficient at >50k nodes on Initiative Galaxy, or
  license Cosmograph for that view specifically?
- **OQ-008** Normalize ingestion to the ontology at ingest time vs.
  store raw vendor schemas and project at query time. Current
  default: normalize at ingest, retain raw as `Artifact`. Confirm
  during Phase 1.
- **OQ-019** G6 (AntV) prototype spike outcome — does its built-in
  behavior surface flip the topology library decision?
- **OQ-020** Final managed-OTEL-collector vendor pick (Grafana Cloud,
  Honeycomb, Tempo self-hosted) deferred to Phase 4.

## 7. AI-Native Workflow Model
### 7.1 Generic workflow contract
<!-- TBD -->
### 7.2 Three canonical workflows
<!-- TBD -->
### 7.3 Agent role definitions
<!-- TBD -->
### 7.4 Open Questions
<!-- TBD -->

## 8. MVP Definition
### 8.1 MVP success bar
<!-- TBD -->
### 8.2 Build Model
<!-- TBD -->
### 8.3 In-scope features with acceptance criteria
<!-- TBD -->
### 8.4 Explicitly out of scope
<!-- TBD -->
### 8.5 Solo-build feasibility audit
<!-- TBD -->
### 8.6 Kill criteria
<!-- TBD -->
### 8.7 Open Questions
<!-- TBD -->

## 9. Dogfooding Domain: Enterprise Architecture / PMO
### 9.1 Why this is the validation domain
<!-- TBD -->
### 9.2 Domain ontology mapped to core primitives
<!-- TBD -->
### 9.3 Validation workflows
<!-- TBD -->
### 9.4 Data sources
<!-- TBD -->
### 9.5 Dogfood success metrics
<!-- TBD -->
### 9.6 Commercial hypothesis (to falsify in closed beta)
<!-- TBD -->
### 9.7 Open Questions
<!-- TBD -->

## 10. Phased Build Plan
<!-- TBD: four phases -->

## 11. Future Vision
<!-- TBD -->

## 12. Glossary
<!-- TBD -->

## 13. Open Questions Index
<!-- TBD: aggregated from all section-level Open Questions -->
