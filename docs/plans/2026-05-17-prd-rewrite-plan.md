# PRD Rewrite Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rewrite `context-os.md` from a two-document stack into a coherent, build-team-ready PRD per the approved Layered Platform Doc design.

**Architecture:** Section-by-section drafting against the design doc's TOC (§4 of `2026-05-17-prd-enrichment-design.md`). Each task produces one PRD section, self-reviewed against acceptance criteria, then committed. Cross-cutting passes at the end ensure references resolve, Open Questions are indexed, and the glossary is complete.

**Tech Stack:** Markdown. Source material in two places: the current PRD (in vault inbox) and the design doc (in repo). No code in this plan — pure documentation work.

---

## Pre-flight

**Working file location decision:** The design doc's OQ-A asks where the enriched PRD lives. Default for this plan: **`/Users/nick/Code/context-os/docs/prd.md`** (repo, version-controlled). The source PRD in the vault stays untouched until the rewrite is approved; at that point a final task copies/symlinks/relocates per author preference.

**Branch:** Per constitution §Governance, feature work uses a feature branch.

**Source references** used throughout the plan:
- **SOURCE-PRD**: `/Users/nick/Vaults/AI Knowledge/AI Knowledge/00-INBOX/context-os.md`
- **DESIGN-DOC**: `/Users/nick/Code/context-os/docs/plans/2026-05-17-prd-enrichment-design.md`
- **CONSTITUTION**: `/Users/nick/Code/context-os/.specify/memory/constitution.md`

---

### Task 0: Create feature branch and scaffold the working PRD file

**Files:**
- Create: `docs/prd.md` (empty scaffold with TOC + section headings + `<!-- TBD -->` markers)

**Step 1: Create feature branch**

```bash
git checkout -b feature/prd-rewrite
```

Expected: switched to a new branch, `git status` shows clean.

**Step 2: Create scaffold**

Write `docs/prd.md` with this content (just headings, all bodies `<!-- TBD -->`):

```markdown
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
<!-- TBD -->

## 2. Vision & Thesis
### 2.1 What this replaces
<!-- TBD -->
### 2.2 Why AI-native, why now
<!-- TBD -->
### 2.3 What "operational cognition" means concretely
<!-- TBD -->

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
```

**Step 3: Commit scaffold**

```bash
git add docs/prd.md
git commit -m "docs: scaffold enriched PRD with TOC and section placeholders

Working file at docs/prd.md per design doc default. Vault source PRD
remains untouched until rewrite is approved.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 1: §1 Executive Summary

**Files:**
- Modify: `docs/prd.md` (replace `## 1. Executive Summary` body)

**Source references:**
- SOURCE-PRD lines 7–50 (current §1 Executive Summary)
- DESIGN-DOC §2 (Goals) and §5.1 (Architectural decisions summary)
- CONSTITUTION (for principle anchors)

**Section content checklist:**
- [ ] One paragraph: what Context-OS is (in plain language, not marketing)
- [ ] One paragraph: who it's for (the three personas from §4, named not described)
- [ ] One paragraph: how it differs from traditional ops/PM tools (intent over tasks, AI-native, viz as cognition, organizational memory)
- [ ] One paragraph: current status (MVP scope, closed-beta target, solo + LLM build model)
- [ ] No new content not supported by later sections — this is a recap, not a place to introduce ideas
- [ ] Max ~400 words

**Acceptance criteria:**
- A reader who stops after §1 understands what Context-OS is, who it serves, why it's different, and where the project is in its lifecycle.
- No forward references to subsection numbers (keep it readable standalone).
- No sentence is unsupported by content elsewhere in the doc.

**Step 1: Read source materials**

Read SOURCE-PRD §1 (lines 7–50), DESIGN-DOC §2 and §5, CONSTITUTION preamble.

**Step 2: Draft §1**

Replace `<!-- TBD -->` under `## 1. Executive Summary` with 4 paragraphs per the checklist.

**Step 3: Self-review**

Re-read draft. For each checklist item, mark [x] or fix. For each sentence, confirm it's supported elsewhere in the doc (or in source materials for sections not yet drafted).

**Step 4: Commit**

