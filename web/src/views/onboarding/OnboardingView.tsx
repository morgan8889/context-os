import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { apiClient } from '@/lib/api/client';
import { viewStateKeys, graphKeys } from '@/lib/api/queryKeys';

// ── Demo dataset ─────────────────────────────────────────────────────────────

const DEMO_NODES = [
  // Goals
  { id: 'demo-goal-1', label: 'Q2 Revenue Growth', node_type: 'goal', status: 'active', owner_team: 'growth', actor_count: 4, risk_score: 0.35, autonomy_level: 2, edge_count: 5 },
  { id: 'demo-goal-2', label: 'Platform Reliability', node_type: 'goal', status: 'active', owner_team: 'platform', actor_count: 6, risk_score: 0.55, autonomy_level: 1, edge_count: 4 },
  { id: 'demo-goal-3', label: 'Developer Experience', node_type: 'goal', status: 'active', owner_team: 'core', actor_count: 3, risk_score: 0.2, autonomy_level: 2, edge_count: 3 },
  // Projects
  { id: 'demo-proj-1', label: 'Billing Redesign', node_type: 'project', status: 'active', owner_team: 'growth', actor_count: 3, risk_score: 0.4, autonomy_level: 2, edge_count: 3 },
  { id: 'demo-proj-2', label: 'API Gateway v2', node_type: 'project', status: 'active', owner_team: 'platform', actor_count: 5, risk_score: 0.65, autonomy_level: 3, edge_count: 5 },
  { id: 'demo-proj-3', label: 'CI/CD Overhaul', node_type: 'project', status: 'paused', owner_team: 'infra', actor_count: 2, risk_score: 0.3, autonomy_level: 1, edge_count: 2 },
  { id: 'demo-proj-4', label: 'Search Indexing', node_type: 'project', status: 'active', owner_team: 'core', actor_count: 4, risk_score: null, autonomy_level: 2, edge_count: 3 },
  { id: 'demo-proj-5', label: 'Pricing Engine', node_type: 'project', status: 'at_risk', owner_team: 'growth', actor_count: 3, risk_score: 0.78, autonomy_level: 2, edge_count: 4 },
  // Signals
  { id: 'demo-sig-1', label: 'Churn Rate Rising', node_type: 'signal', status: 'at_risk', owner_team: 'growth', actor_count: 1, risk_score: 0.82, autonomy_level: null, edge_count: 2 },
  { id: 'demo-sig-2', label: 'P95 Latency Spike', node_type: 'signal', status: 'at_risk', owner_team: 'platform', actor_count: 1, risk_score: 0.7, autonomy_level: null, edge_count: 3 },
  { id: 'demo-sig-3', label: 'Deploy Frequency Up', node_type: 'signal', status: 'active', owner_team: 'infra', actor_count: 1, risk_score: null, autonomy_level: null, edge_count: 1 },
  // Artifacts
  { id: 'demo-art-1', label: 'ADR: API Versioning', node_type: 'artifact', status: 'complete', owner_team: 'platform', actor_count: 2, risk_score: null, autonomy_level: null, edge_count: 2 },
  { id: 'demo-art-2', label: 'Q2 OKR Document', node_type: 'artifact', status: 'active', owner_team: 'growth', actor_count: 1, risk_score: null, autonomy_level: null, edge_count: 3 },
  { id: 'demo-art-3', label: 'Incident Report #42', node_type: 'artifact', status: 'complete', owner_team: 'platform', actor_count: 3, risk_score: null, autonomy_level: null, edge_count: 1 },
  { id: 'demo-art-4', label: 'Reliability Runbook', node_type: 'artifact', status: 'active', owner_team: 'infra', actor_count: 2, risk_score: null, autonomy_level: null, edge_count: 2 },
];

