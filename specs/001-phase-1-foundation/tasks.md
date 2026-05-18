# Tasks: Phase 1 — Foundation

**Input**: `specs/001-phase-1-foundation/` (plan.md, spec.md, data-model.md, research.md, contracts/)
**Branch**: `1-phase-1-foundation`
**Generated**: 2026-05-18

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Parallelizable — different files, no dependencies on incomplete sibling tasks
- **[US#]**: User story label (US1=ingest, US2=query, US3=auth, US4=observability)
- All paths are relative to repository root

---

## Phase 1: Setup

**Purpose**: Project skeleton, infra config, and tooling — no user story code yet.

- [x] T001 Create full project directory skeleton: pyproject.toml with all runtime deps (fastapi>=0.115, sqlalchemy[asyncio]>=2.0, asyncpg, apache-age, pgvector, clerk-backend-api, langfuse>=3, opentelemetry-sdk, opentelemetry-exporter-otlp, opentelemetry-instrumentation-fastapi, cryptography, pydantic>=2, pydantic-settings, alembic, sentence-transformers, httpx, typer) and dev deps (pytest, anyio[asyncio], pytest-httpx, ruff, pyright); create all `__init__.py` stubs for src/context_os/{core,db,graph,vector,relational,ingestion,ingestion/github,ingestion/jira,ingestion/slack,auth,observability,api}/
- [x] T002 [P] Create Docker Compose infrastructure in docker/docker-compose.yml (postgres:16 service with pgvector+AGE extensions, port 5432; langfuse service with OTLP HTTP on port 3000, env seeded with SALT/NEXTAUTH_SECRET/NEXTAUTH_URL/DATABASE_URL/LANGFUSE_INIT_* vars) and docker/postgres/init.sql (CREATE EXTENSION IF NOT EXISTS vector; LOAD 'age'; CREATE EXTENSION IF NOT EXISTS age; SET search_path = ag_catalog, "$user", public)
- [x] T003 [P] Create .env.example with all variables per quickstart.md: DATABASE_URL, CLERK_SECRET_KEY, CLERK_PUBLISHABLE_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST, ENCRYPTION_KEY, GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY_PATH, GITHUB_INSTALLATION_ID, JIRA_CLIENT_ID, JIRA_CLIENT_SECRET, SLACK_BOT_TOKEN, SLACK_CHANNEL_IDS; each with inline comment describing how to obtain it
- [x] T004 [P] Create src/context_os/config.py (Pydantic BaseSettings subclass loading all env variables with type annotations; fail fast with clear error on missing required vars; export a cached `get_settings()` function; include DATABASE_URL, CLERK_SECRET_KEY, LANGFUSE_*, ENCRYPTION_KEY, GITHUB_*, JIRA_*, SLACK_*)
- [x] T005 [P] Configure ruff (pyproject.toml [tool.ruff]: line-length=88, select=["E","W","F","I","UP"], target-version="py312") and pyright ([tool.pyright]: pythonVersion="3.12", typeCheckingMode="strict", exclude=["docker"]); add pytest config ([tool.pytest.ini_options]: asyncio_mode="auto", testpaths=["tests"])

**Checkpoint**: `uv sync` installs all deps; `docker compose -f docker/docker-compose.yml up -d` starts infra; `cp .env.example .env` gives a working template.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core domain types, DB layer, graph client, auth skeleton, observability init — MUST complete before any user story.

⚠️ **CRITICAL**: No user story work can begin until this phase is complete.

- [x] T006 [P] Create src/context_os/core/ontology.py: `NodeType` StrEnum (Goal, Initiative, Signal, Artifact, Actor, Memory); `EdgeType` StrEnum (IMPLEMENTS, PRODUCES, EMITS, AUTHORED_BY, REVIEWED_BY, REFERENCES, DEPENDS_ON, SUMMARIZES); `Source` StrEnum (github, jira, slack, internal); `BaseNodeSchema` Pydantic model with fields: id (UUID), tenant_id (str), source (Source), source_id (str), fetch_ts (datetime), created_at (datetime), updated_at (datetime)
- [x] T007 [P] Create src/context_os/core/errors.py: `ContextOSError` base (code: str, message: str, trace_id: str | None = None); subclasses: `AuthError`, `TenantIsolationError`, `TokenExpiredError`, `RateLimitError` (retry_after: int), `CheckpointError`, `GraphQueryError`, `VectorSearchError`, `ValidationError`; all serializable to dict for API error responses
- [x] T008 Create src/context_os/db/engine.py: SQLAlchemy 2.0 `create_async_engine` using asyncpg driver and DATABASE_URL from config; `async_session_factory` via `AsyncSession(engine)`; `init_db()` / `close_db()` async functions for lifespan; register pgvector asyncpg codec via `sync_engine` `connect` event using `register_vector`
- [x] T009 Create src/context_os/db/models.py: SQLAlchemy ORM declarative models — `Tenant` (id UUID PK, clerk_org_id TEXT UNIQUE, name TEXT, created_at); `OAuthToken` (id UUID PK, tenant_id FK→Tenant, integration TEXT, access_token_enc BYTEA, refresh_token_enc BYTEA, expires_at, scope TEXT, metadata JSONB, updated_at; UNIQUE on tenant_id+integration); `SyncCheckpoint` (tenant_id FK, integration TEXT, object_type TEXT, cursor_value TEXT, updated_at; PK on all three); `NodeEmbedding` (id UUID PK, tenant_id FK, node_type TEXT, content TEXT, embedding Vector(768), updated_at)
- [x] T010 Set up Alembic in src/context_os/db/migrations/: alembic.ini pointing to DATABASE_URL from env; env.py configured for async with asyncpg using `run_async_migrations()`; generate initial migration creating all four tables (tenants, oauth_tokens, sync_checkpoints, node_embeddings) with correct FK constraints and the HNSW index: `CREATE INDEX ON node_embeddings USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64)`
- [x] T011 Create src/context_os/relational/repositories.py: `TenantRepository` (create, get_by_clerk_org_id — all queries require tenant scope); `OAuthTokenRepository` (upsert with Fernet AES-256 encrypt/decrypt using ENCRYPTION_KEY from config, get_for_tenant_integration — returns decrypted token); `CheckpointRepository` (get by tenant+integration+object_type, upsert — checkpoint only updated after successful outer commit)
- [x] T012 Create src/context_os/graph/client.py: `create_age_pool()` returning an asyncpg pool with `statement_cache_size=0` and `init` hook that executes `LOAD 'age'` and `SET search_path = ag_catalog, "$user", public` on each connection; `init_graph(pool, graph_name="context_os")` that runs `SELECT create_graph('context_os')` if not exists; `run_cypher(pool, cypher, params=None)` helper that wraps query in `SELECT * FROM cypher('context_os', $$ ... $$, $params) AS (r agtype)` using AGE parameter map for user values (never f-string injection into Cypher string)
- [x] T013 Create src/context_os/graph/mutations.py: `upsert_node(pool, tenant_id, node_type, props: dict) → str` using AGE MERGE on `(id, tenant_id)` ON CREATE SET all props ON MATCH SET updated_at + fetch_ts; `upsert_edge(pool, tenant_id, from_id, to_id, edge_type, props: dict)` using MERGE on matching from/to node ids; `upsert_pending_edge(pool, tenant_id, from_id, to_source_id, to_source, dependency_type)` creates DEPENDS_ON edge with `resolved=false`; all operations enforce tenant_id as mandatory property
- [x] T014 Create src/context_os/observability/tracer.py: `init_tracer(app_version)` sets up `TracerProvider` with `Resource({SERVICE_NAME: "context-os", SERVICE_VERSION: app_version})`; adds `LangfuseSpanProcessor()` from Langfuse v3 SDK; calls `trace.set_tracer_provider(provider)`; exports `get_tracer(name: str) → Tracer` helper; `instrument_app(app: FastAPI)` calls `FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)`
- [x] T015 [P] Create src/context_os/observability/schema.py: `StructuredLogRecord` dataclass with all v1.0.0 fields (timestamp, level, service, version, trace_id, span_id, event, message, agent_identity, autonomy_level, tenant_id, duration_ms, metadata: dict); `emit_structured_log(record: StructuredLogRecord)` that serializes to JSON and writes to stdout; `EVENT` constants for all Phase 1 events (INGEST_RUN_STARTED, INGEST_RUN_COMPLETED, INGEST_RUN_CHECKPOINT_SAVED, INGEST_RUN_FAILED, INGEST_SOURCE_RATE_LIMITED, INGEST_SOURCE_TOKEN_EXPIRED, GRAPH_TRAVERSE_EXECUTED, GRAPH_TRAVERSE_ERROR, VECTOR_SEARCH_EXECUTED, VECTOR_SEARCH_ERROR, AUTH_REQUEST_REJECTED)
- [x] T016 Create src/context_os/auth/middleware.py: `verify_clerk_jwt(token: str) → dict` using `clerk-backend-api` `authenticate_request()` with CLERK_SECRET_KEY from config; extract `tenant_id = payload["o"]["id"]` (Clerk v2 JWT org claim; NOT `org_id`); raise `AuthError` on invalid/expired token or missing org claim; create src/context_os/auth/dependencies.py: `get_current_tenant` FastAPI dependency using `Depends` pattern that calls verify_clerk_jwt, looks up Tenant row in DB, and returns `TenantContext(tenant_id: str, db_tenant_id: UUID)`
- [x] T017 Create src/context_os/main.py: FastAPI app with `lifespan` context manager that calls `init_db()`, `create_age_pool()`, `init_graph(pool)`, `init_tracer(version)`, `instrument_app(app)` on startup and disposes all on shutdown; include routers from api/ingest.py, api/graph.py, api/vector.py, api/admin.py with `/` prefix; global `exception_handler` for `ContextOSError` that returns JSON `{code, message, trace_id}` with appropriate HTTP status (AuthError→401, ValidationError→400, others→500)
- [x] T018 Create src/context_os/cli.py: Typer app with commands: `graph init` (connect pool, call init_graph); `tenant create --clerk-org-id TEXT --name TEXT` (upsert via TenantRepository, print tenant UUID); `auth github --tenant-id UUID` (generate GitHub App installation token, store encrypted via OAuthTokenRepository); `auth jira --tenant-id UUID` (OAuth 2.0 3LO flow — print auth URL, wait for code, exchange for token, fetch cloudId, store); `auth slack --tenant-id UUID --token TEXT` (store bot token); `ingest github|jira|slack|all --tenant-id UUID [--full]` (invoke appropriate adapter)

**Checkpoint**: `uv run alembic upgrade head` succeeds; `uv run python -m context_os.cli graph init` creates the AGE graph; FastAPI app starts and returns 401 on all endpoints (auth middleware working).

---

## Phase 3: User Story 1 — Ingest and Inspect Real Org Data (Priority: P1) 🎯 MVP

**Goal**: Connect three OAuth sources, run incremental ingest, verify normalized entities in the admin UI with correct ontology types and provenance.

**Independent Test**: Configure one GitHub OAuth token → `cli ingest github --tenant-id <uuid>` → `GET /admin/entities` with valid JWT → assert at least one `Artifact` node with `source: github` and non-null `provenance.source_id` appears.

- [x] T019 [US1] Create src/context_os/ingestion/base.py: abstract `IngestAdapter` with: `run(tenant_id: str) → IngestResult`; internal `_fetch_page(cursor)` and `_normalize(raw) → list[BaseNodeSchema]`; `_load_checkpoint(tenant_id)` and `_save_checkpoint(tenant_id, cursor)` via CheckpointRepository (checkpoint saved only after successful graph commit); `_handle_rate_limit(retry_after: int)` exponential backoff respecting Retry-After header; `_handle_token_expired()` raising `TokenExpiredError` with checkpoint preserved; `IngestResult` dataclass (integration, records_fetched, nodes_created, nodes_updated, edges_created, checkpoint_cursor, error: str | None)
- [x] T020 [P] [US1] Create src/context_os/ingestion/github/client.py: `GitHubClient` using App installation access token (JWT signed with GITHUB_APP_PRIVATE_KEY_PATH + GITHUB_APP_ID, exchanged for installation token via `POST /app/installations/{id}/access_tokens`); methods: `list_repos(since: datetime | None)`, `list_milestones(repo, since)`, `list_pulls(repo, since)`, `list_issues(repo, since)`, `list_pull_reviews(repo, pull_number)`, `get_user(login)`; all paginate via `Link: rel="next"` header (max page=100); 401 → raise `TokenExpiredError`; 429 → raise `RateLimitError(retry_after=int(headers["Retry-After"]))`
- [x] T021 [P] [US1] Create src/context_os/ingestion/github/normalizer.py: `GitHubNormalizer` with per-type methods: `repo_to_initiative(repo, tenant_id)` → Initiative node dict (name→title, description, html_url, status from archived); `milestone_to_goal(milestone, tenant_id)` → Goal dict (title, description, state→status, due_on→due_date, html_url); `pr_to_artifact(pr, tenant_id)` → Artifact dict (title, body→content, artifact_type="pull_request", state/merged_at→status, html_url); `issue_to_signal_or_artifact(issue, tenant_id)` → Signal if open, Artifact if closed; `user_to_actor(user, tenant_id)` → Actor dict (login→name, email, identities JSON); `review_to_signal(review, tenant_id)` → Signal (state+body→content, signal_type="review", submitted_at→occurred_at)
- [x] T022 [P] [US1] Create src/context_os/ingestion/jira/client.py: `JiraClient` using OAuth 2.0 token from OAuthTokenRepository; fetch cloudId from `https://api.atlassian.com/oauth/token/accessible-resources` on first call and cache in metadata; methods: `list_projects(since)`, `list_epics(since)`, `search_issues(jql, cursor)` using `GET /rest/agile/1.0/issue/search` with `updated >= "cursor"` JQL and nextPageToken pagination; `get_user(accountId)`; 401 → `TokenExpiredError`; 429 → `RateLimitError`
- [x] T023 [P] [US1] Create src/context_os/ingestion/jira/normalizer.py: `JiraNomalizer` with: `project_to_initiative(project, tenant_id)` → Initiative (name→title, description, self→url); `epic_to_goal(epic, tenant_id)` → Goal (summary→title, description, status→status); `issue_to_signal_or_artifact(issue, tenant_id)` → Signal if status not Done, Artifact if Done (summary→title/content, status_change→signal_type="status_change"); `user_to_actor(user, tenant_id)` → Actor (displayName→name, emailAddress→email)
- [x] T024 [P] [US1] Create src/context_os/ingestion/slack/client.py: `SlackClient` using bot token (xoxb-) from OAuthTokenRepository; `list_messages(channel_id, oldest: str | None)` using `conversations.history` with `cursor=next_cursor` and `oldest` param for incremental sync (store newest message `ts` as next oldest); `get_user(user_id)` via `users.info`; pagination via `response_metadata.next_cursor`; 401/invalid_auth → `TokenExpiredError`; rate_limited → `RateLimitError(retry_after=int(headers.get("Retry-After", 1)))`
- [x] T025 [P] [US1] Create src/context_os/ingestion/slack/normalizer.py: `SlackNormalizer` with: `message_to_signal(msg, tenant_id)` → Signal (text→content, signal_type="message", ts→occurred_at ISO); `user_to_actor(user, tenant_id)` → Actor (real_name→name, email); `extract_github_pr_refs(text: str) → list[str]` regex for `github.com/.*/pull/\d+` patterns; if refs found, record a pending REFERENCES edge via `upsert_pending_edge` with `resolved=false`
- [x] T026 [P] [US1] Create src/context_os/vector/embeddings.py: `EmbeddingModel` class wrapping `sentence_transformers.SentenceTransformer("all-mpnet-base-v2")`; lazy singleton init (model loaded on first call, not import); `encode(text: str) → list[float]` (768-dim, normalized); `encode_batch(texts: list[str]) → list[list[float]]` with batch_size=32; model runs CPU-only; module-level `get_embedding_model()` factory
- [x] T027 [US1] Implement POST /ingest/{integration} and GET /ingest/{integration}/status endpoints in src/context_os/api/ingest.py per contracts/api.yaml: instantiate adapter from integration name; load OAuth token via OAuthTokenRepository (404 if not configured); call `adapter.run(tenant_id)` → for each normalized node call `upsert_node()` from graph/mutations.py; for Artifact/Memory nodes additionally encode content via embeddings.py and upsert to node_embeddings table; persist checkpoint only after all DB commits succeed; return 202 IngestStatus; on TokenExpiredError return 422 with structured error; GET /status reads last SyncCheckpoint row; all routes require `Depends(get_current_tenant)`
- [x] T028 [P] [US1] Implement GET /admin/entities endpoint in src/context_os/api/admin.py per contracts/api.yaml: query AGE graph with `MATCH (n) WHERE n.tenant_id = $tenant_id` plus optional type/source property filters; paginate with SKIP/LIMIT; map AGE agtype result to `GraphNode` response schema (id, type, tenant_id, provenance: {source, source_id, fetch_ts}, properties); return `{items, total, limit, offset}`; requires `Depends(get_current_tenant)`

**Checkpoint**: `cli ingest github` completes and saves checkpoint; `GET /admin/entities` returns ≥1 node with correct type and provenance; running ingest again produces zero new duplicates.

---

## Phase 4: User Story 2 — Query the Memory Graph (Priority: P2)

**Goal**: Issue 1-hop and k-hop graph traversals and vector similarity searches against ingested data with correct results within performance budgets.

**Independent Test**: After GitHub ingest — run `POST /graph/traverse` from a known Initiative node with max_hops=2 (assert non-empty nodes+edges, query_ms ≤ 500); run `POST /vector/search` with query="authentication" (assert top-3 contains semantically relevant Artifact nodes).

- [x] T029 [P] [US2] Create src/context_os/vector/client.py: `VectorSessionHelper` providing async context manager wrapping the SQLAlchemy async session; `register_pgvector_codec(engine)` called once in DB init to register the asyncpg vector codec via `engine.sync_engine` connect event
- [x] T030 [P] [US2] Implement 1-hop and k-hop graph traversal in src/context_os/graph/queries.py: `traverse(pool, tenant_id, from_id, max_hops=1, edge_types=None, node_types=None) → TraversalResult`; constructs Cypher MATCH clause `(start {id: $from_id, tenant_id: $tenant_id})-[r*1..{max_hops}]->(end)` with optional WHERE on edge type labels and end node type property; uses AGE parameter map for from_id and tenant_id; records `query_ms` via time.monotonic(); raises `GraphQueryError` on AGE failure; `TraversalResult` dataclass (nodes: list[dict], edges: list[dict], query_ms: float)
- [x] T031 [US2] Implement top-k semantic retrieval in src/context_os/vector/search.py: `search(session, tenant_id, query_text, k=5, node_types=None) → list[SearchResult]`; encode query_text via `get_embedding_model().encode(query_text)`; `SELECT id, node_type, content, embedding <=> $query AS distance FROM node_embeddings WHERE tenant_id = $tenant_id AND node_type = ANY($types) ORDER BY distance LIMIT $k`; return `SearchResult(node_id, node_type, content, distance)` list; raise `VectorSearchError` on DB failure; `node_types` defaults to ["Artifact", "Memory"]
- [x] T032 [US2] Implement POST /graph/traverse endpoint in src/context_os/api/graph.py per contracts/api.yaml: parse request body (from_id, edge_types, max_hops default=1 max=5, node_types); validate max_hops ≤ 5 (400 if violated); call `graph/queries.traverse()`; serialize TraversalResult to response schema; 500 with trace_id on GraphQueryError; requires `Depends(get_current_tenant)`
- [x] T033 [US2] Implement POST /vector/search endpoint in src/context_os/api/vector.py per contracts/api.yaml: parse request body (query, k default=5 max=50, node_types default=[Artifact,Memory]); validate query is non-empty string (400 if empty); call `vector/search.search()`; join results against AGE graph to fetch full node properties for response; serialize to VectorSearchResult; 500 with trace_id on VectorSearchError; requires `Depends(get_current_tenant)`

**Checkpoint**: `POST /graph/traverse {from_id: <known>, max_hops: 2}` returns correct adjacent nodes; `POST /vector/search {query: "open pull request"}` returns top-5 semantically relevant Artifacts; both respond in < 500ms on local dataset.

---

## Phase 5: User Story 3 — Multi-Tenant Auth with Tenant Isolation (Priority: P3)

**Goal**: Two stub tenants each see only their own data across all three query interfaces; unauthenticated requests are rejected before any data access.

**Independent Test**: Tenant A has ingested data; authenticate as Tenant B → `GET /admin/entities`, `POST /graph/traverse`, `POST /vector/search` all return empty result sets with zero Tenant A data in response body or structured logs.

- [x] T034 [US3] Harden tenant isolation in src/context_os/graph/queries.py and src/context_os/graph/mutations.py: add `_assert_tenant_id(tenant_id: str)` that raises `TenantIsolationError` if tenant_id is empty/None; call this assertion at the top of every public function; confirm every MATCH clause includes `tenant_id: $tenant_id` in the Cypher node pattern; add integration test script (scripts/verify_isolation.py) that creates two tenants, ingests 3 nodes under tenant A, queries all three APIs as tenant B, and asserts zero results
- [x] T035 [P] [US3] Harden tenant isolation in src/context_os/vector/search.py: add `_assert_tenant_id(tenant_id)` guard at top of `search()`; confirm the SQL WHERE clause always includes `node_embeddings.tenant_id = :tenant_id`; raise `TenantIsolationError` if called without tenant_id
- [x] T036 [P] [US3] Harden tenant isolation in src/context_os/relational/repositories.py: add `_assert_tenant_id(tenant_id)` guard in OAuthTokenRepository.get_for_tenant_integration and CheckpointRepository methods; confirm all SELECT queries include tenant_id in WHERE clause; add runtime assertion that SQLAlchemy query `.where()` clause contains tenant_id
- [x] T037 [US3] Verify unauthenticated rejection across all API endpoints: call GET /admin/entities, POST /graph/traverse, POST /vector/search, POST /ingest/{integration} without Authorization header; assert each returns 401 JSON `{code: "auth_error", message: "..."}` with no data in response body; confirm Clerk JWT verification occurs before any DB call (check structured log: auth.request.rejected emitted, no graph/vector/ingest events follow)
- [x] T038 [US3] Create tests/integration/test_tenant_isolation.py: fixtures create tenant_a and tenant_b from conftest.py; ingest 3 mock nodes (1 Artifact, 1 Initiative, 1 Signal) under tenant_a via graph/mutations.py directly; authenticate as tenant_b; assert GET /admin/entities returns 0 items; assert POST /graph/traverse returns empty nodes+edges; assert POST /vector/search returns empty results; assert no tenant_a data in any response field

**Checkpoint**: `python scripts/verify_isolation.py` exits 0 with "All isolation checks passed"; unauthenticated curl to any endpoint returns 401.

---

## Phase 6: User Story 4 — Observable Operations Baseline (Priority: P4)

**Goal**: Every ingest run, graph query, and vector retrieval emits a structured trace visible in the local Langfuse UI within 30 seconds, including all required governance markers.

**Independent Test**: Run one ingest → open http://localhost:3000 → confirm trace exists with context_os.agent_identity, context_os.autonomy_level, context_os.tenant_id, context_os.input_summary, context_os.output_summary, context_os.governance_markers all present and non-empty.

- [x] T039 [US4] Wire OTEL span instrumentation to all ingest operations in src/context_os/api/ingest.py and src/context_os/ingestion/base.py: wrap each ingest run in a span named "ingest.run"; set required context_os.* span attributes: agent_identity="ingest-agent-v1", autonomy_level=2, tenant_id, input_summary="integration={integration} full={full}", output_summary="records={n} nodes_created={n} nodes_updated={n}", governance_markers="{}"; emit `ingest.run.started` / `ingest.run.completed` / `ingest.run.failed` / `ingest.source.rate_limited` / `ingest.source.token_expired` structured log events via emit_structured_log() per schema.py EVENT constants
- [x] T040 [P] [US4] Wire OTEL span instrumentation to graph operations in src/context_os/api/graph.py: wrap each traversal in span named "graph.traverse"; set context_os.agent_identity="graph-query-v1", autonomy_level=2, tenant_id, input_summary="from_id={id} max_hops={n} edge_types={types}", output_summary="nodes_returned={n} edges_returned={n} query_ms={ms}", governance_markers="{}"; emit `graph.traverse.executed` or `graph.traverse.error` structured log
- [x] T041 [P] [US4] Wire OTEL span instrumentation to vector operations in src/context_os/api/vector.py: wrap each search in span named "vector.search"; set context_os.agent_identity="vector-search-v1", autonomy_level=2, tenant_id, input_summary="query_len={n} k={k}", output_summary="results_returned={n} top_distance={d}", governance_markers="{}"; emit `vector.search.executed` or `vector.search.error` structured log
- [x] T042 [US4] Create tests/fault/test_oauth_expiry.py: use mock_oauth_expire_middleware fixture from conftest.py to inject 401 after first page of GitHub ingest; assert: IngestError raised with code="token_expired"; checkpoint row in DB contains the cursor from the last successful page; no unhandled exception propagates to the API layer; partial nodes already committed to graph are present. Create tests/fault/test_rate_limit.py: inject 429 with Retry-After: 1 on second page; assert: adapter backs off, checkpoint preserved, retry succeeds, no duplicate nodes in graph after re-run

**Checkpoint**: After any ingest/query, open Langfuse UI → trace appears with all context_os.* attributes populated; fault tests pass confirming graceful error handling per SC-007.

---

## Polish & Cross-Cutting Concerns

**Purpose**: Quality gates, remaining test coverage, and end-to-end validation.

- [x] T043 Run `uv run ruff check src/ tests/ --fix` then `uv run ruff format src/ tests/`; resolve all remaining warnings; target: zero ruff violations
- [x] T044 [P] Run `uv run pyright src/` in strict mode; fix all type errors; confirm no implicit `Any` or missing return types; target: zero pyright errors
- [x] T045 [P] Create tests/unit/test_normalizers.py: unit tests for all three normalizers (no network calls, static fixture data); verify each row in data-model.md source normalization map: GitHub Repo → Initiative (name→title), GitHub PR → Artifact (title, body, state), GitHub Issue open → Signal, GitHub Issue closed → Artifact, Jira Project → Initiative, Jira Epic → Goal, Jira Issue done → Artifact, Slack Message → Signal (ts→occurred_at), Actor dedup via email match; assert correct node_type, source, source_id on each output
- [x] T046 End-to-end quickstart.md validation: execute all 11 steps in sequence (docker compose up → alembic upgrade head → graph init → tenant create → auth github → ingest github → start API → GET /admin/entities → POST /graph/traverse → POST /vector/search → verify Langfuse); document any deviation from expected output in quickstart.md; fix any discovered issues; confirm SC-001 through SC-006 pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001–T005) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational completion
- **US2 (Phase 4)**: Depends on Foundational + US1 (needs ingested data to query)
- **US3 (Phase 5)**: Depends on Foundational + US1 (needs ingested data to test isolation)
- **US4 (Phase 6)**: Depends on US1 + US2 + US3 (instruments all operations)
- **Polish (Final)**: Depends on all user story phases

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2; prerequisite for all other stories per spec
- **US2 (P2)**: Requires US1 to have ingested data; vector search requires embeddings written during ingest
- **US3 (P3)**: Requires US1 to have ingested data under tenant A for isolation verification
- **US4 (P4)**: Instruments all operations — implement last to avoid rework as operations stabilize

