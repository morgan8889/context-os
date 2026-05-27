# Contract Surface: Process Re-Architecture (Tier B — Deferred, Phase 6/7)

**Created**: 2026-05-22
**Status**: DEFERRED. This file records the *intended* contract surface for the
process re-architecture objective (US6–US9, FR-015–022) so the spec pack has no
coverage gap between its Tier B entities and its acceptance scenarios. **None of
these contracts are implemented in the Phase 5 build.** Final shapes (request/
response schemas, agent tool definitions, autonomy declarations, telemetry
attributes) belong to the dedicated Phase 6/7 `/speckit.plan`, which must clear
the Tier B Constitution Check first.

---

## Why this is a stub, not a contract

Per Constitution Principles III, V, and VI, any agent- or workflow-backed
endpoint must ship with: a declared autonomy level, a committed evaluation
suite, and OTEL-conformant telemetry. Defining concrete contracts here would
imply they are buildable from this pack; they are not. This stub enumerates the
surface and its governance obligations only.

## Intended endpoints (target — not built)

| Capability | Story | Indicative surface | Governance obligation |
|------------|-------|--------------------|-----------------------|
| Generate process baseline | US6 | `POST /api/v1/processes/{id}/baseline` → ProcessBaseline | Provenance to source signals (Principle II) |
| Pin baseline as anchor | US6 | `POST /api/v1/baselines/{id}/pin` | Immutable once pinned |
| Generate redesign proposal | US7 | `POST /api/v1/baselines/{id}/redesign` → ProcessBlueprint | Agent autonomy ≤2, approval-gated (Principle III) |
| Approve/reject redesign | US7 | `POST /api/v1/blueprints/{id}/decision` | Human authority; decision recorded with rationale |
| Generate implementation plan | US8 | `POST /api/v1/blueprints/{id}/plan` → ImplementationMilestone[] | Durable orchestration (Temporal/LangGraph) |
| Track milestone status | US8 | `GET /api/v1/plans/{id}/milestones` | Blocked milestones carry root-cause context |
| Operational monitoring | US9 | `GET /api/v1/processes/{id}/metrics` | Computed from OTEL traces (Principle VI) |
| Before/after KPI comparison | US9 | `GET /api/v1/processes/{id}/kpi-comparison` | Auditable baseline + post-change windows |
| Optimisation recommendations | US9 | `POST /api/v1/processes/{id}/optimisations` | Agent recommend-only; threshold-triggered |

## Required agent/eval/telemetry artifacts (target — not built)

- Eval suites for: baseline-inference agent, redesign-proposal agent,
  optimisation agent (golden inputs, failure modes, governance edge cases) —
  Principle V gate.
- Telemetry: each agent action emits `context_os.agent_identity`,
  `context_os.autonomy_level`, `context_os.governance_markers`, plus the
  process/blueprint id — Principle VI.
- Autonomy declarations per agent and per blueprint-defined step — Principle III.
