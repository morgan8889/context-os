# Data Model: Phase 4 — Closed Beta Readiness

**Date**: 2026-05-20
**Migration**: `0003_phase4_closed_beta.py` (Alembic)

All Phase 4 additions land in a single Alembic migration to minimise migration
count. Tables use the existing pattern: `UUID` primary keys, `tenant_id` FK
to `tenants.id` (Phase 1), `created_at` / `updated_at` timestamps.

---

## New Tables

### `onboarding_sessions`

One row per tenant — tracks position in the seven-step activation journey.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | Generated |
| `tenant_id` | UUID FK `tenants(id)` UNIQUE | One session per tenant |
| `current_step` | TEXT | Enum: `survey \| connect \| scope \| ingest \| briefing \| activated` |
| `survey_answer` | JSONB | `{ "option": "briefings \| dependencies \| ...", "free_text": "..." }` |
| `connected_integrations` | TEXT[] | e.g. `["jira", "github"]` |
| `scope_selection` | JSONB | `{ "jira_projects": [...], "github_repos": [...], "slack_channels": [...] }` |
| `ingest_job_id` | UUID FK `ingest_jobs(id)` NULLABLE | Set when ingest begins |
| `step_started_at` | JSONB | `{ "connect": "2026-05-20T10:00:00Z", ... }` — one entry per step |
| `step_completed_at` | JSONB | Same structure — used for activation timing segments |
| `activated_at` | TIMESTAMP NULLABLE | Set when first briefing is approved |
| `created_at` | TIMESTAMP | |
| `updated_at` | TIMESTAMP | |

**State transitions (enforced in `OnboardingService`)**:
```
(new) → survey → connect → scope → ingest → briefing → activated
```
Revert allowed on: `connect` (OAuth failure) → back to `connect`.
Revert allowed on: `ingest` (stall > 30 min) → back to `scope`.

---

### `activation_events`

Immutable record created at the activation moment (first briefing approval).
Stores the four timing segments for the admin funnel view.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `tenant_id` | UUID FK UNIQUE | One activation event per tenant |
| `occurred_at` | TIMESTAMP | When first briefing was approved |
| `signup_to_connect_ms` | BIGINT | `step_completed_at.connect - step_started_at.survey` |
| `connect_to_ingest_ms` | BIGINT | `step_completed_at.ingest - step_completed_at.connect` |
| `ingest_to_briefing_ms` | BIGINT | `step_completed_at.briefing - step_completed_at.ingest` |
| `total_active_attention_ms` | BIGINT | Sum of active-attention intervals (excludes overnight wait) |
| `accept_as_is` | BOOLEAN | Whether the first briefing was approved without editing |
| `created_at` | TIMESTAMP | |

---

### `ingest_jobs`

One row per ingest run. Created when the operator confirms scope; updated
throughout the ingest process.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `tenant_id` | UUID FK `tenants(id)` | |
| `source` | TEXT | `"jira" \| "github" \| "slack" \| "all"` |
| `status` | TEXT | `"running" \| "completed" \| "stalled" \| "failed"` |
| `progress_pct` | INTEGER | 0–100 |
| `record_counts` | JSONB | `{ "initiatives": N, "prs": M, "threads": K }` |
| `started_at` | TIMESTAMP | |
| `completed_at` | TIMESTAMP NULLABLE | Set on `completed` or `failed` |
| `last_record_at` | TIMESTAMP NULLABLE | Updated after each successful record insert (drives freshness gauge) |
| `error_detail` | JSONB NULLABLE | `{ "source": "jira", "message": "...", "span_id": "..." }` |
| `created_at` | TIMESTAMP | |
| `updated_at` | TIMESTAMP | |

**Indexes**: `(tenant_id, status)`, `(tenant_id, started_at DESC)`.

---

### `oauth_pending_sessions`

Short-lived records holding PKCE state during the OAuth redirect flow.
Rows expire after 10 minutes; a background cleanup job or TTL filter removes
them on read.

| Column | Type | Notes |
|--------|------|-------|
| `state` | TEXT PK | CSRF-safe random string |
| `tenant_id` | UUID FK `tenants(id)` | |
| `source` | TEXT | `"jira" \| "github" \| "slack"` |
| `code_verifier` | TEXT | Server-side PKCE verifier (never sent to client) |
| `expires_at` | TIMESTAMP | `now() + 10 minutes` |

---

### `revoked_impersonation_tokens`

JTI (JWT ID) blocklist for impersonation tokens. Checked on every
impersonation request; inserted by `/admin/impersonate/revoke`.

| Column | Type | Notes |
|--------|------|-------|
| `jti` | TEXT PK | UUID from the HS256 JWT `jti` claim |
| `revoked_at` | TIMESTAMP | |

---

## Modified Tables

### `tenants` (Phase 1 — add columns)

| Column | Type | Notes |
|--------|------|-------|
| `beta_cohort_id` | TEXT NULLABLE | Identifies which beta cohort this tenant belongs to |
| `onboarded_by` | TEXT NULLABLE | Platform Operator user ID who initiated provisioning |

---

## Derived View: Admin Funnel Row

Not a persisted table — computed from `onboarding_sessions` +
`activation_events` + `ingest_jobs` on each admin panel request.

```sql
SELECT
  t.id AS tenant_id,
  t.name,
  os.current_step,
  os.connected_integrations,
  os.activated_at,
  ae.occurred_at AS activation_occurred_at,
  ae.signup_to_connect_ms,
  ae.connect_to_ingest_ms,
  ae.ingest_to_briefing_ms,
  ae.total_active_attention_ms,
  ae.accept_as_is,
  ij.status AS ingest_status,
  ij.last_record_at,
  -- drop-off flag: pre-activated org stuck > 48h at current step
  CASE
    WHEN os.activated_at IS NULL AND
         now() - (os.step_started_at->>os.current_step)::timestamptz > interval '48 hours'
    THEN true ELSE false
  END AS drop_off_flag
FROM tenants t
JOIN onboarding_sessions os ON os.tenant_id = t.id
LEFT JOIN activation_events ae ON ae.tenant_id = t.id
LEFT JOIN ingest_jobs ij ON ij.id = os.ingest_job_id;
```

---

## Entity Relationships

```text
tenants (Phase 1)
  └── onboarding_sessions (1:1)
        └── ingest_jobs (1:1 per run, via ingest_job_id FK)
  └── activation_events (1:1, created at activation moment)
  └── oauth_pending_sessions (1:N, short-lived)
  └── OAuthToken (Phase 1, extended with 3 sources)

revoked_impersonation_tokens (standalone, no FK — platform-level)
```

---

## Config Changes (`src/context_os/config.py`)

```python
# New in Phase 4:
resend_api_key: str | None = None          # Optional — no-op when absent
resend_from_email: str = "noreply@contextops.ai"
impersonation_secret: str = ""             # 501 when absent
platform_operator_clerk_user_id: str = ""  # Gating admin routes
```
