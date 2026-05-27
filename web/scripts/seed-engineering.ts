#!/usr/bin/env tsx
/**
 * seed-engineering.ts — Deterministic "Acme Platform Engineering" seed dataset.
 *
 * Seeds all three views with a coherent narrative:
 *   Galaxy:    40 nodes (3 goals, 12 initiatives, 15 projects, 10 signals) + 65 edges
 *   Topology:  6 workflows with real step labels and bottleneck data
 *   Decisions: 18 decisions with chronological arc, 3 superseded, 8 edges
 *
 * Usage:
 *   npm run seed:engineering
 *   tsx scripts/seed-engineering.ts --host http://localhost:8000
 */

import { parseArgs } from 'node:util';

// ── Types (match dev_router.py expectations) ───────────────────────────────

type NodeType = 'goal' | 'project' | 'signal' | 'artifact';
type NodeStatus = 'active' | 'paused' | 'complete' | 'at_risk';
type EdgeType = 'depends_on' | 'shared_actor' | 'shared_work';
type WorkflowStatus = 'healthy' | 'degraded' | 'blocked';
type StepStatus = 'active' | 'blocked' | 'complete' | 'pending';
type DecisionStatus = 'active' | 'superseded' | 'retracted';
type DecisionEdgeType = 'predecessor' | 'alternative' | 'dependent';

interface SeedNode {
  id: string;
  label: string;
  node_type: NodeType;
  status: NodeStatus;
  owner_team: string | null;
  actor_count: number;
  risk_score: number | null;
  autonomy_level: number | null;
  edge_count: number;
}

interface SeedEdge {
  id: string;
  source_id: string;
  target_id: string;
  edge_type: EdgeType;
  weight: number;
}

interface WorkflowStep {
  id: string;
  workflow_id: string;
  label: string;
  step_index: number;
  status: StepStatus;
  owner_team: string | null;
  owner_actor: string | null;
  autonomy_level: number;
  latency_p50_ms: number | null;
  latency_p95_ms: number | null;
}

interface WorkflowEdge {
  id: string;
  source_id: string;
  target_id: string;
  label: string | null;
}

interface Workflow {
  id: string;
  name: string;
  owner_team: string | null;
  status: WorkflowStatus;
  steps: WorkflowStep[];
  edges: WorkflowEdge[];
}

interface Decision {
  id: string;
  title: string;
  rationale: string;
  alternatives: Array<{ label: string; reason: string }>;
  author_id: string | null;
  author_name: string | null;
  captured_at: string;
  impacted_systems: string[];
  status: DecisionStatus;
}

interface DecisionEdge {
  id: string;
  source_id: string;
  target_id: string;
  edge_type: DecisionEdgeType;
}

// ── Galaxy: Nodes ──────────────────────────────────────────────────────────

