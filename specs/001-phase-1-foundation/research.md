# Research: Phase 1 — Foundation

**Date**: 2026-05-17  
**Branch**: `1-phase-1-foundation`  
**Status**: Complete — all NEEDS CLARIFICATION resolved

---

## Apache AGE Python Integration

**Decision**: Direct asyncpg SQL with a thin in-house AGType deserializer. No maintained async AGE client library exists.

**Rationale**: `apache-age-python` is psycopg2-only and synchronous. asyncpg is the standard FastAPI driver and measurably faster. The workaround is straightforward: disable prepared statement caching and run LOAD/search_path setup once per connection via pool `init` hook.

**Key implementation points**:
- `asyncpg.create_pool(statement_cache_size=0, init=_age_setup)` where `_age_setup` executes `LOAD 'age'` and `SET search_path = ag_catalog, "$user", public`
- Cypher queries via `SELECT * FROM cypher(graph_name, $$ ... $$) AS (col agtype)`
- No asyncpg bind params inside Cypher string — use AGE parameter map (`parameters agtype` arg) for user-supplied values to prevent injection
- Upsert via `MERGE ... ON CREATE SET ... ON MATCH SET ...` with provenance as node/edge properties
- PG16 + AGE 1.5 is stable; most common error (`AgeNotSet`) is always a missing `LOAD 'age'` or `search_path` — prevented by the `init` hook

**Alternatives considered**: psycopg3 (native async but 1.5–3x slower); apache-age-python (rejected: psycopg2-only).

---

## pgvector + Async Python

**Decision**: `pgvector` package + `asyncpg` via SQLAlchemy 2.0 async engine, HNSW index, `all-mpnet-base-v2` embedding model.

**Rationale**:
- `pgvector` ships `pgvector.sqlalchemy.Vector` ORM type and `pgvector.asyncpg.register_vector` codec; register via `engine.sync_engine` connect event
- HNSW chosen over IVFFlat: 95–99% recall without centroid tuning, handles incremental writes without `REINDEX`, acceptable memory trade-off for <1M vectors
- `all-mpnet-base-v2` (768d, 110M params, MTEB ~57): better polysemy handling for technical jargon than MiniLM; CPU batch throughput ~100–200 sent/s is fine for ingest workloads
- Cosine similarity via `.cosine_distance()` method (maps to `<=>` operator), ordered ascending

**Key implementation points**:
```python
mapped_column(Vector(768))  # ORM column
CREATE INDEX USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64)
stmt = select(Node).order_by(Node.embedding.cosine_distance(query_vec)).limit(k)
```

**Alternatives considered**: IVFFlat (rejected: recall degrades without REINDEX); `all-MiniLM-L6-v2` (fallback if CPU latency is a problem — 384d, 5x faster but slightly lower quality).

---

## OAuth Integration Patterns

### Jira Cloud
**Decision**: OAuth 2.0 3LO (authorization code) for interactive setup; `updated >= "YYYY-MM-DD HH:mm"` JQL filter for incremental sync with nextPageToken pagination.

- After token exchange, call `GET https://api.atlassian.com/oauth/token/accessible-resources` to retrieve `cloudId` — cache per tenant
- Pagination: `nextPageToken` (current API) — paginate until response shorter than `maxResults`
- Checkpoint: high-water-mark timestamp per `(tenant_id, 'jira', object_type)`

### GitHub
**Decision**: GitHub App (not OAuth App) — installation access tokens, fine-grained permissions, 15K req/hr rate limit, not tied to individual user.

- Pagination: `Link: rel="next"` header; default page 30, max 100
- Incremental sync: `since` ISO 8601 filter on `updated_at` for issues/PRs; still paginate with `Link` headers within the filtered window

### Slack
**Decision**: Bot token (`xoxb-`) with `channels:history` scope — not tied to individual user.

- Pagination: `conversations.history` with `cursor=response_metadata.next_cursor`; `oldest` param as Unix timestamp
- Incremental sync: store `ts` of newest message as next `oldest` cursor

### Token Storage
**Decision**: Application-layer AES-256 encryption (Python `cryptography` Fernet) before storing in Postgres `oauth_tokens` table. Key stored in environment secret.

Schema: `(tenant_id, integration, access_token_enc, refresh_token_enc, expires_at, metadata JSONB)` — UNIQUE on `(tenant_id, integration)`.

### Checkpoint Pattern
**Decision**: Postgres `sync_checkpoints` table, keyed `(tenant_id, integration, object_type)`. Update checkpoint only after successful DB commit.

```sql
CREATE TABLE sync_checkpoints (
    tenant_id    UUID NOT NULL,
    integration  TEXT NOT NULL,
    object_type  TEXT NOT NULL,
    cursor_value TEXT,
    updated_at   TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (tenant_id, integration, object_type)
);
```

---

## Clerk + FastAPI Multi-Tenant Auth

**Decision**: `clerk-backend-api` SDK for `authenticate_request()`; application-level query filters for tenant isolation (dev); JWT org claim `o.id` for tenant ID.

**Key points**:
- Install: `clerk-backend-api PyJWT cryptography`
- JWT verification: `clerk.authenticate_request(request, AuthenticateRequestOptions(...))` — handles JWKS fetch (RS256) and caching automatically
- Tenant ID from JWT: `payload.get("o", {}).get("id")` — Clerk v2 nests org data under `o` claim (top-level `org_id` deprecated April 2025)
- FastAPI pattern: `Depends(get_current_tenant)` dependency, not middleware — composable and testable
- Tenant scoping: add `tenant_id` column to all shared tables; filter on it in every query (dev); path to RLS for production hardening

**Alternatives considered**: `fastapi-clerk-middleware` (extra dependency layer); PostgreSQL RLS for dev (overkill for 2 stub tenants).

---

## Langfuse + OpenTelemetry Wiring

**Decision**: Langfuse Python SDK v3 (`LangfuseSpanProcessor`) added to a shared `TracerProvider`; `context_os.*` attribute namespace for governance markers.

**Rationale**: SDK v3 is OTEL-native — installs as a `SpanProcessor`, no custom exporter code needed. Keeping OTEL as the canonical backbone (with Langfuse as one consumer) is the right architecture for an AI platform that will add more telemetry consumers in Phase 2.

**Key implementation points**:
```python
provider = TracerProvider(resource=Resource({SERVICE_NAME: "context-os"}))
provider.add_span_processor(LangfuseSpanProcessor())  # Langfuse consumer
trace.set_tracer_provider(provider)
FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
```

**Governance span attributes**:
- Standard: `gen_ai.system`, `gen_ai.operation.name`
- Custom: `context_os.agent_identity`, `context_os.autonomy_level`, `context_os.tenant_id`, `context_os.input_summary`, `context_os.output_summary`, `context_os.governance_markers`

**Langfuse Docker Compose**: Clone langfuse repo, copy `.env.example`, `docker compose up -d`. UI on port 3000; OTLP HTTP on `http://localhost:3000/api/public/otel`. Required env: `SALT`, `NEXTAUTH_SECRET`, `NEXTAUTH_URL`, `DATABASE_URL`, `LANGFUSE_INIT_*` seed vars.

**Structured log schema**: Committed at Phase 1 exit (see `contracts/telemetry.md`). Extension contract: Phase 2 adds fields inside `metadata` or as new top-level keys; MUST NOT rename or retype required fields; consumers MUST tolerate unknown keys.

**Alternatives considered**: Raw `OTLPSpanExporter` to Langfuse (more setup, no benefit over SDK v3); Langfuse-only (no OTEL backbone, violates constitution Principle VI).