```bash
git add docs/prd.md
git commit -m "docs(prd): write §1 Executive Summary

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 2: §2 Vision & Thesis

**Files:**
- Modify: `docs/prd.md` (replace 3 subsections: 2.1, 2.2, 2.3)

**Source references:**
- SOURCE-PRD lines 7–74 (Executive Summary + Product Vision)
- SOURCE-PRD lines 178–236 (Design Principles 5.1–5.5)
- DESIGN-DOC §4 TOC entry for §2

**Section content checklist:**

**2.1 What this replaces** — ~250 words
- [ ] Name 3–4 concrete failure modes of current ops tooling (manual coordination, static records, siloed systems, fragmented human memory, explicit workflows that don't adapt)
- [ ] For each failure mode: a specific example a reader recognizes (status meetings to gather what Jira already knows; ADRs that nobody re-reads; dependency surprises in week 6 of a quarter)
- [ ] Avoid product/vendor name-calling

**2.2 Why AI-native, why now** — ~300 words
- [ ] What "AI-native" means here (not "has AI features" — designed around AI as the operational layer)
- [ ] Three capability shifts that make this newly possible: persistent semantic context, dynamic workflow orchestration, continuous reasoning over org state
- [ ] Why the timing is now, not 2 years ago and not 2 years from now (LLM agent reliability, tool-use maturity, multimodal grounding)
- [ ] What this does NOT claim (not AGI, not autonomy without governance, not replacement of judgment)

**2.3 What "operational cognition" means concretely** — ~300 words
- [ ] Working definition (1 sentence)
- [ ] Three example moments where operational cognition shows up: pre-meeting briefing that includes the right risks, dependency discovery before a blocker hits, ADR retrieval grounded in current architecture state
- [ ] Contrast with "dashboards" and "reports" (push vs. pull; static vs. living; record vs. reasoning)
- [ ] Tie to Constitution Principle IV (Viz as Cognition) — this is the rationale

**Acceptance criteria:**
- A skeptical reader leaves §2 convinced that (a) the problem is real, (b) the moment is right, (c) the product category is well-defined.
- No section over 350 words.
- Every claim has either an example, a citation to a constitution principle, or a forward link to a later concrete section.

**Step 1: Read source materials**

Read SOURCE-PRD lines 7–74 and 178–236.

**Step 2: Draft 2.1**

Replace `<!-- TBD -->` under `### 2.1` with the failure-modes content per checklist.

**Step 3: Draft 2.2**

Replace `<!-- TBD -->` under `### 2.2`.

**Step 4: Draft 2.3**

Replace `<!-- TBD -->` under `### 2.3`.

**Step 5: Self-review**

For each subsection, verify checklist completion and word count.

**Step 6: Commit**

```bash
git add docs/prd.md
git commit -m "docs(prd): write §2 Vision & Thesis (replaces / why-now / operational cognition)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 3: §3 Conceptual Model

**Files:**
- Modify: `docs/prd.md` (subsections 3.1, 3.2, 3.3, 3.4)

**Source references:**
- SOURCE-PRD lines 240–260 (Universal Cognitive Primitives table)
- SOURCE-PRD lines 178–236 (Design Principles)
- SOURCE-PRD lines 491–501 (Autonomy Levels table)
- CONSTITUTION Core Principles (entire section)

**Section content checklist:**

**3.1 Universal cognitive primitives** — table + ~200 words intro
- [ ] Lead with 1 paragraph: these are the platform's ontology; everything domain-specific is an adapter (per Constitution Principle VII)
- [ ] Table: 15 primitives from SOURCE-PRD lines 242–259, with column for "MVP-relevant?" (yes/no)
- [ ] Note: domain mappings live in §9.2, not here

**3.2 Design principles** — ~400 words
- [ ] 5 principles from SOURCE-PRD §5.1–5.5: Intent Over Tasks, Dynamic Context, Human Governance, AI as Operational Layer, Viz as Cognition
- [ ] For each: 1 sentence what it means; 1 sentence what it forbids
- [ ] Cross-reference to corresponding Constitution principle (these PRD principles are *product* principles; constitution principles are *engineering* principles — explain the relationship)

**3.3 Autonomy ladder (0–5)** — table + ~300 words
- [ ] Table from SOURCE-PRD lines 493–501 with one row per level
- [ ] Add columns: example agent action, required human gate, escalation policy
- [ ] Note Constitution Principle III: levels ≤3 gated by human approval; 4–5 require escalation criteria
- [ ] Note: MVP uses levels 1–3 only; 4–5 are post-beta

**3.4 Open Questions** — bullet list, 3–5 entries with OQ numbers
- [ ] Examples: "Is the 0–5 ladder granular enough for governance, or do we need sub-levels?", "Should every agent have a fixed level, or can level be context-dependent?"
- [ ] Reserve OQ numbers in the §13 index (decide numbering convention here: OQ-NNN, monotonic across the whole doc)

**Acceptance criteria:**
- A build-team reader understands the platform's ontology, design principles, and autonomy model after §3 without needing to read further.
- Every entity used in §5–§10 is defined here.
- Open Questions surface real ambiguity, not rhetorical questions.

**Step 1: Read source materials**

Lines noted above.

**Step 2: Draft 3.1 with primitives table**

**Step 3: Draft 3.2**

**Step 4: Draft 3.3 with autonomy table**

**Step 5: Draft 3.4 Open Questions**

**Step 6: Self-review**

**Step 7: Commit**

```bash
git add docs/prd.md
git commit -m "docs(prd): write §3 Conceptual Model (primitives, principles, autonomy)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 4: §4 Personas