const NODES: SeedNode[] = [
  // ── Goals (3) ────────────────────────────────────────────────────────────
  {
    id: 'goal-idp',
    label: 'Ship Internal Developer Platform v1',
    node_type: 'goal',
    status: 'active',
    owner_team: 'platform',
    actor_count: 22,
    risk_score: 0.35,
    autonomy_level: 1,
    edge_count: 8,
  },
  {
    id: 'goal-soc2',
    label: 'Achieve SOC2 Type II Certification',
    node_type: 'goal',
    status: 'active',
    owner_team: 'security',
    actor_count: 12,
    risk_score: 0.48,
    autonomy_level: null,
    edge_count: 5,
  },
  {
    id: 'goal-incidents',
    label: 'Reduce P1 Incident Rate 50% by Q3',
    node_type: 'goal',
    status: 'at_risk',
    owner_team: 'infra',
    actor_count: 18,
    risk_score: 0.71,
    autonomy_level: null,
    edge_count: 6,
  },

  // ── Initiatives (12, type=project so they cluster with their children) ───
  {
    id: 'init-api-gw',
    label: 'API Gateway Rewrite',
    node_type: 'project',
    status: 'active',
    owner_team: 'platform',
    actor_count: 7,
    risk_score: 0.42,
    autonomy_level: 2,
    edge_count: 7,
  },
  {
    id: 'init-auth',
    label: 'Auth Service Migration to Clerk',
    node_type: 'project',
    status: 'active',
    owner_team: 'platform',
    actor_count: 5,
    risk_score: 0.28,
    autonomy_level: 2,
    edge_count: 5,
  },
  {
    id: 'init-observability',
    label: 'Observability Stack Modernization',
    node_type: 'project',
    status: 'active',
    owner_team: 'infra',
    actor_count: 6,
    risk_score: 0.22,
    autonomy_level: 3,
    edge_count: 6,
  },
  {
    id: 'init-data-pipeline',
    label: 'Data Pipeline Reliability Hardening',
    node_type: 'project',
    status: 'at_risk',
    owner_team: 'data',
    actor_count: 4,
    risk_score: 0.79,
    autonomy_level: 2,
    edge_count: 3,
  },
  {
    id: 'init-idp',
    label: 'Developer Self-Service Portal',
    node_type: 'project',
    status: 'active',
    owner_team: 'platform',
    actor_count: 8,
    risk_score: 0.38,
    autonomy_level: 2,
    edge_count: 5,
  },
  {
    id: 'init-k8s',
    label: 'Kubernetes Migration',
    node_type: 'project',
    status: 'paused',
    owner_team: 'infra',
    actor_count: 5,
    risk_score: 0.55,
    autonomy_level: null,
    edge_count: 6,
  },
  {
    id: 'init-soc2-controls',
    label: 'SOC2 Technical Controls Implementation',
    node_type: 'project',
    status: 'active',
    owner_team: 'security',
    actor_count: 6,
    risk_score: 0.51,
    autonomy_level: 1,
    edge_count: 5,
  },
  {
    id: 'init-secrets',
    label: 'Secrets Management Overhaul',
    node_type: 'project',
    status: 'at_risk',
    owner_team: 'security',
    actor_count: 4,
    risk_score: 0.74,
    autonomy_level: null,
    edge_count: 4,
  },
  {
    id: 'init-cicd',
    label: 'CI/CD Pipeline Modernization',
    node_type: 'project',
    status: 'active',
    owner_team: 'platform',
    actor_count: 6,
    risk_score: 0.31,
    autonomy_level: 3,
    edge_count: 5,
  },
  {
    id: 'init-oncall',
    label: 'On-Call Experience Improvement',
    node_type: 'project',
    status: 'active',
    owner_team: 'infra',
    actor_count: 9,
    risk_score: 0.62,
    autonomy_level: 2,
    edge_count: 3,
  },
  {
    id: 'init-service-mesh',
    label: 'Service Mesh Evaluation',
    node_type: 'project',
    status: 'paused',
    owner_team: 'infra',
    actor_count: 3,
    risk_score: null,
    autonomy_level: null,
    edge_count: 3,
  },
  {
    id: 'init-cost',
    label: 'Cloud Cost Optimisation',
    node_type: 'project',
    status: 'active',
    owner_team: 'infra',
    actor_count: 5,
    risk_score: 0.44,
    autonomy_level: 3,
    edge_count: 3,
  },

  // ── Projects (15, type=artifact — sub-items within initiatives) ───────────
  {
    id: 'proj-api-gw-rate-limit',
    label: 'API Gateway: Rate Limiting Module',
    node_type: 'artifact',
    status: 'active',
    owner_team: 'platform',
    actor_count: 3,
    risk_score: 0.41,
    autonomy_level: 2,
    edge_count: 4,
  },
  {
    id: 'proj-api-gw-auth',
    label: 'API Gateway: Auth Passthrough Integration',
    node_type: 'artifact',
    status: 'complete',
    owner_team: 'platform',
    actor_count: 2,
    risk_score: null,
    autonomy_level: 2,
    edge_count: 2,
  },
  {
    id: 'proj-api-gw-tracing',
    label: 'API Gateway: Distributed Tracing',
    node_type: 'artifact',
    status: 'active',
    owner_team: 'platform',
    actor_count: 2,
    risk_score: 0.18,
    autonomy_level: 3,
    edge_count: 2,
  },
  {
    id: 'proj-auth-token',
    label: 'Auth: Token Refresh Service',
    node_type: 'artifact',
    status: 'active',
    owner_team: 'platform',
    actor_count: 2,
    risk_score: 0.25,
    autonomy_level: 2,
    edge_count: 3,
  },
  {
    id: 'proj-auth-mfa',
    label: 'Auth: MFA Enforcement Rollout',
    node_type: 'artifact',
    status: 'active',
    owner_team: 'platform',
    actor_count: 3,
    risk_score: 0.33,
    autonomy_level: null,
    edge_count: 2,
  },
  {
    id: 'proj-metrics-prometheus',
    label: 'Metrics: Prometheus Migration',
    node_type: 'artifact',
    status: 'complete',
    owner_team: 'infra',
    actor_count: 3,
    risk_score: null,
    autonomy_level: 3,
    edge_count: 3,
  },
  {
    id: 'proj-metrics-grafana',
    label: 'Metrics: Grafana Dashboard Library',
    node_type: 'artifact',
    status: 'active',
    owner_team: 'infra',
    actor_count: 2,
    risk_score: 0.12,
    autonomy_level: 2,
    edge_count: 2,
  },
  {
    id: 'proj-tracing-otel',
    label: 'Tracing: OpenTelemetry Rollout',
    node_type: 'artifact',
    status: 'active',
    owner_team: 'infra',
    actor_count: 4,
    risk_score: 0.21,
    autonomy_level: 3,
    edge_count: 3,
  },
  {
    id: 'proj-idp-catalog',
    label: 'IDP: Service Catalog',
    node_type: 'artifact',
    status: 'active',
    owner_team: 'platform',
    actor_count: 3,
    risk_score: 0.29,
    autonomy_level: 2,
    edge_count: 3,
  },
  {
    id: 'proj-idp-runbook',
    label: 'IDP: Runbook Automation',
    node_type: 'artifact',
    status: 'at_risk',
    owner_team: 'platform',
    actor_count: 2,
    risk_score: 0.61,
    autonomy_level: 4,
    edge_count: 3,
  },
  {
    id: 'proj-soc2-logging',
    label: 'SOC2: Audit Logging Pipeline',
    node_type: 'artifact',
    status: 'complete',
    owner_team: 'security',
    actor_count: 3,
    risk_score: null,
    autonomy_level: 3,
    edge_count: 2,
  },
  {
    id: 'proj-soc2-access',
    label: 'SOC2: Access Review Automation',
    node_type: 'artifact',
    status: 'active',
    owner_team: 'security',
    actor_count: 2,
    risk_score: 0.44,
    autonomy_level: 3,
    edge_count: 2,
  },
  {
    id: 'proj-cicd-cache',
    label: 'CI/CD: Build Cache Optimisation',
    node_type: 'artifact',
    status: 'active',
    owner_team: 'platform',
    actor_count: 2,
    risk_score: 0.19,
    autonomy_level: 3,
    edge_count: 3,
  },
  {
    id: 'proj-secrets-vault',
    label: 'Secrets: HashiCorp Vault Migration',
    node_type: 'artifact',
    status: 'at_risk',
    owner_team: 'security',
    actor_count: 3,
    risk_score: 0.77,
    autonomy_level: null,
    edge_count: 3,
  },
  {
    id: 'proj-k8s-staging',
    label: 'K8s: Staging Cluster Setup',
    node_type: 'artifact',
    status: 'paused',
    owner_team: 'infra',
    actor_count: 2,
    risk_score: 0.52,
    autonomy_level: null,
    edge_count: 2,
  },

  // ── Signals (10) ──────────────────────────────────────────────────────────
  {
    id: 'sig-api-latency',
    label: 'API latency regression: p99 up 40% in 7 days',
    node_type: 'signal',
    status: 'active',
    owner_team: null,
    actor_count: 1,
    risk_score: 0.87,
    autonomy_level: 5,
    edge_count: 2,
  },
  {
    id: 'sig-build-times',
    label: 'Build times increased: 4 min → 12 min',
    node_type: 'signal',
    status: 'active',
    owner_team: null,
    actor_count: 1,
    risk_score: 0.72,
    autonomy_level: 5,
    edge_count: 2,
  },
  {
    id: 'sig-oncall-fatigue',
    label: 'On-call fatigue: 3 engineers requested rotation change',
    node_type: 'signal',
    status: 'active',
    owner_team: null,
    actor_count: 1,
    risk_score: 0.65,
    autonomy_level: 4,
    edge_count: 1,
  },
  {
    id: 'sig-vault-blocked',
    label: 'Vault migration blocked: 2 legacy apps incompatible',
    node_type: 'signal',
    status: 'active',
    owner_team: null,
    actor_count: 1,
    risk_score: 0.78,
    autonomy_level: 4,
    edge_count: 2,
  },
  {
    id: 'sig-soc2-deadline',
    label: 'SOC2 audit scheduled Q3 — 6 weeks out',
    node_type: 'signal',
    status: 'active',
    owner_team: null,
    actor_count: 1,
    risk_score: 0.55,
    autonomy_level: 4,
    edge_count: 1,
  },
  {
    id: 'sig-idp-delay',
    label: 'IDP runbook automation: 2 sprint delays',
    node_type: 'signal',
    status: 'active',
    owner_team: null,
    actor_count: 1,
    risk_score: 0.61,
    autonomy_level: 4,
    edge_count: 1,
  },
  {
    id: 'sig-hire-ramp',
    label: 'New hire ramp time up 60% since team doubled',
    node_type: 'signal',
    status: 'active',
    owner_team: null,
    actor_count: 1,
    risk_score: 0.44,
    autonomy_level: 4,
    edge_count: 1,
  },
  {
    id: 'sig-data-sla',
    label: 'Data pipeline: 3 SLA breaches in 30 days',
    node_type: 'signal',
    status: 'active',
    owner_team: null,
    actor_count: 1,
    risk_score: 0.83,
    autonomy_level: 5,
    edge_count: 1,
  },
  {
    id: 'sig-k8s-gap',
    label: 'K8s migration paused: networking expertise gap',
    node_type: 'signal',
    status: 'active',
    owner_team: null,
    actor_count: 1,
    risk_score: 0.58,
    autonomy_level: 4,
    edge_count: 2,
  },
  {
    id: 'sig-aws-cost',
    label: 'AWS spend anomaly: +$45k/month unattributed',
    node_type: 'signal',
    status: 'active',
    owner_team: null,
    actor_count: 1,
    risk_score: 0.70,
    autonomy_level: 5,
    edge_count: 2,
  },
];

