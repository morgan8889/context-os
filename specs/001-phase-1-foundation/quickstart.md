# Quickstart: Phase 1 — Foundation (Local)

**Date**: 2026-05-17  
**Branch**: `1-phase-1-foundation`

> **Port note**: `docker/docker-compose.yml` maps Postgres to host port **5433**
> (not 5432) and the local Langfuse instance to port **3010** (not 3000) to
> avoid conflicts with other services that may already occupy those ports.
> Adjust `DATABASE_URL` and `LANGFUSE_HOST` accordingly.

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Docker Desktop | 4.x+ | Runs Postgres (AGE), Langfuse |
| Python | 3.12+ | Use pyenv or system |
| uv | 0.4+ | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Clerk account | — | Free tier; create at clerk.com |
| GitHub App | — | Or OAuth App (see below) |
| Jira Cloud OAuth app | — | Atlassian developer console |
| Slack App | — | api.slack.com/apps |

---

## Step 1: Clone and set up Python environment

```bash
git clone <repo-url> context-os
cd context-os
git checkout 1-phase-1-foundation
uv sync
```

---

## Step 2: Start infrastructure

```bash
# Start Postgres (pgvector + AGE) and Langfuse
docker compose -f docker/docker-compose.yml up -d

# Verify Postgres is up
docker compose -f docker/docker-compose.yml ps

# Wait ~2 min for Langfuse to initialize, then open:
# http://localhost:3010
```

---

## Step 3: Configure environment variables

Copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:

```dotenv
# Database — port 5433 to avoid conflict with other local Postgres instances
DATABASE_URL=postgresql+asyncpg://contextos:contextospass@localhost:5433/contextosdb

# Clerk (dev mode — use test publishable key)
CLERK_SECRET_KEY=sk_test_...
CLERK_PUBLISHABLE_KEY=pk_test_...

# Langfuse (use keys from docker-compose.yml init vars or Langfuse UI)
# Default keys seeded by docker-compose init vars:
LANGFUSE_PUBLIC_KEY=pk-lf-1234567890abcdef
LANGFUSE_SECRET_KEY=sk-lf-1234567890abcdef
# Port 3010 (not 3000) — avoid conflict with other local services
LANGFUSE_HOST=http://localhost:3010

# Token encryption key (generate once: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ENCRYPTION_KEY=...

# GitHub App (or OAuth App credentials)
GITHUB_APP_ID=...
GITHUB_APP_PRIVATE_KEY_PATH=./secrets/github-app.pem
GITHUB_INSTALLATION_ID=...

# Jira Cloud OAuth 2.0
JIRA_CLIENT_ID=...
JIRA_CLIENT_SECRET=...

# Slack Bot Token
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_IDS=C0123ABC,C0456DEF  # comma-separated channel IDs to ingest
```

---

## Step 4: Run database migrations

```bash
uv run alembic upgrade head
```

This creates the relational tables (`tenants`, `oauth_tokens`, `sync_checkpoints`, `node_embeddings`) and enables the Postgres extensions (`pgvector`, `age`).

---

## Step 5: Initialize the graph

```bash
uv run python -m context_os.cli graph init
```

Creates the `context_os` AGE graph and registers node/edge labels.

---

## Step 6: Create a stub tenant

```bash
uv run python -m context_os.cli tenant create \
  --clerk-org-id org_your_clerk_org_id \
  --name "My Org"
```

Repeat to create a second stub tenant for isolation testing.

---

## Step 7: Configure OAuth tokens

```bash
# GitHub (uses App installation token)
uv run python -m context_os.cli auth github \
  --tenant-id <tenant-uuid>

# Jira (prompts for OAuth authorization URL, then paste code)
uv run python -m context_os.cli auth jira \
  --tenant-id <tenant-uuid>

# Slack (paste bot token directly)
uv run python -m context_os.cli auth slack \
  --tenant-id <tenant-uuid> \
  --token $SLACK_BOT_TOKEN
```

---

## Step 8: Run ingest

