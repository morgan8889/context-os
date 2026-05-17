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
<!-- TBD -->
### 3.2 Design principles
<!-- TBD -->
### 3.3 Autonomy ladder (0–5)
<!-- TBD -->
### 3.4 Open Questions
<!-- TBD -->

## 4. User & Operator Personas
### 4.1 Strategic Operator
<!-- TBD -->
### 4.2 Domain Practitioner
<!-- TBD -->
### 4.3 Platform Operator (dogfooder)
<!-- TBD -->
### 4.4 Open Questions
<!-- TBD -->

## 5. Product Modules
<!-- TBD: one subsection per module, 7 total -->

## 6. Platform Architecture
### 6.1 Stack decisions
<!-- TBD -->
### 6.2 Data layer topology
<!-- TBD -->
### 6.3 Visualization architecture
<!-- TBD -->
### 6.4 Agent runtime
<!-- TBD -->
### 6.5 Workflow orchestration
<!-- TBD -->
### 6.6 Observability
<!-- TBD -->
### 6.7 Open Questions
<!-- TBD -->

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
