# Feature Specification: Phase 1 — Foundation

**Feature Branch**: `1-phase-1-foundation`
**Created**: 2026-05-17
**Status**: Draft
**Source**: docs/prd.md §10 Phase 1 scope; constitution v1.1.0

---

## User Scenarios & Testing

### User Story 1 — Ingest and inspect real org data (Priority: P1)

The author connects their Jira, GitHub, and Slack accounts and runs a full
ingest. Normalized entities appear in a local admin view — Initiatives, Goals,
Signals, Artifacts, Actors — with provenance showing which source system each
came from.

**Why this priority**: This is the exit criterion for Phase 1 and the
prerequisite for every subsequent phase. Nothing else is testable without real
data in the graph.

**Independent Test**: Configure one OAuth token (GitHub), run ingest, open
admin UI, confirm at least one Artifact and one Actor node appear in the graph
with correct ontology type labels.

**Acceptance Scenarios**:

1. **Given** a valid GitHub OAuth token is configured, **When** the author runs
   `ingest github`, **Then** repositories, pull requests, and issues are
   normalized to `Artifact` / `Initiative` / `Signal` nodes in the memory
   graph with `source: github` provenance.
2. **Given** a valid Jira OAuth token is configured, **When** the author runs
   `ingest jira`, **Then** projects, epics, and issues are normalized to
   `Goal` / `Initiative` / `Signal` nodes with `source: jira` provenance.
3. **Given** a valid Slack OAuth token is configured, **When** the author runs
   `ingest slack`, **Then** messages in configured channels are normalized to
   `Signal` nodes with author mapped to an `Actor` node.
4. **Given** a prior ingest has run, **When** the author runs ingest again,
   **Then** only new or changed items are fetched (incremental sync) and
   existing nodes are updated, not duplicated.
5. **Given** ingestion completes, **When** the author opens the admin UI,
   **Then** all normalized entities are visible with their ontology type,
   source, and provenance.

---

### User Story 2 — Query the memory graph (Priority: P2)

The author issues graph queries against ingested data — traversing edges,
filtering by type, and retrieving semantically similar items — and receives
correct results within the performance budget.

**Why this priority**: Validates the three persistence module interfaces
(relational, graph, vector) before Phase 2 agents depend on them.

**Independent Test**: After ingesting GitHub data, run a 1-hop graph traversal
from a known repository node, a k-hop traversal finding transitive
dependencies, and a vector similarity search for a known phrase; all three
must return non-empty, correct results.

**Acceptance Scenarios**:

1. **Given** ingested data exists, **When** a 1-hop graph query is executed
   from any node, **Then** correct adjacent nodes and edge types are returned
   within the performance budget.
2. **Given** ingested data exists, **When** a k-hop traversal with edge
   filtering is executed, **Then** the result set contains only nodes
   reachable via the specified edge type within k hops, within budget.
3. **Given** `Memory` and `Artifact` nodes with text content exist, **When** a
   vector similarity search is issued for a representative phrase, **Then**
   the top-k results contain the expected semantically relevant nodes.
4. **Given** a query is issued, **When** a database or network error occurs,
   **Then** the caller receives a structured error response, not an
   unhandled exception.

---

### User Story 3 — Multi-tenant auth with tenant isolation (Priority: P3)

The author creates two stub tenants via Clerk and confirms that each tenant's
data is invisible to the other at the query layer.

**Why this priority**: Tenant isolation is a load-bearing pre-condition for
closed-beta; must be verified before any org data is ingested on the platform.

**Independent Test**: Create tenant A and tenant B, ingest data under tenant A,
query as tenant B, confirm zero results and no cross-tenant leakage in query
logs.

**Acceptance Scenarios**:

1. **Given** two tenants exist, **When** the author authenticates as tenant A
   and queries the graph, **Then** only tenant A's data is returned.
2. **Given** two tenants exist, **When** tenant B performs the identical query
   as tenant A, **Then** tenant B receives only their own data (empty if none
   ingested).
3. **Given** an unauthenticated request, **When** any data endpoint is called,
   **Then** the request is rejected with an authentication error before any
   data access occurs.