// ── Galaxy: Edges ──────────────────────────────────────────────────────────

function edge(id: string, source: string, target: string, type: EdgeType, weight = 0.8): SeedEdge {
  return { id, source_id: source, target_id: target, edge_type: type, weight };
}

const EDGES: SeedEdge[] = [
  // Goals → Initiatives
  edge('e-goal-idp-api-gw',       'goal-idp',       'init-api-gw',          'depends_on', 0.9),
  edge('e-goal-idp-auth',         'goal-idp',       'init-auth',            'depends_on', 0.9),
  edge('e-goal-idp-idp',          'goal-idp',       'init-idp',             'depends_on', 1.0),
  edge('e-goal-idp-cicd',         'goal-idp',       'init-cicd',            'depends_on', 0.8),
  edge('e-goal-idp-k8s',          'goal-idp',       'init-k8s',             'depends_on', 0.7),
  edge('e-goal-idp-cost',         'goal-idp',       'init-cost',            'depends_on', 0.5),
  edge('e-goal-soc2-controls',    'goal-soc2',      'init-soc2-controls',   'depends_on', 1.0),
  edge('e-goal-soc2-secrets',     'goal-soc2',      'init-secrets',         'depends_on', 0.9),
  edge('e-goal-soc2-cicd',        'goal-soc2',      'init-cicd',            'depends_on', 0.6),
  edge('e-goal-inc-obs',          'goal-incidents', 'init-observability',   'depends_on', 0.9),
  edge('e-goal-inc-oncall',       'goal-incidents', 'init-oncall',          'depends_on', 1.0),
  edge('e-goal-inc-data',         'goal-incidents', 'init-data-pipeline',   'depends_on', 0.8),
  edge('e-goal-inc-k8s',          'goal-incidents', 'init-k8s',             'depends_on', 0.6),

  // Initiatives → Projects
  edge('e-init-api-gw-rate',      'init-api-gw',    'proj-api-gw-rate-limit', 'depends_on', 0.9),
  edge('e-init-api-gw-auth',      'init-api-gw',    'proj-api-gw-auth',       'depends_on', 0.8),
  edge('e-init-api-gw-trace',     'init-api-gw',    'proj-api-gw-tracing',    'depends_on', 0.8),
  edge('e-init-auth-token',       'init-auth',      'proj-auth-token',         'depends_on', 0.9),
  edge('e-init-auth-mfa',         'init-auth',      'proj-auth-mfa',           'depends_on', 0.9),
  edge('e-init-obs-prom',         'init-observability', 'proj-metrics-prometheus', 'depends_on', 0.9),
  edge('e-init-obs-grafana',      'init-observability', 'proj-metrics-grafana',    'depends_on', 0.8),
  edge('e-init-obs-otel',         'init-observability', 'proj-tracing-otel',       'depends_on', 0.9),
  edge('e-init-idp-catalog',      'init-idp',       'proj-idp-catalog',        'depends_on', 0.9),
  edge('e-init-idp-runbook',      'init-idp',       'proj-idp-runbook',        'depends_on', 0.9),
  edge('e-init-soc2-log',         'init-soc2-controls', 'proj-soc2-logging',   'depends_on', 0.9),
  edge('e-init-soc2-access',      'init-soc2-controls', 'proj-soc2-access',    'depends_on', 0.9),
  edge('e-init-cicd-cache',       'init-cicd',      'proj-cicd-cache',         'depends_on', 0.9),
  edge('e-init-secrets-vault',    'init-secrets',   'proj-secrets-vault',      'depends_on', 1.0),
  edge('e-init-k8s-staging',      'init-k8s',       'proj-k8s-staging',        'depends_on', 0.9),

  // Cross-project dependencies
  edge('e-api-gw-auth-token',     'proj-api-gw-auth',    'proj-auth-token',         'shared_actor', 0.8),
  edge('e-api-gw-trace-otel',     'proj-api-gw-tracing', 'proj-tracing-otel',       'shared_actor', 0.7),
  edge('e-grafana-prom',          'proj-metrics-grafana','proj-metrics-prometheus',  'depends_on',   0.9),
  edge('e-otel-prom',             'proj-tracing-otel',   'proj-metrics-prometheus',  'shared_actor', 0.7),
  edge('e-auth-mfa-token',        'proj-auth-mfa',       'proj-auth-token',          'depends_on',   0.8),
  edge('e-soc2-access-log',       'proj-soc2-access',    'proj-soc2-logging',        'depends_on',   0.8),
  edge('e-k8s-cicd',              'proj-k8s-staging',    'proj-cicd-cache',          'depends_on',   0.6),
  edge('e-idp-catalog-rate',      'proj-idp-catalog',    'proj-api-gw-rate-limit',   'depends_on',   0.7),
  edge('e-cicd-k8s',              'init-cicd',           'init-k8s',                 'shared_work',  0.7),
  edge('e-mesh-k8s',              'init-service-mesh',   'init-k8s',                 'depends_on',   0.9),
  edge('e-mesh-obs',              'init-service-mesh',   'init-observability',        'shared_work',  0.6),
  edge('e-cost-k8s',              'init-cost',           'init-k8s',                 'depends_on',   0.7),

  // Signals → affected nodes
  edge('e-sig-latency-rate',      'sig-api-latency',  'proj-api-gw-rate-limit', 'shared_work', 0.9),
  edge('e-sig-latency-init',      'sig-api-latency',  'init-api-gw',            'shared_work', 0.9),
  edge('e-sig-build-cache',       'sig-build-times',  'proj-cicd-cache',        'shared_work', 0.9),
  edge('e-sig-build-cicd',        'sig-build-times',  'init-cicd',              'shared_work', 0.8),
  edge('e-sig-oncall-init',       'sig-oncall-fatigue','init-oncall',            'shared_work', 1.0),
  edge('e-sig-vault-proj',        'sig-vault-blocked', 'proj-secrets-vault',    'shared_work', 1.0),
  edge('e-sig-vault-init',        'sig-vault-blocked', 'init-secrets',          'shared_work', 0.9),
  edge('e-sig-soc2-init',         'sig-soc2-deadline', 'init-soc2-controls',    'shared_work', 0.9),
  edge('e-sig-idp-runbook',       'sig-idp-delay',    'proj-idp-runbook',       'shared_work', 1.0),
  edge('e-sig-hire-catalog',      'sig-hire-ramp',    'proj-idp-catalog',       'shared_work', 0.8),
  edge('e-sig-data-init',         'sig-data-sla',     'init-data-pipeline',     'shared_work', 1.0),
  edge('e-sig-k8s-staging',       'sig-k8s-gap',      'proj-k8s-staging',       'shared_work', 0.9),
  edge('e-sig-k8s-init',          'sig-k8s-gap',      'init-k8s',               'shared_work', 0.9),
  edge('e-sig-cost-init',         'sig-aws-cost',     'init-cost',              'shared_work', 0.9),
  edge('e-sig-cost-k8s',          'sig-aws-cost',     'init-k8s',               'shared_work', 0.6),
];