const DEMO_EDGES = [
  { id: 'de-1', source_id: 'demo-proj-1', target_id: 'demo-goal-1', edge_type: 'depends_on', weight: 0.9 },
  { id: 'de-2', source_id: 'demo-proj-5', target_id: 'demo-goal-1', edge_type: 'depends_on', weight: 0.8 },
  { id: 'de-3', source_id: 'demo-proj-2', target_id: 'demo-goal-2', edge_type: 'depends_on', weight: 0.9 },
  { id: 'de-4', source_id: 'demo-proj-3', target_id: 'demo-goal-3', edge_type: 'depends_on', weight: 0.7 },
  { id: 'de-5', source_id: 'demo-proj-4', target_id: 'demo-goal-3', edge_type: 'depends_on', weight: 0.8 },
  { id: 'de-6', source_id: 'demo-sig-1', target_id: 'demo-proj-5', edge_type: 'shared_work', weight: 0.6 },
  { id: 'de-7', source_id: 'demo-sig-2', target_id: 'demo-proj-2', edge_type: 'shared_work', weight: 0.7 },
  { id: 'de-8', source_id: 'demo-sig-3', target_id: 'demo-proj-3', edge_type: 'shared_work', weight: 0.5 },
  { id: 'de-9', source_id: 'demo-proj-1', target_id: 'demo-proj-5', edge_type: 'shared_actor', weight: 0.6 },
  { id: 'de-10', source_id: 'demo-art-1', target_id: 'demo-proj-2', edge_type: 'depends_on', weight: 0.8 },
  { id: 'de-11', source_id: 'demo-art-2', target_id: 'demo-goal-1', edge_type: 'depends_on', weight: 0.9 },
  { id: 'de-12', source_id: 'demo-art-3', target_id: 'demo-proj-2', edge_type: 'shared_work', weight: 0.5 },
  { id: 'de-13', source_id: 'demo-art-4', target_id: 'demo-proj-3', edge_type: 'depends_on', weight: 0.7 },
  { id: 'de-14', source_id: 'demo-proj-2', target_id: 'demo-proj-4', edge_type: 'shared_actor', weight: 0.4 },
  { id: 'de-15', source_id: 'demo-goal-2', target_id: 'demo-goal-1', edge_type: 'shared_work', weight: 0.3 },
  { id: 'de-16', source_id: 'demo-sig-1', target_id: 'demo-proj-1', edge_type: 'shared_work', weight: 0.5 },
  { id: 'de-17', source_id: 'demo-sig-2', target_id: 'demo-art-3', edge_type: 'shared_work', weight: 0.6 },
];

// ── Component ─────────────────────────────────────────────────────────────────

type SeedStatus = 'idle' | 'loading' | 'done' | 'error';

export default function OnboardingView() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<SeedStatus>('idle');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function handleLoadSampleData() {
    setStatus('loading');
    setErrorMsg(null);
    try {
      await apiClient.post('/api/v1/graph/nodes/seed', { nodes: DEMO_NODES });
      await apiClient.post('/api/v1/graph/edges/seed', { edges: DEMO_EDGES });

      // Invalidate view state + graph data so galaxy re-fetches immediately
      await queryClient.invalidateQueries({ queryKey: viewStateKeys.all });
      await queryClient.invalidateQueries({ queryKey: graphKeys.all });

      setStatus('done');
      // Brief pause so the user sees "done", then navigate
      setTimeout(() => navigate('/galaxy'), 600);
    } catch (err) {
      setStatus('error');
      setErrorMsg(err instanceof Error ? err.message : 'Seed request failed');
    }
  }

  return (
    <motion.div
      data-view="onboarding"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
      className="flex h-full w-full flex-col items-center justify-center"
      style={{ background: 'var(--color-galaxy-bg, oklch(8% 0 0))' }}
    >
      <div
        style={{
          maxWidth: 480,
          width: '100%',
          padding: '2.5rem',
          background: 'oklch(12% 0 0)',
          borderRadius: '0.75rem',
          border: '1px solid oklch(20% 0 0)',
        }}
      >
        <h1
          className="text-xl font-semibold mb-3"
          style={{ color: 'oklch(88% 0 0)' }}
        >
          Get started with Context-OS
        </h1>
        <p
          className="text-sm leading-relaxed mb-6"
          style={{ color: 'oklch(60% 0 0)' }}
        >
          Load a sample initiative graph to explore the Galaxy, Topology, and
          Decisions views. This creates 15 demo nodes and 17 edges in your
          workspace — goals, projects, signals, and artifacts connected by
          dependencies and shared work.
        </p>

        {status === 'error' && errorMsg && (
          <p
            className="text-sm mb-4 p-3 rounded"
            style={{
              color: 'oklch(70% 0.18 25)',
              background: 'oklch(15% 0.05 25)',
            }}
          >
            {errorMsg}
          </p>
        )}

        <button
          onClick={handleLoadSampleData}
          disabled={status === 'loading' || status === 'done'}
          className="w-full rounded-lg px-5 py-3 text-sm font-medium transition-colors"
          style={{
            background:
              status === 'done'
                ? 'oklch(45% 0.12 145)'
                : status === 'loading'
                  ? 'oklch(30% 0 0)'
                  : 'oklch(55% 0.2 250)',
            color: 'oklch(95% 0 0)',
            cursor: status === 'loading' || status === 'done' ? 'default' : 'pointer',
          }}
        >
          {status === 'loading'
            ? 'Loading sample data…'
            : status === 'done'
              ? 'Done — opening Galaxy'
              : 'Load sample data'}
        </button>

        {status === 'idle' && (
          <p className="text-xs mt-3 text-center" style={{ color: 'oklch(40% 0 0)' }}>
            Sample data is scoped to your workspace and can be cleared at any time.
          </p>
        )}
      </div>
    </motion.div>
  );
}
