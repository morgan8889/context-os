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

Every workflow shipped on the platform must declare seven elements
before it is enabled in any environment beyond development
(Constitution Principle V). The contract is uniform; specializations
live inside the fields, not in the structure.

**1. Inputs.** Typed list of signals, artifacts, and graph entities the
workflow consumes. Each input declares its source (ingestion adapter
or graph query) and any required freshness window.

**2. Outputs.** Typed list of artifacts produced and graph mutations
performed. Each output declares its target persistence path and any
downstream workflows it triggers.

**3. Agents.** The set of AI and human agents that participate, with
each agent's declared autonomy level for this workflow (§3.3). One
agent may participate at different levels in different workflows.

**4. Human gates.** Where in the step sequence humans must approve,
review, or be notified. Maps to the autonomy ladder — a level-2 step
needs an approval gate; a level-3 step needs a post-execution review
surface; a level-4 step needs an escalation rule.

**5. Evaluation criteria.** Metrics that judge whether the workflow
produces good output. Must be measurable, with a baseline established
during Phase 2. Eval suites cover representative inputs, golden
outputs, failure modes, and governance-relevant edge cases. The
workflow may not be promoted past development without its eval suite
passing.

**6. Failure modes.** Named, with detection and recovery rules. At
minimum: hallucinated content, stale inputs, missed escalations,
agent-tool errors, partial completion across retries.

**7. Telemetry surface.** Every step emits a structured trace
conforming to the platform schema (Constitution Principle VI). The
contract specifies any workflow-specific fields beyond the standard
set (agent identity, autonomy level, inputs, outputs, rationale,
latency, cost, governance markers).

### 7.2 Three canonical workflows

#### 7.2.1 Executive Briefing (MVP)

**Inputs.** Jira issue activity (last 7 days), GitHub PR + commit
activity (last 7 days), Slack thread activity in designated channels
(last 7 days), prior Briefing artifact (most recent), open Decisions
awaiting operator action, recent Risks, current Initiative state.

**Outputs.** Markdown briefing (sections: progress, risks, decisions
awaiting you, dependencies that moved, escalations), `Artifact`
record in graph, optional Slack-or-email delivery. Side-effect:
flagged risks become `Risk` graph entries; flagged dependencies update
the dependency edges.

**Agents.** **Operational Synthesizer** (autonomy level 2: drafts,
operator approves). **Dependency Mapper** (level 1: surfaces, doesn't
modify graph without operator action).

**Human gates.** Operator approves the briefing draft before delivery.
Operator confirms any new Risk entries before they become graph state.

**Evaluation criteria.**
- Briefing accept-as-is rate ≥ 40% (edited rate < 60%)
- Manual-edit distance from LLM output to final, median < 25% token churn
- False-positive risk rate < 20% (operator overrides risk flag)
- Median draft-to-approval latency < 5 minutes operator time