---

### User Story 4 — Observable operations baseline (Priority: P4)

Every ingest run, graph query, and vector retrieval emits structured traces and
logs captured by the local observability stack and visible in the Langfuse UI.

**Why this priority**: Constitution Principle VI (Observable Autonomy) is
non-negotiable. Traces must exist from day one so Phase 2 agent work has an
observable substrate from the start.

**Independent Test**: Run one ingest, open Langfuse locally, confirm at least
one trace appears with agent identity, operation name, input summary, latency,
and no governance-marker fields missing.

**Acceptance Scenarios**:

1. **Given** an ingest run completes, **When** the author opens the Langfuse
   UI, **Then** a trace entry exists with source, duration, record count, and
   tenant ID.
2. **Given** a graph query executes, **When** observability logs are inspected,
   **Then** a structured log entry exists with operation, node count, latency,
   and tenant ID.
3. **Given** any operation emits a trace, **Then** the trace includes: agent
   identity, autonomy level, input summary, output summary, latency, and
   governance markers.

---

### Edge Cases

- What happens when an OAuth token expires mid-ingest? Ingest halts
  gracefully, records its checkpoint, and reports a structured error
  indicating token refresh is required. Partial results already persisted
  are retained.
- What happens when a source API rate-limits the ingest? The pipeline backs
  off with exponential retry, respects `Retry-After` headers, and resumes
  from the last checkpoint without duplicating already-persisted nodes.
- What happens when a Slack message references a GitHub PR not yet ingested?
  The cross-source edge is recorded as a pending reference and resolved on
  the next ingest cycle covering the referenced source.
- What happens when AGE graph query latency exceeds 500ms p95 on a
  representative workload? The AGE sunset trigger fires: fall back to plain
  Postgres adjacency tables (+2 weeks), per constitution v1.1.0.
- What happens when the local Postgres instance is unavailable at startup?
  The application exits with a clear structured error identifying the missing
  dependency and the required connection string.

---

## Requirements

### Functional Requirements

**Memory graph**

- **FR-001**: The system MUST provide three logically distinct module
  interfaces: relational, graph traversal, and vector similarity — each
  independently addressable so the underlying store can be split to a
  dedicated backend without a rewrite.
- **FR-002**: The graph module MUST support 1-hop and k-hop traversal with
  edge type filtering on ingested data.
- **FR-003**: The vector module MUST support top-k semantic retrieval over
  `Memory` and `Artifact` node content.
- **FR-004**: All three interfaces MUST return structured error responses on
  failure; unhandled exceptions MUST NOT surface to callers.

**Ingestion**

- **FR-005**: The system MUST authenticate with Jira, GitHub, and Slack via
  OAuth and store credentials securely per tenant.
- **FR-006**: Each ingestion source MUST normalize fetched data to core
  ontology types (Goal, Initiative, Signal, Artifact, Actor, Memory,
  Dependency) before persistence; raw vendor schemas MUST NOT leak into core
  graph queries.
- **FR-007**: Each ingestion run MUST be incremental: only new or changed items
  since the last successful checkpoint are fetched and processed.
- **FR-008**: Ingestion MUST record provenance on every node: source system,
  source ID, fetch timestamp, and tenant ID.
- **FR-009**: On OAuth token expiry or API rate-limit, ingestion MUST halt
  gracefully, persist its checkpoint, and report a structured error.
- **FR-010**: Cross-source references (e.g., a Slack message linking a GitHub
  PR) MUST be recorded as pending edges and resolved on a subsequent ingest
  cycle.

**Auth and multi-tenancy**

- **FR-011**: The system MUST integrate with Clerk for authentication; all API
  endpoints MUST reject unauthenticated requests before any data access.
- **FR-012**: All data reads and writes MUST be scoped to the authenticated
  tenant; cross-tenant access MUST be architecturally prevented at the query
  layer, not only by policy.
- **FR-013**: The system MUST support at least two concurrent tenants for
  isolation testing.

**Observability**