// ── Workflows ──────────────────────────────────────────────────────────────

function buildSteps(
  workflowId: string,
  defs: Array<{
    label: string;
    status: StepStatus;
    team: string | null;
    actor: string | null;
    autonomy: number;
    p50: number | null;
    p95: number | null;
  }>
): { steps: WorkflowStep[]; edges: WorkflowEdge[] } {
  const steps: WorkflowStep[] = defs.map((d, i) => ({
    id: `${workflowId}-s${i}`,
    workflow_id: workflowId,
    label: d.label,
    step_index: i,
    status: d.status,
    owner_team: d.team,
    owner_actor: d.actor,
    autonomy_level: d.autonomy,
    latency_p50_ms: d.p50,
    latency_p95_ms: d.p95,
  }));

  const edges: WorkflowEdge[] = steps.slice(0, -1).map((s, i) => ({
    id: `${workflowId}-e${i}`,
    source_id: s.id,
    target_id: steps[i + 1]!.id,
    label: null,
  }));

  return { steps, edges };
}

const wf1 = buildSteps('wf-deploy-gate', [
  { label: 'Code Review (2 approvers)',  status: 'complete', team: 'platform', actor: 'priya',   autonomy: 0, p50: 180,  p95: 420  },
  { label: 'Security Scan',             status: 'complete', team: 'security', actor: null,      autonomy: 5, p50: 45,   p95: 110  },
  { label: 'Load Test',                 status: 'active',   team: 'infra',    actor: 'james',   autonomy: 4, p50: 480,  p95: 1800 },
  { label: 'Canary Deploy (5%)',         status: 'pending',  team: 'platform', actor: null,      autonomy: 3, p50: 90,   p95: 200  },
  { label: 'Promote to Production',     status: 'pending',  team: 'platform', actor: 'priya',   autonomy: 1, p50: 30,   p95: 80   },
  { label: 'Monitor — 15 min window',   status: 'pending',  team: 'infra',    actor: null,      autonomy: 5, p50: 900,  p95: 900  },
]);