**Failure modes.**
- Hallucinated stakeholders (someone named who doesn't exist) →
  detected by name-lookup against `Agent` table
- Stale dependency claims (relationship since severed) → detected by
  freshness check on `Dependency` edges
- Missed escalations (risk crossing threshold not flagged) → detected
  by counterfactual eval on known-escalation cases
- Citation errors (claim attributed to wrong artifact) → detected by
  retrieval-source consistency check

**Telemetry surface.** Standard schema + briefing-specific fields:
input-signal count per source, retrieval hit-rate, agent token cost
total, edit distance post-approval, downstream-action count.

#### 7.2.2 Architecture Review (post-beta)

**Inputs.** Design document (markdown or PDF), Jira epic, system
diagram, ADR history relevant to impacted systems, current
architecture standards, security requirements, dependency change list.

**Outputs.** Impacted-system map (graph fragment), drift assessment
against standards, conflict report against prior ADRs, draft
recommendations, risk assessment, `Decision` candidate (pending
human ratification).

**Agents.** **Architecture Analyst** (level 2: drafts, architect
approves). **Dependency Mapper** (level 1).

**Human gates.** Architect ratifies impacted-system map. Architecture
review board approves final `Decision`. AI-drafted recommendations are
suggestions; humans own the call.

**Evaluation criteria.**
- Architect-team accept rate of impacted-system map ≥ 70%
- Conflicts caught vs. missed (against human-only baseline) — at
  least parity by week 6 of run-in; improvement target ≥ 25% post-beta
- Standards-drift detection precision ≥ 70%, recall ≥ 50%
- Time-to-first-draft < 10 minutes from doc submission

**Failure modes.**
- Wrong system identified as impacted → detected by reviewer feedback
- Conflict missed against existing ADR → detected by post-decision audit
- Spurious conflict raised against superseded ADR → detected by ADR
  status check
- Standards comparison against wrong version of the standard

**Telemetry surface.** Standard schema + review-specific fields:
retrieved-ADR count and similarity scores, standards-version
references, reviewer agreement deltas, decision outcome.

#### 7.2.3 Portfolio Dependency Intelligence (post-beta)

**Inputs.** Full Initiative graph, current Roadmap state, recent
Decisions affecting initiatives, staffing changes, all Dependency
edges with timestamps.

**Outputs.** Hidden-dependency report (newly inferred edges),
cascading-delay forecast, overlapping-initiative warnings, ownership
ambiguity flags, delivery risk propagation visualization.

**Agents.** **Dependency Mapper** (level 2: proposes new graph edges
for review). **Operational Synthesizer** (level 1: surfaces the
report).

**Human gates.** Operator reviews proposed new dependency edges before
they enter the canonical graph. Operator confirms overlapping-initiative
warnings before they become tracked Risks.

**Evaluation criteria.**
- Dependency detection precision ≥ 70%, recall ≥ 50% on held-out set
- Cascade prediction usefulness rated ≥ 3/5 by operator weekly
- Ownership ambiguity flag rate calibrated such that ≥ 60% of flags
  result in operator action

**Failure modes.** Spurious dependency inference; missed cascading
delays; over-flagging ownership ambiguity to noise level.

**Telemetry surface.** Standard schema + portfolio-specific fields:
graph-walk depth, inference confidence scores, prediction-vs-outcome
deltas (tracked over rolling windows).

### 7.3 Agent role definitions

**MVP agents (2):**

#### Operational Synthesizer (MVP)
- **Responsibilities.** Generate briefings, summarize operational
  state, synthesize across signal sources, draft decision proposals.
- **Default autonomy level.** 2 (drafts, human approves).
- **Tool permissions.** Read: all graph entities, retrieval indices.
  Write: `Artifact` records (drafts), proposed `Decision` and `Risk`
  entries (pending approval). No external system writes without an
  approval gate.
- **Source workflows.** Executive Briefing (7.2.1), Portfolio
  Dependency Intelligence (7.2.3).
- **Evaluation criteria.** Inherits per-workflow eval criteria; plus
  cross-workflow consistency check (does the same fact surface
  identically across briefings and dependency reports?).

#### Dependency Mapper (MVP)
- **Responsibilities.** Discover dependencies between initiatives,
  systems, and decisions; predict delivery impacts; map organizational
  coupling.
- **Default autonomy level.** 1 (surfaces, does not modify graph).
  Escalates to level 2 within Portfolio Dependency Intelligence
  workflow where graph mutation is the purpose.
- **Tool permissions.** Read: graph (all), telemetry (latency, flow
  health). Write: proposed `Dependency` edges (pending approval).
- **Source workflows.** Executive Briefing, Portfolio Dependency
  Intelligence, Architecture Review (when shipped).
- **Evaluation criteria.** Dependency precision/recall on held-out
  set; false-positive cost (operator-rejection rate).

**Post-beta agents (2):**

#### Architecture Analyst (post-beta)
- **Responsibilities.** Review design proposals, identify conflicts
  with prior ADRs and standards, detect architecture drift, suggest
  alignment.
- **Default autonomy level.** 2 (drafts, architect approves).
- **Tool permissions.** Read: ADR history, standards documents,
  architecture topology. Write: `Decision` candidates (pending).
- **Source workflows.** Architecture Review (7.2.2).
- **Evaluation criteria.** Per Architecture Review workflow.

#### Governance Coordinator (post-beta)
- **Responsibilities.** Route approvals, monitor workflows, escalate
  blocked items, coordinate architecture reviews.
- **Default autonomy level.** 3 (executes routing with post-action
  review).
- **Tool permissions.** Read: workflow state, agent registry. Write:
  routing actions, notifications, escalation triggers.
- **Source workflows.** Architecture Review; cross-cutting governance
  for all workflows post-beta.
- **Evaluation criteria.** Routing accuracy, escalation timing,
  operator override rate (low rate signals trust; high rate signals
  miscalibration).

### 7.4 Open Questions

- **OQ-007** Does the 2-agent MVP carry the demo, or is a third agent
  (e.g., Architecture Analyst) required for closed-beta credibility?
- **OQ-021** Should a single agent participate at different autonomy
  levels in different workflows, or should we mint workflow-specific
  agent identities (e.g., `synthesizer-briefing-l2` vs
  `synthesizer-dependency-l1`)? Current design: one agent identity,
  per-workflow autonomy declaration.
- **OQ-022** How are tool permissions versioned and reviewed? When
  agent permissions expand, what is the review process?

## 8. MVP Definition

### 8.1 MVP success bar

MVP is **closed beta with three to five organizations** beyond the
dogfooding org. "Closed beta" means: each beta org has at least one
Strategic Operator persona using the platform weekly, with their org's
real Jira + GitHub + Slack data flowing through ingestion, real
briefings being generated against that data, and real Decisions being
captured. The bar is *survives contact with outside operators* — not
*the author thinks it's good*.

The "personal daily driver" bar (one user, the author) was rejected as
too soft: it doesn't force the multi-tenant, auth, onboarding, and
support investments that make the product credible. The "public-facing
showcase" bar was rejected as too hard: it requires marketing
investment and visual polish budget incompatible with solo build. The
"first design partner" bar (one external org) was considered and
upgraded to 3–5 because the wedge hypothesis (§9.6) needs that many
data points to falsify or confirm.

### 8.2 Build Model

The MVP is built by **one human (the author) leveraging advanced LLM
coding agents and AI design tools across the stack**. The PRD's
architectural choices reflect this: libraries with strong AI training
corpora are preferred (Sigma over Cosmograph partly for this reason);
design system tokens are iterated with AI assistance; component
implementations are LLM-generated and human-reviewed.

**The human's load-bearing contributions are: direction-setting,
taste, evaluation design, and integration coherence.** Everything
else is LLM leverage.

This is not a stylistic note — it is the constraint that determines
every other decision in this section. Cuts in §8.3 are sized against
solo-with-AI throughput, not team capacity. Kill criteria (§8.6)
include LLM-design ceiling triggers.

### 8.3 In-scope features with acceptance criteria

Each MVP feature is specified with four blocks: **Functional
acceptance**, **Qualitative bar**, **Evaluation**, **Out of scope for
MVP**. Per Constitution Principle V, evaluation criteria are
established before the feature is enabled past development.

#### 8.3.1 Organizational memory graph (substrate)

**Functional acceptance.**
- PostgreSQL + pgvector + Apache AGE deployed; all three roles
  addressable through their module interfaces (§6.2)
- Core primitives from §3.1 persistable with type-safe write paths
- Graph queries: 1-hop neighbors, k-hop traversal, edge filtering by
  type and timestamp
- Vector retrieval: cosine similarity over `Memory` and `Artifact`
  embeddings; top-k with score
- Rationale field on `Decision` records is non-optional
- Provenance captured on every write (source agent or human, timestamp,
  upstream signal reference)

**Qualitative bar.** None — substrate, not user-facing.

**Evaluation.**
- Performance benchmark suite (query latencies under realistic
  graph sizes) committed; runs in CI
- Schema-shape regression tests for every primitive

**Out of scope for MVP.** Graph algorithms beyond traversal (PageRank,
community detection); query-time vs. ingest-time projection toggle.

#### 8.3.2 Ingestion: Jira + GitHub + Slack

**Functional acceptance.**
- OAuth flows complete for each of Jira, GitHub, Slack
- Incremental sync (delta since last cursor) with at-least-once delivery
- Normalization to core ontology at ingest (Architectural Constraint):
  Jira issue → `Initiative` or `Workflow` step or `Risk` per type
  config; GitHub PR → `Artifact` linked to Workflow; Slack thread →
  `Signal` with provenance
- Raw payloads retained as `Artifact` records for audit
- Re-ingest of an item must update without duplicating

**Qualitative bar.** None — backend.

**Evaluation.**
- Round-trip test per source: ingest 100 known items, verify
  normalized graph state matches expected
- Latency: incremental sync completes within 60s for a 7-day window
- Failure-mode tests: vendor rate-limit, OAuth expiry, malformed payload

**Out of scope for MVP.** Confluence, Drive, Calendar, custom file
sources, real-time webhook subscriptions (poll-based sync only at
MVP).

#### 8.3.3 Two agents: Operational Synthesizer + Dependency Mapper

**Functional acceptance.**
- Both agents implemented per §7.3
- Each agent's eval suite committed and passing on golden dataset
- Telemetry per Constitution Principle VI (agent identity, autonomy
  level, inputs, outputs, rationale, latency, cost, governance
  markers)
- Tool permission scopes enforced
- Reversal path documented and tested for any write action

**Qualitative bar.** Briefings drafted by Synthesizer are usable
without re-writing (operator accepts as-is or with minor edits) on
≥ 40% of runs by week 14 of Phase 2.

**Evaluation.**
- Eval suite per §7.2.1 and §7.2.3 evaluation criteria
- Cross-workflow consistency check
- Per-week trend on accept-as-is rate logged

**Out of scope for MVP.** Architecture Analyst and Governance
Coordinator agents.

#### 8.3.4 Initiative Galaxy (world-class tier)

**Functional acceptance.**
- Renders ≥ 10k nodes and ≥ 30k edges at ≥ 30fps on M-series Mac and
  2-year-old Windows laptop
- Force layout converges within 5s on a full org-scale graph
- Lasso selection on touch, mouse, and keyboard
- Time-travel scrubber animates between two snapshots in < 500ms
- Overlays (load, risk, autonomy, ownership) compose without
  triggering re-layout
- Read-mostly: node properties viewable; editing deferred to detail
  pane (post-MVP for inline edit)

**Qualitative bar.**
- Side-by-side with Linear's graph view at internal design review,
  no one can tell which is the production product
- Demo-able for 60 seconds with zero explanation needed
- Three internal design reviews completed before closed beta; each
  documented with feedback resolution

**Evaluation.**
- Performance benchmark suite committed; runs in CI on representative
  test graph
- Design-review notes archived as a `docs/design-reviews/` set
- Frame-rate regression test in CI on a fixed graph

**Out of scope for MVP.** 3D mode, real-time multi-user cursors,
inline editing of node properties.

#### 8.3.5 Workflow Topology view (very-good tier)

**Functional acceptance.**
- Renders workflows from §5.2 with status, ownership, autonomy
  markers per node
- Bottleneck and latency overlays
- Filter by team, initiative, status
- Up to 500 nodes render with sub-second interaction

**Qualitative bar.** Defensible against Linear's project views and
Notion's database views in a side-by-side; no data fidelity gaps.

**Evaluation.**
- Visual regression tests at three viewports (mobile-landscape, laptop,
  large display)
- Manual review against reference set (§6.3 design references)

**Out of scope for MVP.** Workflow editing in the view, ML-driven
bottleneck attribution.

#### 8.3.6 Decision Graph view (very-good tier)

**Functional acceptance.**
- Renders `Decision` records with predecessor/alternatives/dependents
  edges using dagre layout
- Search and filter by date range, author, impacted system
- Rationale and alternatives visible on hover or pane
- Up to 1000 decisions render readably (collapsing/expanding clusters
  when density exceeds threshold)

**Qualitative bar.** Defensible against Confluence + manual ADR lists
in a side-by-side; surfacing of rationale and alternatives is the
differentiator.

**Evaluation.**
- Visual regression tests
- Search precision: known-decision lookup completes in < 2s

**Out of scope for MVP.** Decision drafting UI within the graph view
(write happens via workflow or admin module).

#### 8.3.7 Executive Briefing workflow E2E

**Functional acceptance.**
- Per §7.2.1 inputs/outputs/agents/gates/telemetry
- Operator can trigger a briefing on demand and on schedule
- Approval surface presents the draft with edit-in-place and approve/
  reject controls
- Approved briefing emits the configured delivery (Slack DM or email)
- Telemetry captured per Constitution Principle VI

**Qualitative bar.** Operator uses it weekly for four consecutive
weeks during Phase 2 with accept-as-is rate ≥ 40%.

**Evaluation.** Per §7.2.1 evaluation criteria.

**Out of scope for MVP.** Recurring scheduling beyond weekly; multi-
recipient routing rules; localization.

#### 8.3.8 Human approval surface

**Functional acceptance.**
- Inbox-style UI listing pending approvals across workflows
- Each approval shows: source workflow, draft artifact, agent
  identity, autonomy level, reversal path
- Approve / reject / edit actions with audit trail
- Notification on Slack and email for new pending approvals

**Qualitative bar.** Approval flow does not add ceremony — operator
should clear five pending approvals in under three minutes when
content is good.

**Evaluation.** Usability test with the dogfooding operator over four
weeks; time-to-clear-inbox metric tracked.

**Out of scope for MVP.** Delegation, batch operations, custom
approval rules.

### 8.4 Explicitly out of scope

Deferred to post-beta or future. These are real cuts, not omissions.

- **Simulation Engine** (full module) — see §5.5
- **Cognitive Load Engine** (full module) — see §5.6
- **Agent Orchestration UI** — agents configured in code in MVP
- **Architecture Review workflow** — post-beta workflow (§7.2.2)
- **Portfolio Dependency Intelligence workflow** — post-beta (§7.2.3)
- **Architecture Analyst and Governance Coordinator agents**
- **External marketplace** (third-party agents, integrations beyond
  the MVP three)
- **Mobile apps**
- **Real-time voice coordination**
- **Advanced organizational digital twin**
- **Enterprise-scale permissions** (SSO/SAML, custom RBAC)
- **On-prem deployment**
- **White-labeling and custom domains**
- **Billing and subscription flows** (closed beta is free)
- **Advanced search** (vector + keyword fusion ships; faceted
  enterprise search does not)
- **Notification routing rules** (Slack DM and email only)
- **Multi-language UI**
- **Inline graph editing** (read-mostly views in MVP)

### 8.5 Solo-build feasibility audit

The numbers are the schedule. The schedule is the load-bearing risk.

| Feature                                | Effort | Load-bearing risk           |
|----------------------------------------|--------|-----------------------------|
| Memory graph (Postgres + AGE + pgvector) | 3 wk | AGE maturity                |
| Ingestion (Jira + GitHub + Slack)      | 3 wk   | OAuth per vendor            |
| Two agents + eval suites               | 5 wk   | Eval-data acquisition       |
| Initiative Galaxy (world-class, Sigma) | 5 wk   | World-class qualitative bar |
| Workflow Topology view                 | 3 wk   | Custom node design          |
| Decision Graph view                    | 2 wk   | Layout legibility >100 decisions |
| Executive Briefing workflow E2E        | 3 wk   | Output quality variance     |
| Human approval surface                 | 1 wk   | None significant            |
| Auth + multi-tenant (Clerk)            | 2 wk   | None significant            |
| Deploy + observability                 | 1 wk   | None significant            |
| Buffer (30%)                           | 8 wk   | Unknown unknowns            |
| **Total**                              | **36 wk (~8.3 months)** | |

Audit assumes the Build Model (§8.2): one human + advanced LLM coding
and design agents. With LLM leverage removed, this estimate is not
representative; with team scaling added, the estimate shrinks but the
load-bearing risks remain.

### 8.6 Kill criteria

Explicit replan triggers. If any of these fire, scope is cut or
replanned at the next phase boundary — not at the moment of the
trigger, to avoid thrash, unless the trigger is severe.

- **AGE proves immature on real query patterns** → drop AGE, model
  the graph in plain Postgres with adjacency tables; +2 wk.
- **Sigma cannot hit the world-class bar on Galaxy within 6 wk** →
  prototype Cosmograph for Galaxy specifically; +2 wk plus license
  cost.
- **LLM design output not at world-class on Galaxy by week 14** →
  hire contract designer for 4 wk on Galaxy direction-setting, OR
  demote Galaxy to "very good," replan demo around Workflow Topology
  + Briefing.
- **Solo velocity falls below estimate by week 8** → cut to one
  ingestion source (Jira only) and one agent.
- **Workflow Topology consumes > 5 wk despite "very good" tier** →
  cut Decision Graph view from MVP.
- **Both new structured views together > 8 wk combined** → revisit at
  week 12 with hard cut-or-keep decision; preserve Galaxy + one of
  the two structured views, not both.
- **Closed-beta recruitment stalls** → narrow to 1–2 orgs (limited
  beta); treat as wedge-hypothesis test with smaller sample (Plan-B
  candidates per §9.6).

### 8.7 Open Questions

- **OQ-006** Do LLM design agents reach the world-class bar on
  Initiative Galaxy unaided, or is a contract designer required?
  Resolves by week 14 (kill criterion above).
- **OQ-009** Is "very good" Workflow Topology + Decision Graph
  actually defensible against Linear/Notion, or do we need to promote
  one of them to world-class to compete? Resolves in design reviews
  during Phase 3.
- **OQ-010** Pricing model and target price per seat. Required for
  falsification criterion 2 in §9.6. Resolves during closed beta.

## 9. Dogfooding Domain: Enterprise Architecture / PMO

### 9.1 Why this is the validation domain

**The dogfooding domain is where we live and where we validate. It is
not a commercial commitment.** The first market may turn out to be
enterprise architecture and PMO leadership; it may turn out to be
something adjacent (§9.6). The platform's design must not foreclose
either outcome.

The author's lived role is architecture and PMO leadership, so this
domain is where insight is sharpest, where the workflows are
concretely known, and where the platform can be tested against real
artifacts daily. Dogfooding lets us learn things paying users would
not tell us: how the briefing draft breaks on edge cases nobody
admits in a sales call; how the dependency map gets wrong in the
specific way that costs a quarter; whether the operator actually
opens the platform on Monday morning, or only when reminded.

Validation here unlocks the right to ship, not the right to monetize.
Closed beta participants (§9.6 ICP) test whether the dogfooding
lessons generalize beyond one person's work pattern.

### 9.2 Domain ontology mapped to core primitives

Per Constitution Principle VII (Domain-Adapter Extensibility), the
core graph stays domain-agnostic. Architecture/PMO concepts are
adapters onto the primitives in §3.1.

| Domain entity          | Maps to (core primitives)                                |
|------------------------|----------------------------------------------------------|
| Capability             | `Capability` (1:1)                                       |
| System (technical)     | `Capability` + `Constraint` (rendered as a System node)  |
| Initiative             | `Initiative` (1:1)                                       |
| Portfolio              | `Initiative` grouping (typed edge: `in-portfolio`)       |
| Vendor                 | `Agent` (external) + `Capability` (provided)             |
| Team                   | `Agent` group (typed edge: `member-of`)                  |
| Architecture Review    | `Workflow` + (often) one `Decision` output               |
| ADR                    | `Decision` with `rationale`, `alternatives`, predecessor/successor edges |
| Risk                   | `Risk` (1:1)                                             |
| Roadmap                | `Initiative` sequence over time + `Constraint` on dates  |
| Dependency             | `Dependency` (typed: blocks / informs / consumes / implements) |
| Standard               | `Constraint` (governance) + `Memory` (reference content) |

No domain-specific schema in the core graph. Adapters are read/write
modules that render domain views over primitives and accept domain-
shaped writes that decompose into primitive mutations.

### 9.3 Validation workflows

Two workflows are the operational test bed for the platform. Both are
specified per §7's workflow contract. Domain-specific eval and
failure-mode notes appear here in addition to the workflow specs.

#### 9.3.1 Executive Briefing (MVP — see §7.2.1 for full contract)

**Domain-specific evaluation.**
- Briefing accept-as-is rate by author across 30 days
- False-positive risk rate (briefing flags a risk the operator
  overrides as not-a-risk)
- Manual edit distance from LLM output to final
- Dependency-call accuracy (claimed dependencies verifiable in graph
  state)

**Domain-specific failure modes.**
- Hallucinated stakeholders — caught by `Agent`-table lookup
- Stale dependency claims — caught by edge-freshness check
- Missed escalations — caught by counterfactual eval on known cases
- Wrong-version standards citations — caught by `Standard` version
  pinning

#### 9.3.2 Architecture Review (post-MVP — see §7.2.2 for full contract)

**Domain-specific evaluation.**
- Architect-team accept rate of impacted-system map
- Conflicts caught vs. missed against human-only baseline
- Standards-drift detection precision and recall
- Time-to-first-draft from doc submission

**Domain-specific failure modes.**
- Wrong system identified as impacted
- Conflict missed against existing ADR
- Spurious conflict raised against superseded ADR
- Standards comparison against wrong version

### 9.4 Data sources

**MVP (3):** Jira, GitHub, Slack. All normalize to the core ontology
at ingest time per Constitutional Architectural Constraint; raw
payloads retained as `Artifact` records.

**Post-MVP (5):** Confluence, Google Drive, Calendar, architecture
documents (PDF / Markdown), roadmap spreadsheets.

| Source           | MVP? | Primary entity types ingested                  |
|------------------|------|-------------------------------------------------|
| Jira             | Yes  | `Initiative`, `Workflow` steps, `Risk`         |
| GitHub           | Yes  | `Artifact` (PRs, commits), `Workflow` ties     |
| Slack            | Yes  | `Signal` (threads in designated channels)      |
| Confluence       | Post-beta | `Memory` (pages), `Decision` (ADR pages) |
| Google Drive     | Post-beta | `Artifact` (docs), `Memory` (references) |
| Calendar         | Post-beta | `Signal` (meetings as signals)           |
| Architecture docs | Post-beta | `Memory`, `Decision`, `Constraint`      |
| Roadmap sheets   | Post-beta | `Initiative` time sequencing             |

### 9.5 Dogfood success metrics

Three metric blocks, measured on the dogfooding operator's own work.

**Operational metrics** — measured against the author's pre-platform
baseline.

| Metric                           | Baseline (today) | Target (Phase 2 end) |
|----------------------------------|------------------|----------------------|
| Time-to-briefing (minutes)       | 60 (manual)      | < 5 (AI-assisted)    |
| Coordination follow-ups per week | TBD (capture wk 1) | −50%               |
| Architecture-review cycle time   | TBD (capture wk 1) | −30%               |

**Intelligence metrics** — measured against held-out eval set.

| Metric                            | Target                   |
|-----------------------------------|--------------------------|
| Dependency detection precision    | ≥ 70%                    |
| Dependency detection recall       | ≥ 50%                    |
| Risk prediction usefulness rating | ≥ 60% rated "would have caught" |
| Briefing accept-as-is rate        | ≥ 40% (edited rate < 60%) |

**Experience metrics** — self-reported, weekly journal.

| Metric                                          | Format         |
|-------------------------------------------------|----------------|
| Cognitive overload rating (1–5)                 | Likert weekly  |
| Operational visibility confidence (1–5)         | Likert weekly  |
| "Would I keep using this if I weren't building it?" | Y/N weekly |

If the experience metrics trend negative for three consecutive weeks
during Phase 2 or 3, the product direction is wrong; trigger a
direction review.

### 9.6 Commercial hypothesis (to falsify in closed beta)

> **Hypothesis.** The commercial wedge is **engineering leadership at
> Series B–D companies (50–500 engineers) running architecture and
> PMO functions**. The buyer is a VP or Head of Engineering, Head of
> Architecture, or EA-reporting-to-CTO. They pay $X–$Y per seat per
> month because the platform replaces the recurring cost of manual
> operational synthesis, dependency tracking, and architecture-review
> coordination.

**ICP indicators** (used to qualify closed-beta participants):
- 50–500 engineers, distributed across ≥ 3 teams
- Has an EA function, architecture-review board, or equivalent
  governance ritual
- Uses Jira (or Linear, with adapter) + GitHub + Slack as primary
  tools
- Leadership reports > 2 hours per week on operational synthesis
  (briefings, status, dependency tracking)

**Falsification criteria.** Any one of these flips the hypothesis at
end of closed beta:
1. **ICP fit fails.** Fewer than 2 of 5 beta orgs match the ICP
   definition despite recruiting effort. (The pain isn't where we
   said it was.)
2. **Value rejection.** Orgs love the product but rate willingness-to-
   pay below $X per seat per month (target $X to be set during
   recruiting, per OQ-010). (The value cap is wrong; needs different
   positioning or pricing model.)
3. **Function mismatch.** Orgs engage but the most-used surfaces are
   non-engineering (e.g., they ask for sales-pipeline or marketing-
   operations views, not architecture reviews). (The function is
   wrong, even if the company size is right.)
4. **Buyer mismatch.** Engineering leaders see the value but the
   actual buying authority sits with COO/CFO/IT. (The sales motion is
   harder than projected.)

**Plan-B candidates** (pre-named, not pre-ranked):
- Consulting firms (architecture and transformation practices) buying
  per-client
- Internal EA teams at large enterprises (above 500 engineers) —
  slower sales, larger contracts
- Engineering operations / DevEx teams at adjacent sizing
- Cross-functional ops at PE-backed rollups (high coordination tax by
  construction)

**Decision artifact.** At end of closed beta, the dogfooding operator
publishes a wedge decision memo (committed in this repo at
`docs/decisions/`) referencing the falsification evidence, naming the
chosen wedge, and explaining what shifted.

### 9.7 Open Questions

- **OQ-003** Does the commercial-wedge hypothesis (Series B–D
  engineering leadership) survive closed-beta evidence?
- **OQ-004** Is the author's day-to-day actually representative
  enough of the broader market to validate the platform thesis?
- **OQ-005** How long does the "validate, don't sell" stance hold
  before commercial pressure forces a wedge choice?

## 10. Phased Build Plan

Four phases, sized against the 36-week feasibility audit (§8.5). Each
phase has a goal, scope, exit criteria, named risks, and the kill
criteria that apply at that phase boundary. Phase 3 carries the
load-bearing risk; everything else exists to deliver Phase 3
successfully and Phase 4 cleanly.

### Phase 1 — Foundation (weeks 1–9, ~25%)

**Goal.** Substrate ready. The platform can ingest from three sources
and persist normalized semantic state. Auth and deploy are no longer
load-bearing risks for the rest of the build.

**Scope.**
- Memory graph: PostgreSQL + pgvector + Apache AGE deployed; three
  module interfaces (relational, graph, vector)
- Ingestion: Jira, GitHub, Slack OAuth + incremental sync +
  normalization to core ontology
- Auth + multi-tenant: Clerk integration; tenant isolation at
  query layer
- Deploy: backend on Fly.io or Railway; frontend on Vercel
- Observability scaffolding: Langfuse + OpenTelemetry collectors
  wired; structured-log shape committed

**Exit criteria.**
- Author can run a full ingest against own org and see normalized
  entities in the admin UI
- Graph queries (1-hop, k-hop traversal, edge filtering) return
  correct results on real data within performance budget
- Vector retrieval over `Memory` and `Artifact` returns relevant
  top-k for known queries
- Auth + tenant isolation tested with two stub tenants

**Risks.**
- AGE maturity on real query patterns
- OAuth complexity per vendor (especially Slack scopes)

**Kill triggers active in this phase.**
- AGE proves immature → drop to plain Postgres with adjacency
  tables (+2 wk)
- Velocity below estimate by week 8 → cut to one ingestion source

### Phase 2 — Intelligence (weeks 10–18, ~25%)

**Goal.** Two agents producing real outputs against real data, with
evaluations in place and the Executive Briefing workflow running
end-to-end.

**Scope.**
- Operational Synthesizer agent + tool permissions + telemetry
- Dependency Mapper agent + tool permissions + telemetry
- Eval suites for both agents (golden datasets, failure-mode tests,
  governance-edge tests)
- Executive Briefing workflow E2E (§7.2.1): on-demand and scheduled
- Human approval surface (inbox + approve/reject/edit)
- Briefing telemetry per Constitution Principle VI

**Exit criteria.**
- Author receives a useful weekly briefing for **4 consecutive weeks**
- Manual-edit rate < 60% in those four weeks
- Eval suites pass on golden datasets; tracked in CI
- Approval surface clears the dogfooding operator's pending queue in
  under 3 minutes when content is good

**Risks.**
- Output quality variance (the headline risk of Phase 2)
- Eval-data scarcity (no golden set exists at start of phase; must be
  built from the author's manual briefings)

**Kill triggers active in this phase.**
- Briefing accept rate < 40% by week 16 → simplify scope (single-
  source briefing) and revisit prompt strategy
- LLM design output not converging on Galaxy by week 14 (concurrent
  with Phase 3 start of Galaxy work) → trigger Phase-3-level kill
  per §8.6

### Phase 3 — Cognition Surface (weeks 19–28, ~28%)

**Goal.** The visualization layer that carries the demo. One
world-class surface (Initiative Galaxy), two very-good surfaces
(Workflow Topology, Decision Graph), a shared design system, and a
motion language coherent across all three.

This is the phase with the highest load-bearing risk. The "world-
class" bar on Galaxy is the longest-tail uncertainty in the entire
build.

**Scope.**
- Initiative Galaxy (Sigma + Graphology + forceatlas2-worker)
- Workflow Topology view (React Flow + custom nodes)
- Decision Graph view (dagre via Graphology, rendered via Sigma or
  React Flow)
- Design system: Radix + Tailwind + custom motion and color tokens
- Motion language (set-piece transitions in GSAP; everyday in Framer
  Motion)
- Internal design reviews against named references (Linear, Vercel,
  Cosmograph demos)

**Exit criteria.**
- Galaxy passes internal design review against reference set
- Workflow Topology and Decision Graph ship at "very good" tier
  (defensible vs Linear / Notion side-by-side)
- Three internal design reviews completed and documented in
  `docs/design-reviews/`
- Demo-able for 60 seconds with zero narration
- Performance benchmark suite for Galaxy passing in CI

**Risks.**
- World-class qualitative bar on Galaxy is the load-bearing risk
- Cross-surface coherence (the three views feel like one product, not
  three stitched components)
- LLM design output drifting toward generic aesthetics

**Kill triggers active in this phase.**
- Galaxy not at world-class bar by week 26 → 4-week contract designer
  on direction-setting, OR demote Galaxy to "very good" and replan
  demo around Workflow Topology + Briefing
- Workflow Topology consumes > 5 wk despite "very good" tier → cut
  Decision Graph view from MVP
- Both structured views combined > 8 wk → revisit at week 12 (Phase
  2/3 boundary already passed) for hard cut-or-keep

### Phase 4 — Closed Beta Readiness (weeks 29–36, ~22%)

**Goal.** Survive contact with three to five outside organizations.
Multi-tenant hardening, onboarding flow, support workflows, telemetry
dashboards, continuous-eval, documentation.

**Scope.**
- Multi-tenant hardening (data isolation tests, tenant-scoped admin
  surfaces)
- Onboarding flow (org setup, integration connect, first briefing)
- Support workflows (issue intake, debug-trace export, tenant impersonation
  for the Platform Operator persona)
- Telemetry dashboards (managed OTEL collector live; alerts on agent
  failure rates and ingestion freshness)
- Continuous-eval (golden datasets run nightly; regressions block
  promotion)
- Doc site (`docs/` rendered via a static-site generator; getting-
  started + concepts + workflow references)

**Exit criteria.**
- First beta org onboarded successfully end-to-end
- Second org in onboarding pipeline
- Uptime ≥ 99% over trailing 30 days
- All MVP feature evaluation criteria (§8.3) passing on dogfood org
  data over a 4-week window

**Risks.**
- Schedule risk (Phase 4 consumes any prior overrun; the 30% buffer
  in §8.5 mostly lives here)
- ICP-fit risk (beta orgs harder to recruit than estimated)

**Kill triggers active in this phase.**
- Recruitment stalls → narrow to 1–2 orgs (limited beta); preserve
  as wedge-hypothesis test with smaller sample
- Onboarding takes > 1 week per org → cut scope of the onboarding
  flow; defer non-critical setup steps to manual support

## 11. Future Vision

Closed beta is the right level of ambition for MVP. What lies beyond it
is not aspirational — every capability named here has a thread back to
the conceptual model in §3 and a primitive it would use.

**Post-beta (the year after MVP completes).**
- **Architecture Review workflow** ships as a daily-driver workflow
  (§7.2.2), with the Architecture Analyst and Governance Coordinator
  agents (§7.3)
- **Portfolio Dependency Intelligence workflow** ships against full
  closed-beta data (§7.2.3)
- **Simulation Engine** module ships with dependency simulation,
  delivery-risk prediction, and staffing impact analysis (§5.5) — now
  feasible because closed-beta data depth is sufficient to evaluate
- **Cognitive Load Engine** ships against accumulated telemetry, with
  attention topology, decision fatigue indicators, and meeting burden
  surfaces (§5.6)
- **Workflow river** and **agent activity streams** visualizations
  ship as additional topology surfaces
- **Inline graph editing** moves from view-only to direct manipulation
  for selected views
- **Confluence, Drive, Calendar, and document ingestion** expand the
  source surface (§9.4)

**2–3 year horizon (if validation succeeds).**
- **Organizational digital twin** — the closed-beta validation proves
  that organizations can be modeled as living graphs; this scales the
  capability and adds simulation depth
- **Additional domains via adapters** — engineering operations,
  consulting practice management, investment research, household
  operations — all built as adapters over the core ontology
  (Constitution Principle VII), not as parallel products
- **Autonomy levels 4–5** for non-consequential automation (ambient
  monitoring, scheduled syncs) under strong governance scaffolding —
  not earlier, not without it (Constitution Principle III)
- **Strategic simulation platform** — scenario-based planning where
  operators run "what if" against the full operational graph and see
  predicted cascades
- **Cross-organization operational intelligence** — federated patterns
  across multiple beta orgs surface industry-wide signals while
  preserving tenant isolation

**Explicitly never.** A few capabilities are not on the roadmap by
principle, not by sequencing:
- The platform makes no AGI claims and proposes no path to AGI
- No autonomy level is enabled without governance scaffolding adequate
  to it (Principle III)
- No replacement of human judgment on consequence-bearing decisions —
  the platform's role is to *raise* the quality of judgment, not to
  remove it from the loop
- No vendor-specific lock-in inside the core graph (Principle VII) —
  domain support arrives as adapters, never as schema deformations

## 12. Glossary

Definitions for terms used in this PRD that may not be universally
familiar to a build-team reader. Core primitive entries are short;
the full description for each primitive is in §3.1.

**Agent.** A human or AI actor that participates in workflows. See
§3.1.

**Artifact.** An output or generated content captured in the graph
(briefing, doc, PR record, raw ingested payload). See §3.1.

**Autonomy level.** Declared AI authority on a workflow, 0–5. See
§3.3.

**Capability.** An organizational function (e.g., "billing", "incident
response"). See §3.1.

**Closed beta.** The MVP success bar: 3–5 organizations beyond the
dogfooding org, with real operators using the platform weekly. See
§8.1.

**Constraint.** A governance limitation or rule (e.g., a standard,
a budget). See §3.1.

**Context.** Dynamic semantic state attached to graph entities; has
provenance and decay. See §3.1.

**Decision.** A choice with rationale, alternatives, and consequences.
ADRs are a domain adaptation. See §3.1 and §9.2.

**Dependency.** A typed relationship between entities (`blocks`,
`informs`, `consumes`, `implements`, etc.). See §3.1.

**Dogfooding domain.** The domain in which the platform is validated
during MVP — enterprise architecture and PMO leadership. Distinct from
the commercial wedge (§9.6). See §9.

**Eval suite.** Behavioral test set for an AI agent or workflow:
representative inputs, golden outputs, failure modes, governance edge
cases. Required before any agent or workflow ships past development
(Constitution Principle V).

**Goal.** A desired outcome. First-class primitive; tasks derive from
goals via initiatives and workflows. See §3.1.

**ICP (Ideal Customer Profile).** The set of organizational
characteristics that define the target commercial customer in the
wedge hypothesis. See §9.6.

**Initiative.** A coordinated effort against one or more goals. See
§3.1.

**Memory.** Persistent organizational knowledge (decisions, rationale,
relationship history). See §3.1.

**MVP.** Minimum viable product. For this platform: closed beta with
3–5 orgs over ~8 months, built solo with LLM leverage. See §8.

**Platform Operator.** The dogfooding persona — the author of this
PRD running the platform on their own work. See §4.3.

**Primitive.** One of 15 universal cognitive entities the platform
uses to model an organization (Goal, Initiative, Workflow, Signal,
Agent, Artifact, Decision, Constraint, Dependency, Capability, Risk,
Context, Memory, Autonomy, Simulation). See §3.1.

**Risk.** A predicted or active issue. See §3.1.

**Signal.** Incoming information or event from an ingestion source.
See §3.1.

**Simulation.** Predicted future operational state. Post-beta. See
§3.1 and §5.5.

**Strategic Operator.** Primary user persona: engineering/architecture
leadership at a Series B–D company. See §4.1.

**Wedge hypothesis.** The commercial hypothesis to be falsified or
confirmed during closed beta — currently: Series B–D engineering
leadership. See §9.6.

**Workflow.** An execution sequence with declared agents, autonomy
levels, gates, evaluation, and failure modes. See §3.1 and §7.

**Workflow contract.** The seven-element specification every workflow
must declare before shipping past development. See §7.1.

**World-class vs very-good (visualization tiers).** The tiering rule
for MVP UI work. World-class = headline demo surface, indistinguishable
from named references (Linear, Vercel) at design review. Very-good =
defensible against alternatives but not the demo moment. See §6.3.

## 13. Open Questions Index

Every section-level Open Question, aggregated. All entries are open as
of this draft. When an OQ resolves, the resolution is recorded in
`docs/decisions/` and the entry here is updated.

| OQ     | Question                                                                                          | Section | Status |
|--------|---------------------------------------------------------------------------------------------------|---------|--------|
| OQ-001 | Does Postgres + AGE handle our graph query patterns at org-scale, or migrate to Neo4j post-beta?  | §6.7    | Open   |
| OQ-002 | Sigma sufficient at >50k nodes on Initiative Galaxy, or license Cosmograph for that view?         | §6.7    | Open   |
| OQ-003 | Does the commercial-wedge hypothesis (Series B–D engineering leadership) survive closed-beta evidence? | §9.7 | Open   |
| OQ-004 | Is the author's day-to-day representative enough of the broader market to validate the platform thesis? | §9.7 | Open |
| OQ-005 | How long does the "validate, don't sell" stance hold before commercial pressure forces a wedge call? | §9.7 | Open |
| OQ-006 | Do LLM design agents reach the world-class bar on Initiative Galaxy unaided, or is a contract designer required? | §8.7 | Open |
| OQ-007 | Does the 2-agent MVP carry the demo, or is a third agent required for closed-beta credibility?    | §7.4    | Open   |
| OQ-008 | Normalize ingestion to the ontology at ingest time, or store raw and project at query time?       | §6.7    | Open   |
| OQ-009 | Is "very good" Workflow Topology + Decision Graph defensible vs Linear/Notion, or do we promote one to world-class? | §8.7 | Open |
| OQ-010 | Pricing model and target price per seat (required for §9.6 falsification criterion 2)             | §8.7    | Open   |
| OQ-011 | Is the 0–5 autonomy ladder granular enough, or do we need sub-levels?                             | §3.4    | Open   |
| OQ-012 | Can a single workflow span multiple autonomy levels, or must each step declare its own discretely? | §3.4   | Open   |
| OQ-013 | Should "Context" be a primitive or an attribute of other primitives?                              | §3.4    | Open   |
| OQ-014 | Is the Domain Practitioner persona an MVP target or post-beta?                                    | §4.4    | Open   |
| OQ-015 | Does the Platform Operator persona persist past MVP, or get absorbed into Strategic Operator?     | §4.4    | Open   |
| OQ-016 | What additional personas may surface in closed beta (e.g., "Reviewer-Only" stakeholders)?         | §4.4    | Open   |
| OQ-017 | Should the Cognitive Load Engine be a peer engine or a presentation layer over others?            | §5.8    | Open   |
| OQ-018 | Does the Visualization Layer warrant its own engine, or should view-state live with each engine?  | §5.8    | Open   |
| OQ-019 | G6 (AntV) prototype spike — does its built-in behavior surface flip the topology library decision? | §6.7   | Open   |
| OQ-020 | Final managed-OTEL-collector vendor pick (Grafana Cloud, Honeycomb, Tempo self-hosted)             | §6.7    | Open   |
| OQ-021 | Should one agent participate at different autonomy levels in different workflows, or mint workflow-specific agent identities? | §7.4 | Open |
| OQ-022 | How are agent tool permissions versioned and reviewed when they expand?                            | §7.4    | Open   |

**Resolution discipline.** When an OQ resolves:
1. Write a decision memo under `docs/decisions/OQ-NNN-<slug>.md`
2. Update the relevant section in this PRD to reflect the resolution
3. Mark the OQ here as `Resolved (→ link to memo)`
4. Update the `Last updated` date in the PRD header
