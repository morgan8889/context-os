# Quickstart: Phase 4 — Closed Beta Readiness

**Audience**: Developer setting up Phase 4 locally for the first time
**Prerequisites**: Phase 1 backend running, Phase 2 agents deployed, Phase 3 frontend serving

---

## Scenario 1: New Operator Onboarding Flow (Happy Path)

**Goal**: Walk through the seven-step Workflow-First onboarding as a fresh operator.

### Setup
```bash
# Start full stack (backend + Langfuse + new Phase 4 containers)
docker compose -f docker/docker-compose.yml up -d

# Apply Phase 4 migration
uv run alembic upgrade head

# Confirm new tables exist
uv run python -c "
from context_os.db.engine import get_session
import asyncio
async def check():
    async with get_session() as s:
        from sqlalchemy import text
        r = await s.execute(text(\"SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'onboarding%' OR tablename LIKE 'ingest%' OR tablename LIKE 'activation%'\"))
        print([row[0] for row in r])
asyncio.run(check())
# Expected: ['onboarding_sessions', 'ingest_jobs', 'activation_events', 'oauth_pending_sessions']
"

# Start frontend
cd web && npm run dev
```

### Steps
1. Open the app as a freshly-created test user (use Clerk dashboard to create a new user in a new org)
2. Land on the sign-up page → confirm transformation thesis is visible, no feature list
3. Confirm discovery survey appears after account creation
4. Select an option (e.g., "briefings") → session should advance to `connect` step
5. Click "Connect Jira" → popup opens, OAuth flow begins (in dev, use the Atlassian sandbox)
6. Complete connection → parent wizard marks Jira card green
7. Repeat for GitHub and Slack (or skip one to test partial-success path)
8. Confirm scope-selection screen pre-checks active projects
9. Confirm scope → ingest begins → progress surface shows estimated time
10. Leave the tab, return later → `GET /onboarding/session` restores position
11. When ingest completes → notification email sent (requires `RESEND_API_KEY` configured)
12. Review first briefing → approve → activation event emitted, full nav revealed

**Verify**:
```bash
# Check onboarding session state
curl -H "Authorization: Bearer $CLERK_JWT" http://localhost:8000/onboarding/session

# Check activation event was recorded
uv run python -c "
from context_os.db.engine import get_session
import asyncio
async def check():
    async with get_session() as s:
        from sqlalchemy import text
        r = await s.execute(text('SELECT * FROM activation_events'))
        for row in r: print(dict(row._mapping))
asyncio.run(check())
"
```

---

## Scenario 2: OAuth Failure Recovery

**Goal**: Confirm the operator can recover from a failed OAuth connection.

1. Start onboarding to the `connect` step
2. Begin GitHub OAuth flow → cancel in the provider popup (simulate rejection)
3. Confirm parent wizard shows GitHub card as "Connection failed — reconnect"
4. Confirm session remains at `connect` step (not advanced)
5. Retry → popup reopens → complete connection
6. Confirm session advances normally after successful retry

---

## Scenario 3: Ingest Stall Recovery

**Goal**: Confirm recovery path when ingest stalls.

```bash
# Simulate stall: update ingest job directly
uv run python -c "
from context_os.db.engine import get_session
import asyncio
from sqlalchemy import text
async def stall():
    async with get_session() as s:
        await s.execute(text(\"UPDATE ingest_jobs SET status='stalled', last_record_at=now()-interval'3 hours' WHERE status='running'\"))
        await s.commit()
asyncio.run(stall())
"
```

1. Return to the progress surface → confirm stall message appears
2. Click retry → ingest resumes from checkpoint (scope not re-entered)
3. Confirm `GET /onboarding/session` shows `current_step: ingest` (not regressed to scope)

---

## Scenario 4: Admin Funnel View

**Goal**: Confirm Platform Operator sees all beta orgs at correct funnel stages.

```bash
# Set up two orgs at different stages
# Org A: completed survey only
# Org B: fully activated

# Get Platform Operator JWT (Clerk dashboard → add `platform_operator: true` custom claim)
export PO_JWT="<platform_operator_jwt>"

# Funnel view
curl -H "Authorization: Bearer $PO_JWT" http://localhost:8000/admin/funnel

# Expected: two rows, Org A at step=connect, Org B at step=activated with timing data

# Survey responses
curl -H "Authorization: Bearer $PO_JWT" http://localhost:8000/admin/survey-responses
```

---

## Scenario 5: Tenant Impersonation

**Goal**: Confirm Platform Operator can view Org A's data as read-only.

```bash
# Start impersonation session
RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $PO_JWT" \
  http://localhost:8000/admin/impersonate/<org_a_clerk_id>)
IMPERSONATION_TOKEN=$(echo $RESPONSE | jq -r .token)

# Use impersonation token to view Org A's onboarding session
curl -H "Authorization: Bearer $PO_JWT" \
     -H "X-Impersonation-Token: $IMPERSONATION_TOKEN" \
     http://localhost:8000/onboarding/session
# Expected: Org A's session, not the Platform Operator's org

# Attempt a write — must be blocked
curl -X POST \
  -H "Authorization: Bearer $PO_JWT" \
  -H "X-Impersonation-Token: $IMPERSONATION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"option":"briefings"}' \
  http://localhost:8000/onboarding/survey
# Expected: 403 {"code":"write_blocked_during_impersonation"}

# Revoke the session
curl -X DELETE \
  -H "Authorization: Bearer $PO_JWT" \
  -H "X-Impersonation-Token: $IMPERSONATION_TOKEN" \
  http://localhost:8000/admin/impersonate/revoke
```

---

## Scenario 6: Nightly Eval (Manual Run)

**Goal**: Confirm the eval suite runs and reports correctly.

```bash
# Trigger manually (mimics GitHub Actions workflow_dispatch)
uv run pytest tests/evals/ -m nightly_eval -v

# With GPU unavailable (simulates CI environment without GPU runner)
CI_GPU_AVAILABLE="" uv run pytest tests/evals/ -m nightly_eval -v
# Expected: GPU-dependent fixtures show as 'SKIPPED (infrastructure-unavailable)', not 'FAILED'

# Introduce a deliberate regression and confirm gate fires
# (Edit a Synthesizer prompt to produce garbage, re-run eval)
```

---

## Scenario 7: Telemetry Dashboard

**Goal**: Confirm Prometheus metrics and Grafana dashboards are populated.

```bash
# Confirm metrics endpoint is live
curl http://localhost:8000/metrics | grep context_os_

# Open Grafana
open http://localhost:3001
# Default credentials: admin/admin
# Navigate to "Agent Health" dashboard → confirm agent invocation rates visible
# Navigate to "Ingestion Freshness" dashboard → confirm last_record_at gauge updating
```

---

## Environment Variables Checklist (Phase 4 additions)

```bash
# Required for admin/impersonation:
IMPERSONATION_SECRET=<random-256-bit-hex>
PLATFORM_OPERATOR_CLERK_USER_ID=<your-clerk-user-id>

# Optional (transactional email):
RESEND_API_KEY=re_...
RESEND_FROM_EMAIL=ingest@contextops.ai

# Pre-existing (Phase 1/2/3 carry-forward):
DATABASE_URL=postgresql+asyncpg://...
CLERK_SECRET_KEY=sk_test_...
LANGFUSE_SECRET_KEY=...
ANTHROPIC_API_KEY=sk-ant-...
VITE_API_URL=http://localhost:8000
```