### Within Each User Story

- Abstract base (T019) before concrete adapters (T020–T026)
- Adapters (T020–T026) are [P] — all different files, no inter-adapter dependencies
- Embedding model (T026) before ingest endpoint (T027) — T027 calls T026
- Ingest endpoint (T027) before admin endpoint (T028) — both [P] with each other as they touch different files
- Vector retrieval (T031) before API endpoint (T033) — sequential

### Parallel Opportunities

Within Phase 2: T006, T007 [P] immediately; T012, T014, T015 [P] once T008 exists; T016 [P] with T012
Within US1: T020, T021, T022, T023, T024, T025, T026 all [P] once T019 is done; T027 and T028 [P] with each other
Within US2: T029, T030 [P]; T032 and T033 are separate files [P] but depend on T030/T031 respectively
Within US3: T034, T035, T036 [P] — different files; T037 depends on T034–T036
Within US4: T039, T040, T041 [P] — different files

---

## Parallel Example: User Story 1

```bash
# After T019 (IngestAdapter base) is complete, launch simultaneously:
Task T020: "Create GitHub client in src/context_os/ingestion/github/client.py"
Task T021: "Create GitHub normalizer in src/context_os/ingestion/github/normalizer.py"
Task T022: "Create Jira client in src/context_os/ingestion/jira/client.py"
Task T023: "Create Jira normalizer in src/context_os/ingestion/jira/normalizer.py"
Task T024: "Create Slack client in src/context_os/ingestion/slack/client.py"
Task T025: "Create Slack normalizer in src/context_os/ingestion/slack/normalizer.py"
Task T026: "Create embedding model wrapper in src/context_os/vector/embeddings.py"

# After T020–T026 complete:
Task T027: "Implement ingest endpoints in src/context_os/api/ingest.py"
Task T028: "Implement admin entities endpoint in src/context_os/api/admin.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (**CRITICAL** — blocks everything)
3. Complete Phase 3: User Story 1
4. **STOP AND VALIDATE**: `cli ingest github` → `GET /admin/entities` → assert nodes visible
5. This alone proves persistence interfaces, normalization layer, and the admin UI

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 → Ingest + admin view (MVP!)
3. US2 → Graph queries + vector search
4. US3 → Tenant isolation hardened
5. US4 → Full observability confirmed
6. Polish → Quality gates pass

### Parallel Team Strategy

Once Phase 2 (Foundational) is complete, the adapters (T020–T026) are fully parallelizable across team members:
- Developer A: GitHub client + normalizer (T020, T021)
- Developer B: Jira client + normalizer (T022, T023)
- Developer C: Slack client + normalizer + embedding model (T024, T025, T026)
- All merge before T027 (ingest endpoint) and T028 (admin endpoint)

---

## Notes

- **Tests included**: Only fault injection tests (T042) are task-generated — explicitly required by SC-007 ("verified by injected fault tests") and tenant isolation test (T038) as the primary verification vehicle for US3. Unit normalizer tests (T045) in polish phase for normalization map verification.
- **Constitution non-negotiable**: Every node write MUST include tenant_id (T013 enforces this). Every span MUST include context_os.* governance attributes (T039–T041). No exceptions.
- **AGE injection safety**: Never use Python f-strings inside Cypher strings. Always use AGE parameter map for user-supplied values (enforced in T012, T013, T030).
- **Checkpoint discipline**: Checkpoint row updated ONLY after successful DB commit — not after fetch, not after normalize (enforced in T019 base, saved in T027 ingest endpoint).
- **Embedding on ingest**: Artifact and Memory nodes get embeddings written to node_embeddings at ingest time (T027). Vector search (T031) reads from this table — US2 depends on US1 having run first.
- **AGE sunset trigger**: If graph query p95 exceeds 500ms on representative local dataset, fall back to plain Postgres adjacency tables per constitution v1.1.0. Monitor via query_ms in TraversalResult.
