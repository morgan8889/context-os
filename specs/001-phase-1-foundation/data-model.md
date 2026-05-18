# Data Model: Phase 1 — Foundation

**Date**: 2026-05-17  
**Branch**: `1-phase-1-foundation`

---

## Core Ontology (AGE Graph Nodes)

All nodes live in an Apache AGE graph named `context_os` and carry the following base properties regardless of type.

### Base Node Properties (all types)

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | string (UUID) | ✅ | Stable identifier across syncs |
| `tenant_id` | string | ✅ | Clerk org ID; all queries filter on this |
| `source` | string | ✅ | `github` \| `jira` \| `slack` \| `internal` |
| `source_id` | string | ✅ | Vendor-assigned ID (PR number, issue key, etc.) |
| `fetch_ts` | string (ISO 8601) | ✅ | Timestamp of last successful ingest |
| `created_at` | string (ISO 8601) | ✅ | First seen in graph |
| `updated_at` | string (ISO 8601) | ✅ | Last updated in graph |

### Node Types

#### Goal
Maps to: Jira Epic, GitHub Milestone

| Property | Type | Description |
|----------|------|-------------|
| `title` | string | Epic/milestone name |
| `description` | string | Summary |
| `status` | string | `open` \| `in_progress` \| `done` \| `cancelled` |
| `due_date` | string (ISO 8601) | nullable |
| `url` | string | Link to source |

#### Initiative
Maps to: Jira Project, GitHub Repository

| Property | Type | Description |
|----------|------|-------------|
| `title` | string | Project/repo name |
| `description` | string | nullable |
| `status` | string | `active` \| `archived` \| `closed` |
| `url` | string | Link to source |

#### Signal
Maps to: Jira issue status change, GitHub PR review event, Slack message

| Property | Type | Description |
|----------|------|-------------|
| `content` | string | Raw signal text / description |
| `signal_type` | string | `status_change` \| `review` \| `message` \| `comment` |
| `sentiment` | string | nullable; populated in Phase 2 |
| `url` | string | nullable; deep link to source event |
| `occurred_at` | string (ISO 8601) | When the event happened |

#### Artifact
Maps to: GitHub PR, merged commit, Jira completed issue

| Property | Type | Description |
|----------|------|-------------|
| `title` | string | PR title, commit message, issue title |
| `content` | string | Body/description for embedding |
| `artifact_type` | string | `pull_request` \| `commit` \| `issue` \| `document` |
| `status` | string | `open` \| `merged` \| `closed` \| `draft` |
| `url` | string | Source link |
| `embedding` | vector(768) | Stored in pgvector (via relational mirror table) |

#### Actor
Maps to: GitHub user, Jira user, Slack user; deduplicated cross-source where email matches.

| Property | Type | Description |
|----------|------|-------------|
| `name` | string | Display name |
| `email` | string | nullable; used for cross-source dedup |
| `identities` | string (JSON array) | `[{"source":"github","id":"gh_user_123"}]` |

#### Memory
Semantic unit of context for retrieval. Created by Phase 2 agents; schema committed in Phase 1.

| Property | Type | Description |
|----------|------|-------------|
| `content` | string | Summarized text or decision rationale |
| `memory_type` | string | `summary` \| `decision` \| `context` |
| `embedding` | vector(768) | Stored in pgvector mirror table |
| `source_span` | string (JSON) | `{"from": ISO, "to": ISO}` — time range covered |

#### Dependency (Edge type, not a node)
Directed edge between any two nodes. Represented as an AGE edge, not a node.

| Property | Type | Description |
|----------|------|-------------|
| `dependency_type` | string | `blocks` \| `references` \| `implements` \| `pending` |
| `source` | string | Source system that declared this dependency |
| `resolved` | bool | `false` for cross-source pending references |

---

## Edge Types (AGE Graph Edges)