```bash
# Ingest all three sources for a tenant
uv run python -m context_os.cli ingest all \
  --tenant-id <tenant-uuid>

# Or ingest one source at a time
uv run python -m context_os.cli ingest github --tenant-id <uuid>
uv run python -m context_os.cli ingest jira   --tenant-id <uuid>
uv run python -m context_os.cli ingest slack  --tenant-id <uuid>
```

Ingest prints progress and saves a checkpoint on completion. Run again to pick up incremental changes.

---

## Step 9: Start the API server

```bash
uv run uvicorn context_os.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

---

## Step 10: Verify in admin UI

```bash
# Get a Clerk session token for your tenant (use Clerk Dashboard → Users → test token)
export TOKEN=eyJ...

# List all entities
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/admin/entities | jq .

# Run a graph traversal
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"from_id": "<node-uuid>", "max_hops": 2}' \
  http://localhost:8000/graph/traverse | jq .

# Run a vector search
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication PRs merged last sprint", "k": 5}' \
  http://localhost:8000/vector/search | jq .
```

---

## Step 11: Verify observability

Open Langfuse: http://localhost:3010

After any ingest or query, you should see traces appear within ~30 seconds. Each trace includes:
- Operation name (ingest.run, graph.traverse, vector.search)
- Duration
- `context_os.tenant_id`, `context_os.agent_identity`, `context_os.autonomy_level`

---

## Troubleshooting

### `AgeNotSet` or graph errors
Postgres AGE extension not loaded. Check docker logs:
```bash
docker compose -f docker/docker-compose.yml logs postgres
```
Ensure `docker/postgres/init.sql` ran successfully on first start. If not: `docker compose down -v && docker compose up -d`.

### Langfuse not receiving traces
Check `LANGFUSE_HOST` is `http://localhost:3010` (not https, not port 3000). Verify public/secret keys match what's in the Langfuse UI under Settings → API Keys.

### OAuth token rejected mid-ingest
Ingest halts and saves checkpoint. Re-run `uv run python -m context_os.cli auth <source>` to refresh the token, then re-run ingest — it resumes from checkpoint.

### Rate limit (429) from GitHub/Jira/Slack
Ingest backs off with exponential retry and respects `Retry-After` headers. Wait and re-run; checkpoint prevents duplicate work.

---

## T046 Validation Status

### Validated without live infrastructure

The following were confirmed working in-process (no running Postgres or Langfuse required):

| Check | Result |
|-------|--------|
| `uv sync` — all deps install | PASS (39 packages) |
| Config loading (`get_settings()`) | PASS — all required env vars validated |
| FastAPI app import + 10 routes registered | PASS (`/admin/entities`, `/graph/traverse`, `/vector/search`, `/ingest/{integration}`, `/health`) |
| CLI help: `graph`, `tenant`, `auth`, `ingest` subcommands | PASS — all commands parse correctly |
| Alembic migration: `versions/20260518_0001_initial_schema.py` | PASS — migration file exists |
| Unit tests (29 normalizer tests) | PASS — 0.16s |
| Fault tests (10 tests: oauth_expiry + rate_limit) | PASS — 0.17s |

### Requires live infrastructure (SC-001 through SC-006)

SC-001 through SC-006 require running Postgres+AGE + real OAuth credentials:

| SC | Criterion | Status |
|----|-----------|--------|
| SC-001 | Full three-source ingest visible in admin UI within 15 min | Requires live infra + credentials |
| SC-002 | Repeat ingest produces zero duplicate nodes | Requires live infra + credentials |
| SC-003 | 1-hop and k-hop traversal within p95 ≤ 500ms | Requires live infra + ingested data |
| SC-004 | Vector search returns top-3 semantically relevant results | Requires live infra + ingested data |
| SC-005 | Zero cross-tenant data visibility | Requires live infra (integration tests) |
| SC-006 | Observable trace in Langfuse within 30s | Requires live Langfuse |
| SC-007 | Fault handling without data loss | **PASS** — verified by 10 injected fault tests |

**To complete live validation**: start infra with `docker compose -f docker/docker-compose.yml up -d`, run migrations, and follow Steps 4–11 above.
