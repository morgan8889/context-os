/**
 * OrgDetail — per-org admin detail view.
 *
 * Route: /admin/orgs/:tenantId
 * Shows timing breakdown, survey answer, connected integrations, ingest status.
 * "Impersonate" button starts impersonation session.
 */
import { useState, type ReactNode } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchFunnel, startImpersonation } from '@/lib/api/admin';
import type { AdminFunnelRow } from '@/lib/api/admin';
import { useImpersonation } from '@/lib/hooks/useImpersonation';
import { adminKeys } from './FunnelView';

// ── Stat Card ──────────────────────────────────────────────────────────────────

function StatCard({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="rounded-xl border border-neutral-200 bg-white p-4 shadow-sm">
      <p className="mb-1 text-xs font-medium uppercase tracking-wide text-neutral-400">{label}</p>
      <p className="text-base font-semibold text-neutral-900">{value}</p>
    </div>
  );
}

function formatDuration(seconds: number | null): string {
  if (seconds === null) return '—';
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

// ── Component ──────────────────────────────────────────────────────────────────

export default function OrgDetail() {
  const { tenantId } = useParams<{ tenantId: string }>();
  const navigate = useNavigate();
  const { startImpersonation: activateImpersonation } = useImpersonation();
  const [isImpersonating, setIsImpersonating] = useState(false);
  const [impersonationError, setImpersonationError] = useState<string | null>(null);

  // Reuse the funnel query (already cached from FunnelView)
  const { data: rows, isLoading } = useQuery<AdminFunnelRow[], Error>({
    queryKey: adminKeys.funnel,
    queryFn: fetchFunnel,
    staleTime: 30_000,
  });

  const org = rows?.find((r) => r.tenant_id === tenantId);

  async function handleImpersonate() {
    if (!tenantId) return;
    setIsImpersonating(true);
    setImpersonationError(null);

    try {
      const result = await startImpersonation(tenantId);
      activateImpersonation(result.token, result.expires_at, result.target_tenant_name);
      // Navigate away so the operator can see the impersonated workspace
      void navigate('/galaxy');
    } catch (err) {
      setImpersonationError(err instanceof Error ? err.message : 'Failed to start impersonation');
    } finally {
      setIsImpersonating(false);
    }
  }

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="mb-4 h-6 w-48 animate-pulse rounded bg-neutral-200" />
        <div className="grid grid-cols-3 gap-4">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-20 animate-pulse rounded-xl bg-neutral-100" />
          ))}
        </div>
      </div>
    );
  }

  if (!org) {
    return (
      <div className="p-8">
        <button
          type="button"
          onClick={() => void navigate('/admin/funnel')}
          className="mb-4 text-sm text-blue-600 hover:underline"
        >
          ← Back to Funnel
        </button>
        <p className="text-sm text-neutral-500">Organization not found: {tenantId}</p>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Back link */}
      <button
        type="button"
        onClick={() => void navigate('/admin/funnel')}
        className="mb-6 flex items-center gap-1 text-sm text-neutral-500 hover:text-neutral-900"
      >
        <svg viewBox="0 0 16 16" className="h-4 w-4" fill="currentColor" aria-hidden="true">
          <path fillRule="evenodd" d="M9.78 4.22a.75.75 0 010 1.06L7.06 8l2.72 2.72a.75.75 0 11-1.06 1.06L5.47 8.53a.75.75 0 010-1.06L8.72 4.22a.75.75 0 011.06 0z" clipRule="evenodd" />
        </svg>
        Back to Funnel
      </button>

      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">{org.tenant_name}</h1>
          <p className="mt-0.5 font-mono text-xs text-neutral-400">{org.tenant_id}</p>
        </div>

        <button
          type="button"
          onClick={() => void handleImpersonate()}
          disabled={isImpersonating}
          className={[
            'flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold',
            'transition-colors duration-150 focus-visible:outline-none',
            'focus-visible:ring-2 focus-visible:ring-amber-500',
            isImpersonating
              ? 'cursor-not-allowed bg-neutral-100 text-neutral-400'
              : 'bg-amber-500 text-white hover:bg-amber-600',
          ].join(' ')}
        >
          {isImpersonating ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-neutral-300 border-t-neutral-600" aria-hidden="true" />
              Starting…
            </>
          ) : (
            <>
              <svg viewBox="0 0 16 16" className="h-4 w-4" fill="currentColor" aria-hidden="true">
                <path d="M8 8a3 3 0 100-6 3 3 0 000 6zM12.735 14c.618 0 1.093-.561.872-1.139a6.002 6.002 0 00-11.215 0c-.22.578.254 1.139.872 1.139h9.47z" />
              </svg>
              Impersonate
            </>
          )}
        </button>
      </div>

      {impersonationError && (
        <div className="mb-6 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {impersonationError}
        </div>
      )}

      {/* Stats Grid */}
      <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-3">
        <StatCard label="Current Step" value={
          <span className="capitalize">{org.current_step}</span>
        } />
        <StatCard label="Time in Step" value={formatDuration(org.time_in_current_step_seconds)} />
        <StatCard
          label="Activated At"
          value={org.activated_at
            ? new Date(org.activated_at).toLocaleDateString(undefined, {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
              })
            : '—'}
        />
        <StatCard
          label="Time to Activate"
          value={formatDuration(org.activation_timing)}
        />
        <StatCard
          label="Drop-off"
          value={org.drop_off_flag ? '⚠️ Yes' : 'No'}
        />
        <StatCard
          label="Integrations"
          value={
            org.connected_integrations.length > 0
              ? org.connected_integrations.join(', ')
              : 'None connected'
          }
        />
      </div>
    </div>
  );
}