const wf2 = buildSteps('wf-incident-p1', [
  { label: 'Alert Fires (PagerDuty)',    status: 'complete', team: 'infra',    actor: null,      autonomy: 5, p50: 0,    p95: 0    },
  { label: 'On-Call Acknowledges',       status: 'complete', team: 'infra',    actor: 'daniel',  autonomy: 0, p50: 120,  p95: 480  },
  { label: 'Diagnose & Escalate',        status: 'active',   team: 'infra',    actor: 'daniel',  autonomy: 2, p50: 300,  p95: 900  },
  { label: 'Mitigate or Rollback',       status: 'pending',  team: 'platform', actor: null,      autonomy: 2, p50: 240,  p95: 600  },
  { label: 'Post-Mortem Draft',          status: 'pending',  team: 'infra',    actor: 'mei-lin', autonomy: 3, p50: 1800, p95: 3600 },
]);

const wf3 = buildSteps('wf-rfc-review', [
  { label: 'RFC Drafted',               status: 'complete', team: 'platform', actor: 'sofia',   autonomy: 1, p50: null, p95: null },
  { label: 'Architecture Review',       status: 'complete', team: 'platform', actor: null,      autonomy: 0, p50: 240,  p95: 480  },
  { label: 'Security Sign-Off',         status: 'active',   team: 'security', actor: 'james',   autonomy: 0, p50: 360,  p95: 480  },
  { label: 'Stakeholder Approval',      status: 'pending',  team: null,       actor: null,      autonomy: 0, p50: 720,  p95: 1440 },
  { label: 'Implementation Kickoff',    status: 'pending',  team: 'platform', actor: 'sofia',   autonomy: 0, p50: null, p95: null },
]);

const wf4 = buildSteps('wf-new-hire', [
  { label: 'Account Provisioning',      status: 'complete', team: 'platform', actor: null,      autonomy: 4, p50: 30,   p95: 60   },
  { label: 'Tooling Access (JIRA, GitHub, Slack)', status: 'blocked', team: 'platform', actor: 'priya', autonomy: 2, p50: 480, p95: 2400 },
  { label: 'Dev Environment Setup',     status: 'pending',  team: 'platform', actor: null,      autonomy: 3, p50: 120,  p95: 300  },
  { label: 'Codebase Walkthrough',      status: 'pending',  team: null,       actor: 'sofia',   autonomy: 0, p50: null, p95: null },
  { label: 'First PR Review',           status: 'pending',  team: null,       actor: 'james',   autonomy: 0, p50: null, p95: null },
  { label: 'Team Retro Check-In',       status: 'pending',  team: null,       actor: null,      autonomy: 0, p50: null, p95: null },
]);

const wf5 = buildSteps('wf-security-review', [
  { label: 'Dependency Audit',          status: 'complete', team: 'security', actor: null,      autonomy: 5, p50: 60,   p95: 120  },
  { label: 'Access Review',             status: 'active',   team: 'security', actor: 'james',   autonomy: 3, p50: 480,  p95: 720  },
  { label: 'Pen Test Report Review',    status: 'pending',  team: 'security', actor: null,      autonomy: 1, p50: 1440, p95: 2880 },
  { label: 'Remediation Sign-Off',      status: 'pending',  team: 'security', actor: 'james',   autonomy: 0, p50: 360,  p95: 480  },
]);

const wf6 = buildSteps('wf-oncall-handoff', [
  { label: 'Outgoing Engineer Summary', status: 'complete', team: 'infra',    actor: 'daniel',  autonomy: 1, p50: null, p95: null },
  { label: 'Runbook Update',            status: 'blocked',  team: 'infra',    actor: 'mei-lin', autonomy: 2, p50: 480,  p95: 1200 },
  { label: 'Incoming Engineer Briefing',status: 'pending',  team: 'infra',    actor: null,      autonomy: 0, p50: null, p95: null },
  { label: 'Shadow On-Call (2 hrs)',    status: 'pending',  team: 'infra',    actor: null,      autonomy: 0, p50: 7200, p95: 7200 },
]);

const WORKFLOWS: Workflow[] = [
  { id: 'wf-deploy-gate',   name: 'Production Deploy Gate',     owner_team: 'platform', status: 'healthy',  ...wf1 },
  { id: 'wf-incident-p1',   name: 'P1 Incident Response',       owner_team: 'infra',    status: 'degraded', ...wf2 },
  { id: 'wf-rfc-review',    name: 'RFC / Design Review Process', owner_team: 'platform', status: 'healthy',  ...wf3 },
  { id: 'wf-new-hire',      name: 'New Engineer Onboarding',     owner_team: 'platform', status: 'degraded', ...wf4 },
  { id: 'wf-security-review',name: 'Quarterly Security Review',  owner_team: 'security', status: 'healthy',  ...wf5 },
  { id: 'wf-oncall-handoff', name: 'On-Call Handoff Protocol',   owner_team: 'infra',    status: 'degraded', ...wf6 },
];

// ── Decisions ──────────────────────────────────────────────────────────────

