/**
 * FunnelView — onboarding funnel table for platform operators.
 *
 * Columns: Org Name, Current Step, Connected Integrations, Time in Step,
 *          Drop-off (⚠️), Activated At
 * Amber background for rows with drop_off_flag === true.
 * Row click → /admin/orgs/:tenant_id
 */
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { fetchFunnel } from '@/lib/api/admin';
import type { AdminFunnelRow } from '@/lib/api/admin';

// ── Query Key ──────────────────────────────────────────────────────────────────

export const adminKeys = {
  funnel: ['admin', 'funnel'] as const,
  surveyResponses: ['admin', 'survey-responses'] as const,
};

// ── Step Badge ─────────────────────────────────────────────────────────────────

const STEP_COLORS: Record<string, string> = {
  survey: 'bg-blue-100 text-blue-700',
  connect: 'bg-purple-100 text-purple-700',
  scope: 'bg-indigo-100 text-indigo-700',
  ingest: 'bg-amber-100 text-amber-700',
  briefing: 'bg-orange-100 text-orange-700',
  activated: 'bg-green-100 text-green-700',
};

function StepBadge({ step }: { step: string }) {
  const cls = STEP_COLORS[step] ?? 'bg-neutral-100 text-neutral-600';
  return (
    <span className={['inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize', cls].join(' ')}>
      {step}
    </span>
  );
}

// ── Integration Chips ──────────────────────────────────────────────────────────

const INTEGRATION_ICONS: Record<string, string> = {
  jira: 'J',
  github: 'GH',
  slack: 'SL',
};

function IntegrationChips({ integrations }: { integrations: string[] }) {
  if (integrations.length === 0) {
    return <span className="text-xs text-neutral-400">None</span>;
  }
  return (
    <div className="flex gap-1">
      {integrations.map((src) => (
        <span
          key={src}
          className="inline-flex items-center rounded bg-neutral-100 px-1.5 py-0.5 text-xs font-medium text-neutral-600"
          title={src}
        >
          {INTEGRATION_ICONS[src] ?? src.slice(0, 2).toUpperCase()}
        </span>
      ))}
    </div>
  );
}

// ── Time Display ───────────────────────────────────────────────────────────────

function relativeTime(seconds: number | null): string {
  if (seconds === null) return '—';
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
}

function formatDate(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// ── Table Skeleton ─────────────────────────────────────────────────────────────

function TableSkeleton() {
  return (
    <div className="space-y-1 p-6">
      {[0, 1, 2, 3, 4].map((i) => (
        <div key={i} className="flex gap-4 rounded-lg border border-neutral-100 p-3">
          {[0, 1, 2, 3].map((j) => (
            <div
              key={j}
              className={['h-4 animate-pulse rounded bg-neutral-100', j === 0 ? 'w-32' : 'w-20'].join(' ')}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

// ── Component ──────────────────────────────────────────────────────────────────

export default function FunnelView() {
  const navigate = useNavigate();

  const { data: rows, isLoading, error } = useQuery<AdminFunnelRow[], Error>({
    queryKey: adminKeys.funnel,
    queryFn: fetchFunnel,
    staleTime: 30_000,
  });

  if (isLoading) {
    return (
      <div className="p-8">
        <h1 className="mb-6 text-xl font-bold text-neutral-900">Onboarding Funnel</h1>
        <TableSkeleton />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <h1 className="mb-6 text-xl font-bold text-neutral-900">Onboarding Funnel</h1>
        <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-700">
          Failed to load funnel data: {error.message}
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-bold text-neutral-900">Onboarding Funnel</h1>
        <span className="text-sm text-neutral-400">{rows?.length ?? 0} orgs</span>
      </div>

      <div className="overflow-hidden rounded-xl border border-neutral-200 bg-white shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-200 bg-neutral-50">
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-neutral-500">
                Org Name
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-neutral-500">
                Step
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-neutral-500">
                Connected
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-neutral-500">
                Time in Step
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-neutral-500">
                Drop-off
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-neutral-500">
                Activated At
              </th>
            </tr>
          </thead>
          <tbody>
            {(rows ?? []).map((row, idx) => (
              <tr
                key={row.tenant_id}
                onClick={() => void navigate(`/admin/orgs/${row.tenant_id}`)}
                className={[
                  'cursor-pointer border-b border-neutral-100 transition-colors duration-100',
                  'last:border-0',
                  row.drop_off_flag
                    ? 'bg-amber-50 hover:bg-amber-100'
                    : idx % 2 === 0
                      ? 'bg-white hover:bg-neutral-50'
                      : 'bg-neutral-50/50 hover:bg-neutral-50',
                ].join(' ')}
              >
                <td className="px-4 py-3 font-medium text-neutral-900">{row.tenant_name}</td>
                <td className="px-4 py-3">
                  <StepBadge step={row.current_step} />
                </td>
                <td className="px-4 py-3">
                  <IntegrationChips integrations={row.connected_integrations} />
                </td>
                <td className="px-4 py-3 text-neutral-600">
                  {relativeTime(row.time_in_current_step_seconds)}
                </td>
                <td className="px-4 py-3">
                  {row.drop_off_flag ? (
                    <span className="text-base" title="Drop-off detected" role="img" aria-label="Drop-off">
                      ⚠️
                    </span>
                  ) : (
                    <span className="text-neutral-300">—</span>
                  )}
                </td>
                <td className="px-4 py-3 text-neutral-500">{formatDate(row.activated_at)}</td>
              </tr>
            ))}
            {(rows?.length ?? 0) === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-sm text-neutral-400">
                  No orgs found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
