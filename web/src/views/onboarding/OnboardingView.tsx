import { useState, type CSSProperties, type ChangeEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { apiClient } from '@/lib/api/client';
import { viewStateKeys, graphKeys } from '@/lib/api/queryKeys';

// ── Demo dataset ─────────────────────────────────────────────────────────────

const DEMO_NODES = [
  { id: 'demo-goal-1', label: 'Q2 Revenue Growth', node_type: 'goal', status: 'active', owner_team: 'growth', actor_count: 4, risk_score: 0.35, autonomy_level: 2, edge_count: 5 },
  { id: 'demo-goal-2', label: 'Platform Reliability', node_type: 'goal', status: 'active', owner_team: 'platform', actor_count: 6, risk_score: 0.55, autonomy_level: 1, edge_count: 4 },
  { id: 'demo-goal-3', label: 'Developer Experience', node_type: 'goal', status: 'active', owner_team: 'core', actor_count: 3, risk_score: 0.2, autonomy_level: 2, edge_count: 3 },
  { id: 'demo-proj-1', label: 'Billing Redesign', node_type: 'project', status: 'active', owner_team: 'growth', actor_count: 3, risk_score: 0.4, autonomy_level: 2, edge_count: 3 },
  { id: 'demo-proj-2', label: 'API Gateway v2', node_type: 'project', status: 'active', owner_team: 'platform', actor_count: 5, risk_score: 0.65, autonomy_level: 3, edge_count: 5 },
  { id: 'demo-proj-3', label: 'CI/CD Overhaul', node_type: 'project', status: 'paused', owner_team: 'infra', actor_count: 2, risk_score: 0.3, autonomy_level: 1, edge_count: 2 },
  { id: 'demo-proj-4', label: 'Search Indexing', node_type: 'project', status: 'active', owner_team: 'core', actor_count: 4, risk_score: null, autonomy_level: 2, edge_count: 3 },
  { id: 'demo-proj-5', label: 'Pricing Engine', node_type: 'project', status: 'at_risk', owner_team: 'growth', actor_count: 3, risk_score: 0.78, autonomy_level: 2, edge_count: 4 },
  { id: 'demo-sig-1', label: 'Churn Rate Rising', node_type: 'signal', status: 'at_risk', owner_team: 'growth', actor_count: 1, risk_score: 0.82, autonomy_level: null, edge_count: 2 },
  { id: 'demo-sig-2', label: 'P95 Latency Spike', node_type: 'signal', status: 'at_risk', owner_team: 'platform', actor_count: 1, risk_score: 0.7, autonomy_level: null, edge_count: 3 },
  { id: 'demo-sig-3', label: 'Deploy Frequency Up', node_type: 'signal', status: 'active', owner_team: 'infra', actor_count: 1, risk_score: null, autonomy_level: null, edge_count: 1 },
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

// ── Shared styles ─────────────────────────────────────────────────────────────

const card: CSSProperties = {
  maxWidth: 520,
  width: '100%',
  padding: '2.5rem',
  background: 'oklch(12% 0 0)',
  borderRadius: '0.75rem',
  border: '1px solid oklch(20% 0 0)',
};

// ── GitHub connect tab ────────────────────────────────────────────────────────

type GitHubStatus = 'idle' | 'connecting' | 'ingesting' | 'done' | 'error';

function GitHubConnectTab() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [pat, setPat] = useState('');
  const [ghStatus, setGhStatus] = useState<GitHubStatus>('idle');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function handleConnect() {
    if (!pat.trim()) return;
    setGhStatus('connecting');
    setErrorMsg(null);

    try {
      // Store the PAT
      await apiClient.post('/api/v1/admin/integrations/github/connect', {
        token: pat.trim(),
      });

      // Trigger ingest
      setGhStatus('ingesting');
      await apiClient.post('/api/v1/ingest/github', {});

      // Invalidate caches so the galaxy re-fetches
      await queryClient.invalidateQueries({ queryKey: viewStateKeys.all });
      await queryClient.invalidateQueries({ queryKey: graphKeys.all });

      setGhStatus('done');
      setTimeout(() => navigate('/galaxy'), 800);
    } catch (err) {
      setGhStatus('error');
      setErrorMsg(err instanceof Error ? err.message : 'Connection failed');
    }
  }

  const busy = ghStatus === 'connecting' || ghStatus === 'ingesting';

  return (
    <div style={card}>
      <h1 className="text-xl font-semibold mb-2" style={{ color: 'oklch(88% 0 0)' }}>
        Connect GitHub
      </h1>
      <p className="text-sm leading-relaxed mb-5" style={{ color: 'oklch(60% 0 0)' }}>
        Create a{' '}
        <span style={{ color: 'oklch(70% 0.15 250)' }}>
          Personal Access Token
        </span>{' '}
        at github.com/settings/tokens with <strong style={{ color: 'oklch(75% 0 0)' }}>repo:read</strong> scope,
        then paste it below. Your repos, milestones, and issues will appear as
        nodes in the Galaxy.
      </p>

      {ghStatus === 'error' && errorMsg && (
        <p
          className="text-sm mb-4 p-3 rounded"
          style={{ color: 'oklch(70% 0.18 25)', background: 'oklch(15% 0.05 25)' }}
        >
          {errorMsg}
        </p>
      )}

      <input
        type="password"
        placeholder="ghp_••••••••••••••••••••••••••••••••••••"
        value={pat}
        onChange={(e: ChangeEvent<HTMLInputElement>) => setPat(e.target.value)}
        disabled={busy || ghStatus === 'done'}
        className="w-full rounded-lg border px-3 py-2.5 text-sm mb-4 focus-visible:outline-none focus-visible:ring-2"
        style={{
          background: 'oklch(9% 0 0)',
          borderColor: 'oklch(25% 0 0)',
          color: 'oklch(85% 0 0)',
        }}
      />

      <button
        onClick={handleConnect}
        disabled={busy || ghStatus === 'done' || !pat.trim()}
        className="w-full rounded-lg px-5 py-3 text-sm font-medium transition-colors"
        style={{
          background:
            ghStatus === 'done'
              ? 'oklch(45% 0.12 145)'
              : busy
                ? 'oklch(30% 0 0)'
                : !pat.trim()
                  ? 'oklch(30% 0 0)'
                  : 'oklch(55% 0.2 250)',
          color: !pat.trim() ? 'oklch(50% 0 0)' : 'oklch(95% 0 0)',
          cursor: busy || ghStatus === 'done' || !pat.trim() ? 'default' : 'pointer',
        }}
      >
        {ghStatus === 'connecting'
          ? 'Connecting…'
          : ghStatus === 'ingesting'
            ? 'Syncing your repos…'
            : ghStatus === 'done'
              ? 'Done — opening Galaxy'
              : 'Connect GitHub'}
      </button>
    </div>
  );
}

// ── Sample data tab ───────────────────────────────────────────────────────────

type SeedStatus = 'idle' | 'loading' | 'done' | 'error';

function SampleDataTab() {
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
      await queryClient.invalidateQueries({ queryKey: viewStateKeys.all });
      await queryClient.invalidateQueries({ queryKey: graphKeys.all });
      setStatus('done');
      setTimeout(() => navigate('/galaxy'), 600);
    } catch (err) {
      setStatus('error');
      setErrorMsg(err instanceof Error ? err.message : 'Seed request failed');
    }
  }

  return (
    <div style={card}>
      <h1 className="text-xl font-semibold mb-3" style={{ color: 'oklch(88% 0 0)' }}>
        Load sample data
      </h1>
      <p className="text-sm leading-relaxed mb-6" style={{ color: 'oklch(60% 0 0)' }}>
        Load a demo initiative graph to explore the Galaxy, Topology, and
        Decisions views — 15 nodes and 17 edges representing goals, projects,
        signals, and artifacts.
      </p>

      {status === 'error' && errorMsg && (
        <p
          className="text-sm mb-4 p-3 rounded"
          style={{ color: 'oklch(70% 0.18 25)', background: 'oklch(15% 0.05 25)' }}
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
                : 'oklch(38% 0 0)',
          color: 'oklch(95% 0 0)',
          cursor: status === 'loading' || status === 'done' ? 'default' : 'pointer',
        }}
      >
        {status === 'loading'
          ? 'Loading…'
          : status === 'done'
            ? 'Done — opening Galaxy'
            : 'Load sample data'}
      </button>

      {status === 'idle' && (
        <p className="text-xs mt-3 text-center" style={{ color: 'oklch(40% 0 0)' }}>
          Scoped to your workspace. Can be cleared any time.
        </p>
      )}
    </div>
  );
}

// ── Tab bar ───────────────────────────────────────────────────────────────────

type Tab = 'github' | 'sample';

// ── Main view ─────────────────────────────────────────────────────────────────

export default function OnboardingView() {
  const [tab, setTab] = useState<Tab>('github');

  return (
    <motion.div
      data-view="onboarding"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
      className="flex h-full w-full flex-col items-center justify-center gap-6"
      style={{ background: 'var(--color-galaxy-bg, oklch(8% 0 0))' }}
    >
      <div className="flex gap-1 rounded-lg p-1" style={{ background: 'oklch(14% 0 0)', border: '1px solid oklch(22% 0 0)' }}>
        {(['github', 'sample'] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className="rounded-md px-4 py-1.5 text-sm font-medium transition-colors"
            style={{
              background: tab === t ? 'oklch(22% 0 0)' : 'transparent',
              color: tab === t ? 'oklch(88% 0 0)' : 'oklch(50% 0 0)',
            }}
          >
            {t === 'github' ? 'Connect GitHub' : 'Sample data'}
          </button>
        ))}
      </div>

      {tab === 'github' ? <GitHubConnectTab /> : <SampleDataTab />}
    </motion.div>
  );
}