**Files:**
- Modify: `docs/prd.md` (subsections 4.1, 4.2, 4.3, 4.4)

**Source references:**
- DESIGN-DOC §5.x Personas design (in Section 5 of design doc)
- No source-PRD content (this is new)

**Section content checklist:**

For each persona (4.1 Strategic Operator, 4.2 Domain Practitioner, 4.3 Platform Operator):
- [ ] Profile (role, company stage, team context) — 1 sentence
- [ ] Day-to-day (3–5 representative activities) — bullet list
- [ ] Cognitive load profile — 1 paragraph
- [ ] Pain points (3–5) — bullet list, specific not generic
- [ ] What they want from the platform — bullet list
- [ ] How MVP serves them (or doesn't) — 1 paragraph
- [ ] ~200 words total per persona

**4.4 Open Questions:**
- [ ] e.g., "Is the Domain Practitioner persona an MVP target or post-beta?", "Does the Platform Operator persona collapse into Strategic Operator over time?"

**Acceptance criteria:**
- Each persona is specific enough that a build-team reader can write user stories from it.
- Personas don't blur into each other (test: can you tell which persona a feature serves?).
- The Platform Operator persona is honest about being the author dogfooding.

**Step 1: Draft 4.1**
**Step 2: Draft 4.2**
**Step 3: Draft 4.3**
**Step 4: Draft 4.4**
**Step 5: Self-review**
**Step 6: Commit**

```bash
git add docs/prd.md
git commit -m "docs(prd): write §4 Personas (Strategic Operator, Domain Practitioner, Platform Operator)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 5: §5 Product Modules

**Files:**
- Modify: `docs/prd.md` (replace §5 with 7 module subsections + open questions)

**Source references:**
- SOURCE-PRD lines 262–449 (Modules 1–7: Intent, Operational Flow, Memory, Agent Orchestration, Simulation, Cognitive Load, Visualization)

**Section content checklist:**

For each module (7 total):
- [ ] Purpose — 1 sentence
- [ ] Capabilities — bullet list, drawn from current SOURCE-PRD content
- [ ] Owned data (which primitives from §3.1) — bullet list
- [ ] AI/human boundary — 1 paragraph: which capabilities are agent-driven, which are human-driven, which are mixed
- [ ] MVP-vs-future cut — table with each capability marked: MVP / post-beta / future
- [ ] Open Questions specific to this module (if any)
- [ ] ~250 words per module

**Modules:**
1. Intent Engine
2. Operational Flow Engine
3. Organizational Memory Engine
4. Agent Orchestration Engine
5. Simulation Engine
6. Cognitive Load Engine
7. Visualization Layer

**MVP cuts per DESIGN-DOC §5.4:**
- Module 1 (Intent): minimal MVP (goals graph, initiative graph)
- Module 2 (Flow): Workflow Topology view is MVP at "very good" tier
- Module 3 (Memory): full MVP substrate + Decision Graph view at "very good" tier
- Module 4 (Agent Orchestration): 2 agents in MVP, no orchestration UI
- Module 5 (Simulation): post-beta (engine hooks only in MVP)
- Module 6 (Cognitive Load): post-beta
- Module 7 (Visualization): Initiative Galaxy as world-class MVP surface; topology + decision graph at very-good tier

**Acceptance criteria:**
- A reader can scan §5 and see what's in MVP and what's deferred for each module.
- Each module's owned data is unambiguous — no overlap with another module.
- AI/human boundaries respect Constitution Principle III.

**Step 1: Read SOURCE-PRD lines 262–449**

**Steps 2–8: Draft each module (one commit per module is overkill; group into one task)**

**Step 9: Self-review against the DESIGN-DOC §5.4 cuts**

**Step 10: Commit**

```bash
git add docs/prd.md
git commit -m "docs(prd): write §5 Product Modules (7 modules + MVP-vs-future cuts)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 6: §6 Platform Architecture

**Files:**
- Modify: `docs/prd.md` (subsections 6.1 through 6.7)

**Source references:**
- SOURCE-PRD lines 506–572 (current candidate lists)
- DESIGN-DOC §5.1 (Architectural decisions table) and Section 2 (deep viz dive)
- CONSTITUTION (Architectural Constraints section)

**Section content checklist:**

**6.1 Stack decisions** — full table per DESIGN-DOC §5.1, plus 1 paragraph per pick explaining "Decided / Why / When we'd revisit"

For each layer in the stack table:
- [ ] **Decided:** the pick
- [ ] **Why over alternatives:** 1–2 lines naming the closest alternative and what made it lose
- [ ] **When we'd revisit:** trigger condition (e.g., "if Sigma can't hit world-class on Galaxy in 6 weeks, prototype Cosmograph")

**6.2 Data layer topology** — ~400 words + diagram description
- [ ] PostgreSQL + pgvector + Apache AGE as single physical store
- [ ] Logical separation: relational module, graph module, vector module
- [ ] Reference Constitution v1.1.0 amendment (single-store with sunset triggers)
- [ ] List sunset triggers verbatim from constitution
- [ ] Note Open Question OQ-008 (normalize at ingest vs project at query)

**6.3 Visualization architecture** — ~600 words, the longest subsection
- [ ] Substrate model: M1 (one library per view type) — picked over M2 and M3
- [ ] Per view type: Initiative Galaxy → Sigma+Graphology+forceatlas2-worker; Workflow Topology → React Flow; Decision Graph → dagre layout via Sigma or React Flow
- [ ] Design system: Radix + Tailwind + custom motion/color tokens
- [ ] Design references named: Linear, Vercel, Arc, Cosmograph demos, Kumu, GitHub Next
- [ ] World-class vs very-good tiering rule (verbatim from DESIGN-DOC §5.2)
- [ ] Sigma vs Cosmograph trade-off summary (paragraph each: layout polymorphism, license, customization ceiling, AI-agent ergonomics)
- [ ] G6 (AntV) noted as half-day spike before commit
- [ ] Cosmograph noted as deferred upgrade for Galaxy if Sigma doesn't sing at scale

**6.4 Agent runtime** — ~150 words
- [ ] Claude API primary, OpenAI fallback
- [ ] Single primary keeps eval surface manageable
- [ ] Note Constitution Principle V (eval-first)

**6.5 Workflow orchestration** — ~200 words
- [ ] LangGraph for agents, Postgres-backed queue for workflows
- [ ] Defer Temporal until closed beta demands it
- [ ] Note Constitution requirement: workflows must be durable across restarts

**6.6 Observability** — ~200 words
- [ ] Langfuse (LLM traces) + OpenTelemetry (app traces) + Postgres logs
- [ ] Reference Constitution Principle VI (Observable Autonomy) trace schema requirements
- [ ] Telemetry stack must be OTEL-compatible per Architectural Constraints

**6.7 Open Questions** — bullet list with OQ numbers
- [ ] OQ-001 (AGE at scale, see DESIGN-DOC §5.12)
- [ ] OQ-002 (Sigma vs Cosmograph for Galaxy)
- [ ] OQ-008 (normalize at ingest vs query)
- [ ] Any new ones surfaced during drafting

**Acceptance criteria:**
- Every layer has a single decided pick — no "or" in the decisions table.
- Every architectural choice traces to either a constitution principle or a design-doc rationale.
- A build-team engineer can start `git init` on a stack repo after reading §6 alone.

**Step 1: Read SOURCE-PRD lines 506–572 + DESIGN-DOC §5.1 + DESIGN-DOC Section 2 (viz deep dive) + CONSTITUTION Architectural Constraints**

**Step 2: Draft 6.1 stack table + per-pick rationale**

**Step 3: Draft 6.2 data layer**

**Step 4: Draft 6.3 visualization (longest — budget extra time)**

**Step 5: Draft 6.4, 6.5, 6.6**

**Step 6: Draft 6.7 Open Questions with OQ numbers**

**Step 7: Self-review — check every pick has Decided/Why/Revisit blocks**

**Step 8: Commit**

```bash
git add docs/prd.md
git commit -m "docs(prd): write §6 Platform Architecture (decisions, viz deep dive, stack, data, observability)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 7: §7 AI-Native Workflow Model

**Files:**
- Modify: `docs/prd.md` (subsections 7.1 through 7.4)

**Source references:**
- SOURCE-PRD lines 452–501 (Traditional vs AI-Native Workflow + Autonomy Levels)
- SOURCE-PRD lines 615–673 (Example workflows 1–3, original generic doc)
- SOURCE-PRD lines 755–826 (Workflows 1–3 in seed-domain doc — more detailed versions)
- SOURCE-PRD lines 883–924 (4 agent definitions)
- DESIGN-DOC §5.4 (MVP feature surface — 2 agents in MVP)

**Section content checklist:**

**7.1 Generic workflow contract** — ~300 words
- [ ] What every workflow must declare: inputs, outputs, agents, autonomy level, human gates, evaluation criteria, failure modes
- [ ] This is the contract format used in 7.2 and 9.3
- [ ] Reference Constitution Principle V (eval-first) and VI (observable)

**7.2 Three canonical workflows** — three sub-blocks
- [ ] **7.2.1 Executive Briefing** (MVP) — full spec per contract: inputs (Jira + GitHub + Slack threads), outputs (markdown briefing + decision proposals + risk callouts), agents (Synthesizer, Dependency Mapper), autonomy level (3: AI executes with review), eval criteria (briefing accept rate, manual-edit distance, false-positive risk rate), failure modes (hallucinated stakeholders, stale dependency claims, missed escalations)
- [ ] **7.2.2 Architecture Review** (post-beta) — full spec
- [ ] **7.2.3 Portfolio Dependency Intelligence** (post-beta) — full spec

**7.3 Agent role definitions** — table + per-agent block
- [ ] **MVP agents (2):**
  - Operational Synthesizer — responsibilities, default autonomy level, tool permissions, eval criteria, source workflows
  - Dependency Mapper — same fields
- [ ] **Post-beta agents (2):**
  - Architecture Analyst
  - Governance Coordinator
- [ ] Each agent block ~120 words

**7.4 Open Questions**
- [ ] OQ-007 (does 2-agent MVP carry the demo, or need a third?)
- [ ] Any new ones

**Acceptance criteria:**
- Every workflow has an evaluation criterion that's measurable, not aspirational.
- Every agent has explicit tool permissions and autonomy declaration.
- MVP vs post-beta is unambiguous.

**Step 1: Read source materials**
**Step 2: Draft 7.1 workflow contract**
**Step 3: Draft 7.2.1 Executive Briefing in full spec**
**Step 4: Draft 7.2.2 and 7.2.3**
**Step 5: Draft 7.3 agent roles**
**Step 6: Draft 7.4 Open Questions**
**Step 7: Self-review against contract format**
**Step 8: Commit**

```bash
git add docs/prd.md
git commit -m "docs(prd): write §7 Workflow Model (contract, 3 canonical workflows, 4 agents)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 8: §8 MVP Definition

**Files:**
- Modify: `docs/prd.md` (subsections 8.1 through 8.7)

**Source references:**
- SOURCE-PRD lines 575–611 (current MVP section)
- DESIGN-DOC §5.4 (MVP feature surface), §5.5 (acceptance criteria format), §5.6 (feasibility audit), §5.7 (kill criteria), §5.8 (Build Model)

**Section content checklist:**

**8.1 MVP success bar** — ~150 words
- [ ] "Closed beta with 3–5 organizations" as the bar
- [ ] What "survives contact with outside orgs" means (multi-tenant-lite, basic auth, demo-able, support workflows)
- [ ] Why this bar over alternatives (personal-use bar too soft; public-launch bar too hard)

**8.2 Build Model** — verbatim from DESIGN-DOC §5.8, ~200 words
- [ ] Solo + advanced LLMs for coding and design
- [ ] Human load-bearing contributions: direction-setting, taste, eval design, integration coherence
- [ ] Architectural reflection: library picks favor strong AI training corpora

**8.3 In-scope features with acceptance criteria** — the longest subsection
- [ ] Feature list per DESIGN-DOC §5.4 (11 features, 8 MVP + 3 deferred)
- [ ] For each MVP feature (8), full block: Functional acceptance / Qualitative bar / Evaluation / Out of scope for MVP
- [ ] Initiative Galaxy block uses verbatim example from DESIGN-DOC §5.5
- [ ] Other 7 features get parallel structure

**8.4 Explicitly out of scope** — bullet list, ~150 words
- [ ] From SOURCE-PRD lines 603–611 plus closed-beta-context exclusions: SSO/SAML, custom RBAC, on-prem, white-labeling, billing, advanced search, multi-language, mobile apps

**8.5 Solo-build feasibility audit** — verbatim from DESIGN-DOC §5.6 table
- [ ] Table with 11 rows (10 features + buffer)
- [ ] 36 weeks total
- [ ] Risk column populated

**8.6 Kill criteria** — verbatim from DESIGN-DOC §5.7
- [ ] 6+ kill triggers with their actions
- [ ] These flow into Phase-level kill criteria in §10

**8.7 Open Questions**
- [ ] OQ-006 (LLM design ceiling)
- [ ] OQ-009 (very-good tier defensibility)
- [ ] OQ-010 (pricing model)
- [ ] Any new

**Acceptance criteria:**
- Every MVP feature has a measurable Functional acceptance block.
- Every kill trigger has a defined replan action.
- 8.5 feasibility audit math adds up.

**Step 1: Read DESIGN-DOC §5.4–5.8**
**Step 2: Draft 8.1, 8.2 (short)**
**Step 3: Draft 8.3 — one block per MVP feature**
**Step 4: Draft 8.4, 8.5, 8.6**
**Step 5: Draft 8.7 Open Questions**
**Step 6: Self-review — re-verify 8.5 math**
**Step 7: Commit**

```bash
git add docs/prd.md
git commit -m "docs(prd): write §8 MVP Definition (success bar, features+ACs, feasibility audit, kill criteria)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 9: §9 Dogfooding Domain

**Files:**
- Modify: `docs/prd.md` (subsections 9.1 through 9.7)

**Source references:**
- SOURCE-PRD lines 689–1038 (entire second/seed-domain numbered sequence)
- DESIGN-DOC §5.9 (reframing principle), §5.10 (commercial hypothesis)

**Section content checklist:**

**9.1 Why this is the validation domain** — ~250 words
- [ ] Reframing principle verbatim from DESIGN-DOC §5.9
- [ ] Author's lived role context
- [ ] Validation > sales: dogfooding teaches what paying users wouldn't say
- [ ] Explicit non-claim: not the commercial wedge (defer to 9.6)

**9.2 Domain ontology mapped to core primitives** — table
- [ ] 12 domain entities from SOURCE-PRD lines 736–750
- [ ] Each maps to one or more core primitives from §3.1
- [ ] Adapter pattern per Constitution Principle VII
- [ ] No domain-specific schema in the core graph

**9.3 Validation workflows** — two workflows, full specs
- [ ] 9.3.1 Executive Briefing (cross-reference to §7.2.1; expand domain-specific eval here)
- [ ] 9.3.2 Architecture Review (cross-reference to §7.2.2; expand domain-specific eval here)

**9.4 Data sources** — ~150 words + table
- [ ] MVP: Jira, GitHub, Slack
- [ ] Post-MVP: Confluence, Drive, Calendar, architecture docs, roadmap spreadsheets
- [ ] All normalize to ontology at ingest (constraint per constitution)

**9.5 Dogfood success metrics** — three blocks (operational, intelligence, experience)
- [ ] Operational: time-to-briefing, follow-ups/week, review cycle time
- [ ] Intelligence: dependency precision/recall, risk usefulness, briefing accept rate
- [ ] Experience: weekly journal Likert ratings, "would I keep using this" Y/N
- [ ] All from DESIGN-DOC §5.9 (Dogfood success metrics block)

**9.6 Commercial hypothesis (to falsify in closed beta)** — verbatim from DESIGN-DOC §5.10
- [ ] Hypothesis statement
- [ ] ICP indicators
- [ ] Four falsification criteria
- [ ] Plan-B candidates
- [ ] Commitment to publish wedge decision memo at end of closed beta

**9.7 Open Questions**
- [ ] OQ-003, OQ-004, OQ-005 from DESIGN-DOC §5.12
- [ ] Any new

**Acceptance criteria:**
- §9 is unambiguously about validation, not commercial commitment.
- Domain ontology table has zero domain entities that don't map onto a core primitive.
- Falsification criteria are measurable, not subjective.

**Step 1: Read SOURCE-PRD lines 689–1038**
**Step 2: Draft 9.1 reframing**
**Step 3: Draft 9.2 ontology table**
**Step 4: Draft 9.3 with cross-references**
**Step 5: Draft 9.4, 9.5**
**Step 6: Draft 9.6 with falsification criteria**
**Step 7: Draft 9.7 Open Questions**
**Step 8: Self-review — every domain entity maps to a primitive**
**Step 9: Commit**

```bash
git add docs/prd.md
git commit -m "docs(prd): write §9 Dogfooding Domain (validation reframe, ontology, hypothesis to falsify)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 10: §10 Phased Build Plan

**Files:**
- Modify: `docs/prd.md` (replace §10 with 4 phase blocks)

**Source references:**
- DESIGN-DOC §5.11 (Phased Build Plan)
- SOURCE-PRD lines 974–1013 (current Phase 1–4 sketches in seed-domain doc)

**Section content checklist:**

Four phase blocks per DESIGN-DOC §5.11:

For each phase:
- [ ] Phase name and week range
- [ ] **Goal** (1 sentence)
- [ ] **Scope** (bullet list of deliverables)
- [ ] **Exit criteria** (checkable, not aspirational)
- [ ] **Risks** (load-bearing risks named)
- [ ] **Kill criteria** (per phase, drawn from §8.6)
- [ ] ~200 words per phase

**Phases:**
1. Foundation (wk 1–9): substrate, ingestion, auth, deploy
2. Intelligence (wk 10–18): agents, briefing E2E, approval
3. Cognition Surface (wk 19–28): Galaxy + Topology + Decision
4. Closed Beta Readiness (wk 29–36): hardening, onboarding, support, telemetry

**Acceptance criteria:**
- Phase 3 exit gate is the most fragile and is named explicitly.
- Phase-level kill criteria match §8.6 entries.
- 36 weeks total (matches §8.5 audit).

**Step 1: Draft Phase 1**
**Step 2: Draft Phase 2**
**Step 3: Draft Phase 3**
**Step 4: Draft Phase 4**
**Step 5: Self-review — total weeks = 36**
**Step 6: Commit**

```bash
git add docs/prd.md
git commit -m "docs(prd): write §10 Phased Build Plan (4 phases, 36 weeks)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 11: §11 Future Vision

**Files:**
- Modify: `docs/prd.md` (replace §11)

**Source references:**
- SOURCE-PRD lines 678–688 (current Future Vision)
- SOURCE-PRD lines 1017–1038 (seed-domain Strategic Vision)

**Section content checklist:**
- [ ] ~400 words
- [ ] What MVP unlocks (post-beta features named: simulation engine, agent orchestration UI, Architecture Review workflow, more agents, more visualizations)
- [ ] What 2–3 years out looks like if validation succeeds (org digital twin, more domains, autonomy levels 4–5 with strong governance)
- [ ] What we'll NOT do (no AGI claims, no autonomy-without-governance, no replacement of judgment — anchor to Constitution Principle III)
- [ ] Connect to Constitution Principle VII — broader domains via adapters, not forks

**Acceptance criteria:**
- Aspirational but not magical-thinking.
- Every future capability has a thread back to the conceptual model.
- No new product surfaces invented here that aren't supported by primitives.

**Step 1: Read source materials**
**Step 2: Draft**
**Step 3: Self-review**
**Step 4: Commit**

```bash
git add docs/prd.md
git commit -m "docs(prd): write §11 Future Vision

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 12: §12 Glossary

**Files:**
- Modify: `docs/prd.md` (replace §12)

**Source references:**
- §3.1 (primitives) — these are the core glossary entries
- DESIGN-DOC OQ-B (glossary scope default: core primitives only)

**Section content checklist:**
- [ ] Alphabetical
- [ ] Entry per primitive (15) + a small set of platform-specific terms:
  - Autonomy Level
  - Closed Beta
  - Dogfooding Domain
  - Eval / Evaluation Suite
  - ICP (Ideal Customer Profile)
  - Initiative
  - Workflow Contract
  - World-Class vs Very-Good (visualization tiers)
- [ ] Each entry: 1–2 sentences max
- [ ] Cross-reference primitive entries to §3.1 (full definitions live there)

**Acceptance criteria:**
- Every entity name used in the PRD without prior context is in the glossary.
- No marketing terms or fluff entries.

**Step 1: Walk through the PRD, extract terms readers might not know**
**Step 2: Draft glossary**
**Step 3: Self-review — every PRD term unique to this domain is included**
**Step 4: Commit**

```bash
git add docs/prd.md
git commit -m "docs(prd): write §12 Glossary

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 13: §13 Open Questions Index

**Files:**
- Modify: `docs/prd.md` (replace §13)

**Source references:**
- Every section's Open Questions subsection (already drafted in Tasks 3, 4, 6, 7, 8, 9)
- DESIGN-DOC §5.12 (Open Questions Index pattern)

**Section content checklist:**
- [ ] All OQs aggregated into a single table or list
- [ ] Columns: OQ number, statement, source section, status (open/deferred/resolved — all "open" at this point)
- [ ] Match the 10 OQs from DESIGN-DOC §5.12, plus any added during drafting
- [ ] Renumber if necessary to be sequential (OQ-001 through OQ-NNN)
- [ ] Each OQ also appears verbatim at the bottom of its source section

**Acceptance criteria:**
- Every section-level Open Question appears in the index.
- Every index entry exists in its source section.
- OQ numbering is consistent.

**Step 1: Grep the doc for every "OQ-" occurrence to verify coverage**

```bash
grep -n "OQ-" docs/prd.md
```

**Step 2: Build the index**
**Step 3: Verify two-way consistency (every OQ in index → in section; every OQ in section → in index)**
**Step 4: Commit**

```bash
git add docs/prd.md
git commit -m "docs(prd): write §13 Open Questions Index

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 14: Cross-cutting consistency pass

**Files:**
- Modify: `docs/prd.md` (touch-ups throughout)

**Goal:** the PRD reads as one coherent document, not 13 stitched sections.

**Checks to run:**

**Step 1: Internal cross-references**
- Every "see §X.Y" link points to an actual section/subsection
- No phantom references

```bash
grep -nE "§\d+(\.\d+)?" docs/prd.md
```

**Step 2: Constitution alignment**
- Every constitution principle referenced is named correctly and at the right point
- Architectural Constraints amendments (v1.1.0) reflected accurately in §6.2

```bash
grep -n "Principle" docs/prd.md
grep -n "v1\.[01]" docs/prd.md
```

**Step 3: Term consistency**
- "Initiative Galaxy" (not "initiative galaxy" / "Galaxy view" / etc.)
- "Workflow Topology" (not "workflow topology view")
- "Decision Graph" (not "Decisions Graph" / "ADR graph")
- "Operational Synthesizer" / "Dependency Mapper" (not other casings)
- "MVP" / "closed beta" lowercase
- "Constitution" capitalized when referring to the document

**Step 4: MVP-vs-future cuts agreement**
- §5 module cuts agree with §8 feature surface agree with §10 phase scope
- Check the matrix: every MVP feature in §8.3 has a phase home in §10

**Step 5: Word-count check**
- Section length roughly matches plan estimates
- No section grossly overweight (>1500 words) or underweight (<150 words)

```bash
wc -w docs/prd.md
```

**Step 6: Fix what's broken; commit**

```bash
git add docs/prd.md
git commit -m "docs(prd): cross-cutting consistency pass (references, terms, MVP alignment)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 15: Author review checkpoint (HUMAN GATE)

**Files:** none (read-only review)

**Goal:** Author reads the full PRD end-to-end and signs off, or files revision tasks.

**Step 1: Print the doc and read it**

```bash
wc -l docs/prd.md
# Expected: 800–1500 lines
```

**Step 2: Author reads top-to-bottom in one sitting**

This is a load-bearing review. Look for:
- Did the doc deliver what the design promised?
- Does §1 sell a skeptical reader on the next 12 sections?
- Are MVP cuts honest given solo + closed-beta?
- Do any OQs need to be resolved before the doc ships, or is "open" acceptable?
- Anything missing that a build team would need?

**Step 3: If changes needed:** file revision tasks; iterate against each, commit per fix.

**Step 4: If approved:** record approval

```bash
git tag prd-v1.0-draft
```

---

### Task 16: Relocate to vault and/or finalize source-of-truth

**Files:**
- Possibly modify: `/Users/nick/Vaults/AI Knowledge/AI Knowledge/00-INBOX/context-os.md` (replace with enriched content, or replace with a pointer to `docs/prd.md`)
- Possibly modify: `docs/prd.md` (add canonical-source note in header)

**Decision required from author (DESIGN-DOC OQ-A):**
- (a) Move enriched PRD into the vault inbox, replacing original
- (b) Keep enriched PRD in repo at `docs/prd.md`; archive the vault original as `context-os-v0.md` and add a forwarding pointer
- (c) Keep both — vault PRD is the personal-thinking surface, repo PRD is the build-team surface (with explicit reconciliation policy)

**Recommendation:** (b) — repo as source of truth, vault gets a pointer. Repo is version-controlled and traceable; vault is for capture/ideation.

**Step 1: Get author decision**

**Step 2: Execute the chosen option**

**Step 3: Commit (if repo files touched)**

```bash
git add docs/prd.md  # if header updated
git commit -m "docs(prd): mark canonical source-of-truth location

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

**Step 4: Open PR or merge to main**

```bash
git checkout main
git merge --no-ff feature/prd-rewrite -m "merge: PRD rewrite v1.0"
```

(If using PR flow: `git push -u origin feature/prd-rewrite && gh pr create ...`)

---

## Skills referenced

- `superpowers:executing-plans` — execute this plan task-by-task
- `superpowers:subagent-driven-development` — if execution dispatches one subagent per task
- `superpowers:verification-before-completion` — applies at Task 15 author-review gate

## Estimated total effort

| Task | Effort |
|---|---|
| Task 0 scaffold | 15 min |
| Tasks 1–13 sections (13 tasks) | 6–10 hrs (avg 30–45 min each, §6 and §8 longer) |
| Task 14 consistency | 30–60 min |
| Task 15 author review | 30–60 min |
| Task 16 finalization | 15 min |
| **Total** | **8–13 hours of focused work** |

Realistic over 2–3 working sessions if author reviews each section before moving on, faster if executed via subagents with end-of-batch review.

---

## Plan complete

Saved to `docs/plans/2026-05-17-prd-rewrite-plan.md`. Two execution options:

**1. Subagent-Driven (this session)** — I dispatch a fresh subagent per Task 1–14, review between tasks, commit per task. Fast iteration; you stay in the loop at decision points (Task 15, Task 16).

**2. Parallel Session (separate)** — Open a new session in this repo, invoke `superpowers:executing-plans`, batch execution with checkpoints. Better if you want to fully step away.

**Which approach?**
