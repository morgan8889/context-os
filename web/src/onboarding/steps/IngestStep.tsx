/**
 * IngestStep — live progress view while data is being synced.
 *
 * - Polls GET /onboarding/ingest-status every 5 seconds
 * - Animated progress bar with progress_pct
 * - Shows elapsed time and simple estimate
 * - Completed: record counts + "Drafting your first briefing now."
 * - Stalled: retry button
 */
import { useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { onboardingKeys } from '@/lib/hooks/useOnboardingSession';

// ── Types ──────────────────────────────────────────────────────────────────────

export interface IngestJob {
  id: string;
  tenant_id: string;
  source: string;
  status: 'running' | 'completed' | 'stalled' | 'failed';
  progress_pct: number;
  record_counts: { initiatives?: number; prs?: number; threads?: number };
  started_at: string;
  completed_at: string | null;
  error_detail: object | null;
}

// ── Elapsed Timer ──────────────────────────────────────────────────────────────

function useElapsed(startedAt: string | undefined): string {
  return useMemo(() => {
    if (!startedAt) return '0s';
    const seconds = Math.floor((Date.now() - new Date(startedAt).getTime()) / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remaining = seconds % 60;
    return `${minutes}m ${remaining}s`;
  }, [startedAt]);
}

// ── Progress Bar ───────────────────────────────────────────────────────────────

interface ProgressBarProps {
  pct: number;
  status: IngestJob['status'];
}

function ProgressBar({ pct, status }: ProgressBarProps) {
  const clampedPct = Math.min(100, Math.max(0, pct));

  const barColor =
    status === 'completed'
      ? 'bg-green-500'
      : status === 'stalled' || status === 'failed'
        ? 'bg-amber-500'
        : 'bg-blue-500';

  return (
    <div
      className="h-3 w-full overflow-hidden rounded-full bg-neutral-100"
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={clampedPct}
      aria-label="Ingest progress"
    >
      <div
        className={['h-full rounded-full transition-all duration-1000 ease-out', barColor].join(' ')}
        style={{ width: `${clampedPct}%` }}
      />
    </div>
  );
}

// ── Component ──────────────────────────────────────────────────────────────────

export default function IngestStep() {
  const queryClient = useQueryClient();

  const { data: job, isLoading } = useQuery<IngestJob, Error>({
    queryKey: onboardingKeys.ingestStatus(),
    queryFn: async () => {
      const response = await apiClient.get<IngestJob>('/onboarding/ingest-status');
      return response.data;
    },
    // Poll every 5s unless completed / failed
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === 'completed' || status === 'failed') return false;
      return 5_000;
    },
    staleTime: 0,
  });

  const elapsed = useElapsed(job?.started_at);

  function handleRetry() {
    void queryClient.invalidateQueries({ queryKey: onboardingKeys.ingestStatus() });
  }

  if (isLoading) {
    return (
      <div className="rounded-2xl border border-neutral-200 bg-white p-8 shadow-sm">
        <div className="h-6 w-1/2 animate-pulse rounded bg-neutral-200" />
        <div className="mt-4 h-3 w-full animate-pulse rounded-full bg-neutral-100" />
      </div>
    );
  }

  const status = job?.status ?? 'running';
  const pct = job?.progress_pct ?? 0;
  const counts = job?.record_counts ?? {};

  return (
    <div className="rounded-2xl border border-neutral-200 bg-white p-8 shadow-sm">
      <h2 className="mb-1 text-xl font-bold text-neutral-900">
        {status === 'completed' ? 'Sync complete' : status === 'stalled' ? 'Sync stalled' : 'Syncing your data…'}
      </h2>
      <p className="mb-6 text-sm text-neutral-500">
        {status === 'completed'
          ? 'Your data has been indexed and your first briefing is being drafted.'
          : status === 'stalled'
            ? 'The ingest process appears to have stalled. You can retry below.'
            : 'This usually takes 2–5 minutes depending on the size of your workspace.'}
      </p>

      {/* Progress bar */}
      <ProgressBar pct={pct} status={status} />

      {/* Meta row */}
      <div className="mt-3 flex items-center justify-between text-xs text-neutral-400">
        <span>{Math.round(pct)}% complete</span>
        <span>Elapsed: {elapsed}</span>
      </div>

      {/* Completed state */}
      {status === 'completed' && (
        <div className="mt-6 rounded-xl bg-green-50 border border-green-200 px-5 py-4">
          <p className="text-sm font-medium text-green-800">
            Found{' '}
            <strong>{counts.initiatives ?? 0}</strong> initiatives,{' '}
            <strong>{counts.prs ?? 0}</strong> PRs,{' '}
            <strong>{counts.threads ?? 0}</strong> threads.{' '}
            Drafting your first briefing now.
          </p>
          <div className="mt-3 flex items-center gap-2 text-xs text-green-600">
            <span
              className="h-4 w-4 animate-spin rounded-full border-2 border-green-200 border-t-green-600"
              aria-hidden="true"
            />
            Drafting briefing…
          </div>
        </div>
      )}

      {/* Stalled state */}
      {status === 'stalled' && (
        <div className="mt-6 rounded-xl bg-amber-50 border border-amber-200 px-5 py-4">
          <p className="mb-3 text-sm font-medium text-amber-800">
            Ingest appears stalled — no progress in the last few minutes.
          </p>
          <button
            type="button"
            onClick={handleRetry}
            className={[
              'rounded-lg bg-amber-600 px-4 py-2 text-xs font-semibold text-white',
              'hover:bg-amber-700 focus-visible:outline-none',
              'focus-visible:ring-2 focus-visible:ring-amber-500',
            ].join(' ')}
          >
            Retry ingest
          </button>
        </div>
      )}

      {/* Running state — pulsing dots */}
      {status === 'running' && (
        <div className="mt-6 flex items-center gap-2 text-sm text-neutral-400">
          <span className="inline-flex gap-1">
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                className="h-1.5 w-1.5 animate-bounce rounded-full bg-blue-400"
                style={{ animationDelay: `${i * 150}ms` }}
                aria-hidden="true"
              />
            ))}
          </span>
          Processing records from your connected tools
        </div>
      )}
    </div>
  );
}