| Edge | From → To | Meaning |
|------|-----------|---------|
| `IMPLEMENTS` | Initiative → Goal | Repo/project implements a milestone/epic |
| `PRODUCES` | Initiative → Artifact | Repo/project produced this PR/commit |
| `EMITS` | Initiative → Signal | Project emits a status signal |
| `AUTHORED_BY` | Artifact → Actor | PR/commit authored by this person |
| `REVIEWED_BY` | Artifact → Actor | PR reviewed by this person |
| `AUTHORED_BY` | Signal → Actor | Slack message authored by this person |
| `REFERENCES` | Signal → Artifact | Slack message references a PR (cross-source edge) |
| `DEPENDS_ON` | Any → Any | Generic dependency with `dependency_type` property |
| `SUMMARIZES` | Memory → Any | Memory node covers this entity's time span |

---

## Relational Tables (PostgreSQL / SQLAlchemy)

These tables handle operational state that is not graph-traversal data.

### `tenants`
```sql
CREATE TABLE tenants (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clerk_org_id TEXT UNIQUE NOT NULL,
    name        TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);
```

### `oauth_tokens`
```sql
CREATE TABLE oauth_tokens (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id         UUID NOT NULL REFERENCES tenants(id),
    integration       TEXT NOT NULL,          -- 'jira' | 'github' | 'slack'
    access_token_enc  BYTEA NOT NULL,
    refresh_token_enc BYTEA,
    expires_at        TIMESTAMPTZ,
    scope             TEXT,
    metadata          JSONB,                   -- cloudId, installation_id, etc.
    updated_at        TIMESTAMPTZ DEFAULT now(),
    UNIQUE (tenant_id, integration)
);
```

### `sync_checkpoints`
```sql
CREATE TABLE sync_checkpoints (
    tenant_id    UUID NOT NULL REFERENCES tenants(id),
    integration  TEXT NOT NULL,
    object_type  TEXT NOT NULL,               -- 'issues' | 'prs' | 'messages' | etc.
    cursor_value TEXT,                         -- ISO timestamp, nextPageToken, Slack ts
    updated_at   TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (tenant_id, integration, object_type)
);
```

### `node_embeddings`
Mirrors graph nodes that have embeddings for pgvector retrieval. Owned by the vector module.

```sql
CREATE TABLE node_embeddings (
    id          UUID PRIMARY KEY,             -- same UUID as AGE node id
    tenant_id   UUID NOT NULL REFERENCES tenants(id),
    node_type   TEXT NOT NULL,               -- 'Artifact' | 'Memory'
    content     TEXT NOT NULL,               -- text that was embedded
    embedding   VECTOR(768),
    updated_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ON node_embeddings USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

---

## Source Normalization Map

| Source | Source Object | Normalized Node Type | Key Fields Mapped |
|--------|--------------|---------------------|-------------------|
| GitHub | Repository | Initiative | name → title, description, html_url |
| GitHub | Milestone | Goal | title, description, state, due_on |
| GitHub | Pull Request | Artifact | title, body, state, html_url, merged_at |
| GitHub | Issue | Signal or Artifact | open → Signal, closed → Artifact |
| GitHub | User | Actor | login → name, email |
| GitHub | PR Review | Signal | state, body, submitted_at |
| Jira | Project | Initiative | name → title, description, url |
| Jira | Epic | Goal | summary → title, description, status |
| Jira | Issue (in-progress) | Signal | summary → content, status change → signal_type |
| Jira | Issue (done) | Artifact | summary → title, description, url |
| Jira | User | Actor | displayName → name, emailAddress |
| Slack | Message | Signal | text → content, ts → occurred_at |
| Slack | User | Actor | real_name → name, email |

---

## State Transitions

### Artifact status flow (normalized)
```
draft → open → merged
         └──→ closed
```

### Signal resolution
- Cross-source pending references (`Slack message → GitHub PR`): edge created with `resolved=false` on first Slack ingest; resolved to `resolved=true` on next GitHub ingest cycle that includes the referenced PR.

---

## Validation Rules

- `tenant_id` MUST be present on every node and every query filter — no tenant-agnostic writes
- `source_id` + `source` + `tenant_id` is the deduplication key for MERGE operations
- `embedding` MUST be updated whenever `content` changes (enforced in vector module update path)
- Actors with matching `email` across sources MUST be merged into a single node with updated `identities` array
- `pending` Dependency edges MUST carry `resolved=false`; resolved edges update `resolved=true` and retain original creation provenance