- **FR-014**: Every ingest run, graph query, and vector retrieval MUST emit an
  OpenTelemetry-compatible trace containing: agent identity, autonomy level,
  input summary, output summary, latency, tenant ID, and governance markers.
- **FR-015**: Traces MUST be captured by a local Langfuse instance and
  accessible via its UI.
- **FR-016**: Structured log shape MUST be committed (fields defined and
  documented) before Phase 1 exits, so Phase 2 telemetry can extend it
  without breaking existing consumers.

**Admin UI**

- **FR-017**: The system MUST provide a local admin view listing all normalized
  entities in the graph with their ontology type, source, and provenance after
  an ingest run.
- **FR-018**: The admin UI MUST be sufficient for the author to verify
  normalization correctness without requiring direct database access.

### Key Entities

- **Goal**: Desired outcome; maps to Jira Epics, GitHub Milestones.
- **Initiative**: Body of work traceable to a Goal; maps to Jira Projects,
  GitHub Repositories.
- **Signal**: Event or observation from a source; maps to Jira issue status
  changes, Slack messages, GitHub PR reviews.
- **Artifact**: Produced output; maps to GitHub PRs, merged commits, Jira
  completed issues.
- **Actor**: Human or system participant; deduplicated cross-source where
  identity can be inferred.
- **Memory**: Semantic unit of context stored for retrieval; includes
  summarized thread content and decision rationale.
- **Dependency**: Directed edge between any two nodes indicating a dependency
  or cross-reference relationship.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: The author can run a full three-source ingest (Jira + GitHub +
  Slack) against their own org and see normalized entities in the admin UI
  within 15 minutes of providing OAuth tokens.
- **SC-002**: A repeat ingest run on unchanged data produces zero duplicate
  nodes and reflects only changes since the prior run.
- **SC-003**: 1-hop and k-hop graph traversal queries return correct results
  within the performance budget (p95 ≤ 500ms) on real ingested data.
- **SC-004**: Vector similarity retrieval returns at least one semantically
  relevant result in the top-3 for five representative natural-language
  queries against real ingested data.
- **SC-005**: Two stub tenants show zero cross-tenant data visibility across
  all three query interfaces, verified by direct query comparison.
- **SC-006**: Every operation produces an observable trace in the local
  Langfuse UI within 30 seconds of the operation completing.
- **SC-007**: Ingestion handles OAuth token expiry and API rate-limits without
  data loss or unhandled exceptions, verified by injected fault tests.

---

## Assumptions

- **A-001**: The author has valid OAuth credentials for at least one Jira Cloud
  workspace, one GitHub organization, and one Slack workspace.
- **A-002**: PostgreSQL with pgvector and Apache AGE extensions is available
  locally via Docker Compose; no cloud database is required for Phase 1.
- **A-003**: Clerk runs in development mode (test keys); no production Clerk
  tenant is required.
- **A-004**: Performance budget for graph queries: p95 ≤ 500ms on a
  representative local dataset, per constitution v1.1.0 AGE sunset trigger.
- **A-005**: Top-k for vector retrieval defaults to k=5 unless a query
  specifies otherwise.
- **A-006**: The admin UI is a minimal read-only view; no design polish
  required in Phase 1.
- **A-007**: Langfuse runs locally via Docker Compose; no Langfuse cloud
  account required.
- **A-008**: Incremental sync uses cursor-based pagination on each source's
  `updated_since` parameter; full re-ingest is available as a manual override.

---

## Dependencies and Out of Scope

### Dependencies

- PostgreSQL + pgvector + Apache AGE (local Docker Compose)
- Clerk (auth, development keys)
- Langfuse (local Docker Compose)
- Jira Cloud API, GitHub REST/GraphQL API, Slack API (OAuth apps
  pre-registered by the author)

### Out of Scope for Phase 1

- Cloud deployment (Fly.io, Railway, Vercel) — Phase 3/4
- Any AI agent or LLM-based workflow — Phase 2
- Executive Briefing or any user-facing workflow — Phase 2
- Galaxy visualization layer — Phase 3
- Production Clerk tenant or real user management — Phase 3
- More than three ingestion sources — Phase 2+
- New-user activation / onboarding flow — Phase 4