const DECISIONS: Decision[] = [
  {
    id: 'dec-postgres',
    title: 'Adopt PostgreSQL as primary datastore',
    rationale: 'Chosen for mature ecosystem, native JSONB support, pgvector extension for embeddings, and Apache AGE for graph queries — a single physical store avoids operational complexity of polyglot persistence.',
    alternatives: [
      { label: 'MySQL', reason: 'Lacks JSONB and vector extension ecosystem.' },
      { label: 'MongoDB', reason: 'Schema flexibility not required; ACID transactions are.' },
      { label: 'CockroachDB', reason: 'Distributed overhead not justified at current scale.' },
    ],
    author_id: 'usr-priya', author_name: 'Priya Raghavan',
    captured_at: '2022-02-14T10:00:00Z',
    impacted_systems: ['api-gateway', 'auth-service', 'graph-module', 'vector-module'],
    status: 'active',
  },
  {
    id: 'dec-datadog',
    title: 'Use DataDog for all observability',
    rationale: 'Initially selected for its out-of-the-box dashboards and APM integration. Superseded after vendor lock-in costs scaled disproportionately and OpenTelemetry became production-ready.',
    alternatives: [
      { label: 'New Relic', reason: 'Similar pricing model and lock-in risk.' },
      { label: 'Custom logging only', reason: 'Insufficient for distributed trace correlation.' },
    ],
    author_id: 'usr-james', author_name: 'James Okafor',
    captured_at: '2022-03-20T09:00:00Z',
    impacted_systems: ['observability', 'api-gateway', 'agent-runtime'],
    status: 'superseded',
  },
  {
    id: 'dec-python312',
    title: 'Standardize on Python 3.12 across services',
    rationale: 'Python 3.12 delivers measurable asyncio performance improvements and unlocks modern type hint syntax (PEP 695). Standardizing eliminates version drift across services.',
    alternatives: [
      { label: 'Python 3.11', reason: 'Stable but misses 3.12 performance and type improvements.' },
      { label: 'Go', reason: 'Better runtime performance but slower ML/AI ecosystem.' },
    ],
    author_id: 'usr-sofia', author_name: 'Sofia Marchetti',
    captured_at: '2022-06-01T11:00:00Z',
    impacted_systems: ['api-gateway', 'auth-service', 'agent-runtime', 'ingestion-pipeline'],
    status: 'active',
  },
  {
    id: 'dec-ecs',
    title: 'Deploy on AWS ECS Fargate',
    rationale: 'ECS Fargate selected for its serverless container model and zero cluster management overhead at early stage. Superseded as team grew and workload scheduling requirements exceeded ECS capabilities.',
    alternatives: [
      { label: 'EC2 with manual Docker', reason: 'Too much operational overhead for small team.' },
      { label: 'Kubernetes (early)', reason: 'Operational complexity not justified at the time.' },
    ],
    author_id: 'usr-daniel', author_name: 'Daniel Svensson',
    captured_at: '2022-09-15T14:00:00Z',
    impacted_systems: ['api-gateway', 'auth-service', 'agent-runtime', 'ingestion-pipeline'],
    status: 'superseded',
  },
  {
    id: 'dec-custom-auth',
    title: 'Build custom authentication service',
    rationale: 'Initially built in-house to maintain full control over JWT claims and org tenancy model. Superseded after audit revealed session management gaps and Clerk matured to support all required features natively.',
    alternatives: [
      { label: 'Auth0', reason: 'Good DX but expensive at scale and limited custom claim flexibility.' },
      { label: 'Firebase Auth', reason: 'Google lock-in; lacks org/tenant model required for B2B.' },
    ],
    author_id: 'usr-priya', author_name: 'Priya Raghavan',
    captured_at: '2023-01-10T10:00:00Z',
    impacted_systems: ['auth-service', 'api-gateway'],
    status: 'superseded',
  },
  {
    id: 'dec-fastapi',
    title: 'Use FastAPI for all new HTTP services',
    rationale: 'FastAPI provides async-native request handling, automatic OpenAPI generation, and Pydantic validation — eliminating boilerplate while keeping type safety. Lifespan context manager integrates cleanly with async DB pools.',
    alternatives: [
      { label: 'Flask', reason: 'Synchronous by default; requires manual OpenAPI.' },
      { label: 'Django REST', reason: 'Heavyweight; ORM assumptions conflict with SQLAlchemy async.' },
    ],
    author_id: 'usr-sofia', author_name: 'Sofia Marchetti',
    captured_at: '2023-02-22T09:00:00Z',
    impacted_systems: ['api-gateway', 'auth-service', 'agent-runtime'],
    status: 'active',
  },
  {
    id: 'dec-clerk',
    title: 'Adopt Clerk for authentication across services',
    rationale: 'Clerk provides JWT RS256 with per-organization claims out of the box, eliminating the security debt of the custom auth service. The platform_operator custom claim supports our admin access model without additional infrastructure.',
    alternatives: [
      { label: 'Continue custom auth', reason: 'Audit revealed session management gaps too costly to remediate.' },
      { label: 'Auth0', reason: 'Org/tenant model required custom extension points not available at our tier.' },
    ],
    author_id: 'usr-priya', author_name: 'Priya Raghavan',
    captured_at: '2023-04-05T11:00:00Z',
    impacted_systems: ['auth-service', 'api-gateway', 'web-frontend'],
    status: 'active',
  },
  {
    id: 'dec-otel',
    title: 'Use OpenTelemetry for all telemetry',
    rationale: 'OpenTelemetry is now CNCF stable for traces and metrics. Switching from DataDog eliminates $180k/year vendor spend and achieves the Observable Autonomy principle with vendor-neutral span export to Langfuse and Prometheus.',
    alternatives: [
      { label: 'Keep DataDog', reason: 'Costs scaling disproportionately; agent licensing per-host model hostile to K8s.' },
      { label: 'Jaeger only', reason: 'Traces only; no metrics or logs standard.' },
    ],
    author_id: 'usr-james', author_name: 'James Okafor',
    captured_at: '2023-06-18T10:00:00Z',
    impacted_systems: ['observability', 'api-gateway', 'agent-runtime', 'ingestion-pipeline'],
    status: 'active',
  },
  {
    id: 'dec-age',
    title: 'Use Apache AGE for graph queries in Postgres',
    rationale: 'AGE enables Cypher-based pattern matching directly inside Postgres without a separate graph database. Combined with pgvector, a single Postgres instance covers relational, vector, and graph workloads in the MVP.',
    alternatives: [
      { label: 'Neo4j', reason: 'Separate operational cluster; licensing costs; breaks single-store constraint.' },
      { label: 'Pure SQL recursive CTEs', reason: 'Performant but extremely verbose for deep traversal queries.' },
    ],
    author_id: 'usr-mei-lin', author_name: 'Mei-Lin Chen',
    captured_at: '2023-08-30T14:00:00Z',
    impacted_systems: ['graph-module', 'api-gateway'],
    status: 'active',
  },
  {
    id: 'dec-k8s',
    title: 'Migrate container orchestration to Kubernetes',
    rationale: 'ECS Fargate task scheduling cannot express the workload affinity and resource reservation requirements of the agent runtime. Kubernetes enables GPU node pools for eval workloads and better cost attribution via namespace resource quotas.',
    alternatives: [
      { label: 'Stay on ECS', reason: 'Simpler but cannot express GPU node affinity or fine-grained resource policies.' },
      { label: 'Nomad', reason: 'Better ergonomics but narrower ecosystem for our ML toolchain.' },
    ],
    author_id: 'usr-daniel', author_name: 'Daniel Svensson',
    captured_at: '2023-10-12T09:00:00Z',
    impacted_systems: ['api-gateway', 'agent-runtime', 'ingestion-pipeline', 'eval-runner'],
    status: 'active',
  },
  {
    id: 'dec-hnsw',
    title: 'Implement HNSW indexes for vector similarity search',
    rationale: 'HNSW achieves sub-millisecond approximate nearest-neighbour search at our query volume. pgvector 0.7 supports HNSW natively, keeping vector search inside the single Postgres store.',
    alternatives: [
      { label: 'IVFFlat', reason: 'Faster build but lower recall at equivalent ef_search.' },
      { label: 'Pinecone', reason: 'External managed service; violates single-store principle.' },
    ],
    author_id: 'usr-mei-lin', author_name: 'Mei-Lin Chen',
    captured_at: '2023-11-05T10:00:00Z',
    impacted_systems: ['vector-module', 'agent-runtime'],
    status: 'active',
  },
  {
    id: 'dec-langgraph',
    title: 'Use LangGraph for multi-step agent workflows',
    rationale: 'LangGraph provides durable, resumable workflow execution with AsyncPostgresSaver, interrupt_before for human-in-the-loop gates, and explicit state typing. This satisfies the Human Governance principle without custom orchestration code.',
    alternatives: [
      { label: 'Temporal', reason: 'More mature but Java-centric SDK; Python SDK lagging.' },
      { label: 'Custom async state machine', reason: 'Full control but re-invents persistence and replay semantics.' },
    ],
    author_id: 'usr-sofia', author_name: 'Sofia Marchetti',
    captured_at: '2023-12-01T11:00:00Z',
    impacted_systems: ['agent-runtime', 'workflow-engine'],
    status: 'active',
  },
  {
    id: 'dec-react19',
    title: 'Adopt React 19 + Vite for the web workspace',
    rationale: 'React 19 concurrent rendering reduces waterfall patterns in data-heavy views. Vite 6 provides the fastest local dev experience and shares the transform pipeline with Vitest, eliminating Jest configuration complexity.',
    alternatives: [
      { label: 'Next.js', reason: 'SSR incompatible with WebGL Sigma.js renderer.' },
      { label: 'Remix', reason: 'Same SSR conflict; file-system routing too opinionated for SPA.' },
    ],
    author_id: 'usr-priya', author_name: 'Priya Raghavan',
    captured_at: '2024-01-15T10:00:00Z',
    impacted_systems: ['web-frontend'],
    status: 'active',
  },
  {
    id: 'dec-api-freeze',
    title: 'Freeze public API contracts before GA',
    rationale: 'Premature API changes during closed beta would break integrations for the 12 early-access customers. All breaking changes must go through a deprecation cycle with 90-day notice.',
    alternatives: [
      { label: 'Versioned endpoints only', reason: 'Allows evolution but increases surface area and documentation burden.' },
    ],
    author_id: 'usr-james', author_name: 'James Okafor',
    captured_at: '2024-02-20T14:00:00Z',
    impacted_systems: ['api-gateway'],
    status: 'active',
  },
  {
    id: 'dec-two-approvers',
    title: 'Require two approvers for production deploys',
    rationale: 'Incident post-mortem from Q4 found that 60% of P1s traced to single-reviewer deploys. Requiring a second approver adds 20 minutes to cycle time but reduces blast radius from unreviewed changes.',
    alternatives: [
      { label: 'Single reviewer', reason: 'Faster but incident data shows increased defect escape rate.' },
      { label: 'Automated approval for green CI', reason: 'Removes human check; conflicts with SOC2 change management requirement.' },
    ],
    author_id: 'usr-daniel', author_name: 'Daniel Svensson',
    captured_at: '2024-03-08T09:00:00Z',
    impacted_systems: ['api-gateway', 'auth-service', 'agent-runtime'],
    status: 'active',
  },
  {
    id: 'dec-ruff',
    title: 'Enforce Ruff as sole Python linter and formatter',
    rationale: 'Ruff replaces flake8 + isort + black with a single Rust-based tool that runs 10-100× faster. Single-tool configuration reduces CI complexity and eliminates the flake8/black conflict over line length.',
    alternatives: [
      { label: 'Keep flake8 + black', reason: 'Familiar but slow; config conflicts require per-repo overrides.' },
      { label: 'Pylint', reason: 'More comprehensive but 50× slower; too noisy for pre-commit.' },
    ],
    author_id: 'usr-sofia', author_name: 'Sofia Marchetti',
    captured_at: '2024-04-02T10:00:00Z',
    impacted_systems: ['api-gateway', 'auth-service', 'agent-runtime', 'ingestion-pipeline', 'eval-runner'],
    status: 'active',
  },
  {
    id: 'dec-alembic',
    title: 'Use Alembic for all database migrations',
    rationale: 'Alembic auto-generates reviewable migration files version-controlled alongside application code. The async-compatible API integrates with SQLAlchemy 2.0 without blocking the event loop.',
    alternatives: [
      { label: 'Flyway', reason: 'Java-centric; Python SDK limited.' },
      { label: 'Manual DDL scripts', reason: 'Error-prone; no rollback semantics.' },
    ],
    author_id: 'usr-mei-lin', author_name: 'Mei-Lin Chen',
    captured_at: '2024-05-14T11:00:00Z',
    impacted_systems: ['api-gateway', 'auth-service', 'agent-runtime'],
    status: 'active',
  },
  {
    id: 'dec-prometheus',
    title: 'Adopt Prometheus + Grafana for the metrics stack',
    rationale: 'Prometheus scrape-based model pairs naturally with the OTEL Collector and keeps metrics self-hosted, satisfying data residency requirements. Grafana dashboards are version-controlled as JSON and provisioned automatically.',
    alternatives: [
      { label: 'InfluxDB + Chronograf', reason: 'Push-based model harder to integrate with OTEL Collector.' },
      { label: 'DataDog metrics', reason: 'Already superseded as primary observability vendor.' },
    ],
    author_id: 'usr-james', author_name: 'James Okafor',
    captured_at: '2024-06-03T09:00:00Z',
    impacted_systems: ['observability', 'api-gateway', 'agent-runtime', 'ingestion-pipeline'],
    status: 'active',
  },
];

