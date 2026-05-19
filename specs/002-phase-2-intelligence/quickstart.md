# Quickstart: Phase 2 — Intelligence

End-to-end integration scenarios for the Operational Synthesizer agent, Dependency
Mapper agent, and approval inbox. These scenarios assume Phase 1 Foundation is running
(`uv run uvicorn context_os.main:app --reload --port 8000`) with ingested data.

---

## Prerequisites

```bash
# Verify Phase 1 is running with data
curl -H "Authorization: Bearer $CLERK_JWT" http://localhost:8000/admin/entities?limit=5

# Expected: JSON with at least 5 graph nodes (Goal, Initiative, Signal, etc.)
# If empty: run an ingest first
curl -X POST -H "Authorization: Bearer $CLERK_JWT" http://localhost:8000/ingest/github
curl -X POST -H "Authorization: Bearer $CLERK_JWT" http://localhost:8000/ingest/jira

# Start infra (if not already running)
docker compose -f docker/docker-compose.yml up -d

# Run Phase 2 migration
uv run alembic upgrade head
```

---

## Scenario 1: Generate and approve a weekly briefing

This is the primary Phase 2 exit criterion. Run this weekly for four consecutive weeks.

### Step 1: Trigger briefing generation

```bash
RUN_ID=$(curl -s -X POST \
  -H "Authorization: Bearer $CLERK_JWT" \
  -H "Content-Type: application/json" \
  -d '{"window_days": 7}' \
  http://localhost:8000/briefing/generate | jq -r '.run_id')

echo "Briefing run started: $RUN_ID"
```

### Step 2: Poll for completion (target: under 5 minutes)

```bash
while true; do
  STATUS=$(curl -s \
    -H "Authorization: Bearer $CLERK_JWT" \
    "http://localhost:8000/briefing/status/$RUN_ID" | jq -r '.status')

  echo "Status: $STATUS"
  [ "$STATUS" = "complete" ] || [ "$STATUS" = "failed" ] && break
  sleep 15
done

# Get the approval item ID from the completed run
ITEM_ID=$(curl -s \
  -H "Authorization: Bearer $CLERK_JWT" \
  "http://localhost:8000/briefing/status/$RUN_ID" | jq -r '.approval_item_id')
```

### Step 3: Review the draft in the approval inbox

```bash
# List pending items
curl -s -H "Authorization: Bearer $CLERK_JWT" \
  "http://localhost:8000/inbox?status=pending" | jq '.items[] | {id, item_type, preview, stale}'

# Read the full briefing draft
curl -s -H "Authorization: Bearer $CLERK_JWT" \
  "http://localhost:8000/inbox/$ITEM_ID" | jq '.content.sections'
```

**Expected output**: A structured JSON with five sections — `progress`, `risks`,
`decisions`, `dependencies`, `escalations`. Each item has `text` and `source_ids`.

Check for failure flags:
```bash
curl -s -H "Authorization: Bearer $CLERK_JWT" \
  "http://localhost:8000/inbox/$ITEM_ID" | jq '.failure_flags'

# Empty array = clean draft
# Non-empty = review each flagged issue before approving
```

### Step 4a: Approve as-is (counts toward ≥ 40% accept rate target)

```bash
curl -s -X POST \
  -H "Authorization: Bearer $CLERK_JWT" \
  "http://localhost:8000/inbox/$ITEM_ID/approve" | jq '{status, graph_node_id: .content}'
```

### Step 4b: Edit then approve

```bash
# Get the current draft content
DRAFT=$(curl -s -H "Authorization: Bearer $CLERK_JWT" \
  "http://localhost:8000/inbox/$ITEM_ID" | jq '.content')

# Edit the content (example: update a risk item)
EDITED=$(echo "$DRAFT" | jq '.sections.risks[0].text = "Updated risk description after operator review"')

curl -s -X POST \
  -H "Authorization: Bearer $CLERK_JWT" \
  -H "Content-Type: application/json" \
  -d "{\"edited_content\": $EDITED}" \
  "http://localhost:8000/inbox/$ITEM_ID/approve" | jq '{status}'
```

### Step 4c: Reject the draft

```bash
curl -s -X POST \
  -H "Authorization: Bearer $CLERK_JWT" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Too many hallucination flags; ingest more data first"}' \
  "http://localhost:8000/inbox/$ITEM_ID/reject" | jq '{status}'
```

### Step 5: Verify canonical graph state (approve path only)

```bash
# After approval, the briefing becomes an Artifact node in the graph
# Find it via the admin entities endpoint
curl -s -H "Authorization: Bearer $CLERK_JWT" \
  "http://localhost:8000/admin/entities?type=Artifact" | \
  jq '.items[] | select(.properties.subtype == "briefing")'
```

---

## Scenario 2: Dependency Mapper scan

The Dependency Mapper discovers hidden relationships and surfaces them for approval.

### Step 1: Trigger a dependency scan

```bash
SCAN=$(curl -s -X POST \
  -H "Authorization: Bearer $CLERK_JWT" \
  -H "Content-Type: application/json" \
  -d '{"max_depth": 3}' \
  http://localhost:8000/mapper/scan)

echo "$SCAN" | jq '{scan_id, status}'
```

### Step 2: Review proposed dependencies in the inbox

```bash
# Wait for scan to complete, then check for proposed_dependency items
curl -s -H "Authorization: Bearer $CLERK_JWT" \
  "http://localhost:8000/inbox?status=pending&item_type=proposed_dependency" | \
  jq '.items[] | {id, preview}'

# Read a specific proposed dependency
curl -s -H "Authorization: Bearer $CLERK_JWT" \
  "http://localhost:8000/inbox/$DEP_ITEM_ID" | \
  jq '{from: .content.from_node_id, to: .content.to_node_id, confidence: .content.confidence, evidence: .content.evidence}'
```