const DECISION_EDGES: DecisionEdge[] = [
  // Supersession chains
  { id: 'de-datadog-otel',        source_id: 'dec-datadog',      target_id: 'dec-otel',       edge_type: 'predecessor' },
  { id: 'de-ecs-k8s',             source_id: 'dec-ecs',          target_id: 'dec-k8s',        edge_type: 'predecessor' },
  { id: 'de-custom-auth-clerk',   source_id: 'dec-custom-auth',  target_id: 'dec-clerk',      edge_type: 'predecessor' },
  // Technical dependencies
  { id: 'de-postgres-age',        source_id: 'dec-postgres',     target_id: 'dec-age',        edge_type: 'dependent'   },
  { id: 'de-postgres-hnsw',       source_id: 'dec-postgres',     target_id: 'dec-hnsw',       edge_type: 'dependent'   },
  { id: 'de-fastapi-clerk',       source_id: 'dec-fastapi',      target_id: 'dec-clerk',      edge_type: 'dependent'   },
  { id: 'de-otel-prometheus',     source_id: 'dec-otel',         target_id: 'dec-prometheus', edge_type: 'dependent'   },
  { id: 'de-k8s-prometheus',      source_id: 'dec-k8s',          target_id: 'dec-prometheus', edge_type: 'dependent'   },
];

// ── HTTP helper ────────────────────────────────────────────────────────────

async function post(url: string, body: unknown): Promise<void> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '(no body)');
    throw new Error(`POST ${url} → ${res.status} ${res.statusText}\n${text}`);
  }
}

// ── Main ───────────────────────────────────────────────────────────────────

async function main() {
  const { values } = parseArgs({
    options: { host: { type: 'string', default: 'http://localhost:8000' } },
    strict: false,
  });
  const host = values.host as string;

  console.log(`[seed-engineering] Seeding against ${host}\n`);

  // 1. Galaxy nodes
  await post(`${host}/api/v1/graph/nodes/seed`, { nodes: NODES });
  console.log(`  Galaxy nodes   : ${NODES.length}`);

  // 2. Galaxy edges
  await post(`${host}/api/v1/graph/edges/seed`, { edges: EDGES });
  console.log(`  Galaxy edges   : ${EDGES.length}`);

  // 3. Workflows
  await post(`${host}/api/v1/graph/seed`, { workflows: WORKFLOWS, view_state: 'activated' });
  const totalSteps = WORKFLOWS.reduce((n, w) => n + w.steps.length, 0);
  console.log(`  Workflows      : ${WORKFLOWS.length}  (${totalSteps} steps)`);

  // 4. Decisions
  await post(`${host}/api/v1/dev/seed-decisions`, {
    decisions: DECISIONS,
    edges: DECISION_EDGES,
    view_state: 'activated',
  });
  console.log(`  Decisions      : ${DECISIONS.length}  (${DECISION_EDGES.length} edges)`);

  const bottlenecks = WORKFLOWS.flatMap((w) => w.steps).filter((s) => (s.latency_p95_ms ?? 0) > 500);
  const blocked     = WORKFLOWS.flatMap((w) => w.steps).filter((s) => s.status === 'blocked');
  const atRisk      = NODES.filter((n) => n.status === 'at_risk');
  const superseded  = DECISIONS.filter((d) => d.status === 'superseded');

  console.log(`\n  At-risk nodes  : ${atRisk.length}`);
  console.log(`  Bottleneck steps: ${bottlenecks.length}`);
  console.log(`  Blocked steps  : ${blocked.length}`);
  console.log(`  Superseded decisions: ${superseded.length}`);
  console.log(`\n[seed-engineering] Done ✓  →  http://localhost:5173`);
}

main().catch((err) => {
  console.error('[seed-engineering] Failed:', err instanceof Error ? err.message : err);
  process.exit(1);
});