### Step 3: Approve or reject the proposed dependency

```bash
# Approve — creates DEPENDS_ON edge in the canonical graph
curl -s -X POST \
  -H "Authorization: Bearer $CLERK_JWT" \
  "http://localhost:8000/inbox/$DEP_ITEM_ID/approve" | jq '{status}'

# Reject — contributes to false-positive rate metric
curl -s -X POST \
  -H "Authorization: Bearer $CLERK_JWT" \
  -H "Content-Type: application/json" \
  -d '{"reason": "These initiatives are not actually coupled"}' \
  "http://localhost:8000/inbox/$DEP_ITEM_ID/reject" | jq '{status}'
```

### Step 4: Verify the approved dependency edge

```bash
# Traverse from the from-node to confirm the DEPENDS_ON edge was written
curl -s -X POST \
  -H "Authorization: Bearer $CLERK_JWT" \
  -H "Content-Type: application/json" \
  -d "{\"from_id\": \"$FROM_NODE_ID\", \"edge_types\": [\"DEPENDS_ON\"], \"max_hops\": 1}" \
  http://localhost:8000/graph/traverse | jq '.edges'
```

---

## Scenario 3: Run the evaluation suite

Run this after accumulating at least 5 real approved briefings as your golden dataset.

### Step 1: Build a golden dataset from approved briefings

```bash
# The CLI command builds a golden dataset from recent approved approval_items
uv run python -m context_os.cli eval build-dataset \
  --type synthesizer \
  --version "1.0.0" \
  --description "First four weeks of Phase 2 dogfooding"
```

### Step 2: Run the Synthesizer eval suite

```bash
EVAL=$(curl -s -X POST \
  -H "Authorization: Bearer $CLERK_JWT" \
  -H "Content-Type: application/json" \
  -d '{"eval_type": "synthesizer"}' \
  http://localhost:8000/eval/run)

EVAL_RUN_ID=$(echo "$EVAL" | jq -r '.run_id')
echo "Eval run started: $EVAL_RUN_ID"
```

### Step 3: Wait for results and check CI gates

```bash
# Poll for completion
while true; do
  STATUS=$(curl -s \
    -H "Authorization: Bearer $CLERK_JWT" \
    "http://localhost:8000/eval/runs/$EVAL_RUN_ID" | jq -r '.status')
  [ "$STATUS" != "running" ] && break
  sleep 5
done

# Check scores and gate status
curl -s -H "Authorization: Bearer $CLERK_JWT" \
  "http://localhost:8000/eval/runs/$EVAL_RUN_ID" | \
  jq '{gates_passed, scores}'
```

**Expected output for a passing eval run**:
```json
{
  "gates_passed": true,
  "scores": {
    "accept_rate": 0.45,
    "median_edit_distance": 0.31,
    "false_positive_risk_rate": 0.12,
    "failure_mode_detection": {
      "hallucinated_stakeholder": true,
      "stale_dependency": true,
      "missed_escalation": true,
      "citation_error": true
    }
  }
}
```

### Step 4: Run the Mapper eval suite

```bash
curl -s -X POST \
  -H "Authorization: Bearer $CLERK_JWT" \
  -H "Content-Type: application/json" \
  -d '{"eval_type": "mapper"}' \
  http://localhost:8000/eval/run | jq '{run_id}'
```

### Step 5: Trend eval results over time

```bash
curl -s -H "Authorization: Bearer $CLERK_JWT" \
  "http://localhost:8000/eval/runs?eval_type=synthesizer" | \
  jq '.items[] | {run_id, status, scores: {accept_rate: .scores.accept_rate}, gates_passed}'
```

---

## Telemetry verification

Every agent action should appear in Langfuse within 30 seconds of completion.

```bash
# Check OTEL traces for a briefing run
# (Langfuse UI: http://localhost:3000 — see docker-compose.yml)

# Verify required span attributes are populated
curl -s -H "Authorization: Bearer $CLERK_JWT" \
  "http://localhost:8000/briefing/status/$RUN_ID" | jq '{cost_tokens, latency_ms}'
```

Expected telemetry attributes on every agent span:
- `context_os.agent_identity` — `synthesizer` or `mapper`
- `context_os.autonomy_level` — `2` for Synthesizer, `1` or `2` for Mapper
- `context_os.tenant_id` — authenticated tenant
- `context_os.input_summary` — signal count and window description
- `context_os.output_summary` — item count proposed / draft section count
- `context_os.governance_markers` — `["requires_approval"]`

---

## Stale inbox item check

Items pending for more than 24 hours are flagged automatically.

```bash
# List stale items
curl -s -H "Authorization: Bearer $CLERK_JWT" \
  "http://localhost:8000/inbox?stale_only=true" | \
  jq '.items[] | {id, item_type, created_at}'
```

---

## Dev commands reference

```bash
# Install / update dependencies
uv sync

# Start infrastructure
docker compose -f docker/docker-compose.yml up -d

# Run Phase 2 migration
uv run alembic upgrade head

# Start API server
uv run uvicorn context_os.main:app --reload --port 8000

# CLI: build golden dataset
uv run python -m context_os.cli eval build-dataset --type synthesizer --version "1.0.0"

# CLI: run eval suite locally (without API)
uv run python -m context_os.cli eval run --type synthesizer

# Run all tests (unit + integration + eval)
uv run pytest

# Run only eval tests
uv run pytest tests/evals/

# Lint and format
uv run ruff check . && uv run ruff format .

# Type check
uv run pyright
```
