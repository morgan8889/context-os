/**
 * BriefingStep — renders the first AI-drafted briefing for review and approval.
 *
 * - Fetches briefing from GET /api/v1/briefings/{id} via inbox if needed
 * - "Approve" button calls useActivationMutation
 * - On success renders OnboardingComplete
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { useOnboardingSession, useActivationMutation } from '@/lib/hooks/useOnboardingSession';
import OnboardingComplete from '../OnboardingComplete';

// ── Types ──────────────────────────────────────────────────────────────────────

interface BriefingContent {
  id: string;
  title: string;
  summary: string;
  sections: Array<{ heading: string; body: string }>;
  created_at: string;
}

// ── Briefing Skeleton ──────────────────────────────────────────────────────────

function BriefingSkeleton() {
  return (
    <div className="space-y-4">
      <div className="h-6 w-2/3 animate-pulse rounded bg-neutral-200" />
      <div className="space-y-2">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className={['h-4 animate-pulse rounded bg-neutral-100', i === 3 ? 'w-1/2' : 'w-full'].join(' ')} />
        ))}
      </div>
      <div className="mt-4 space-y-3">
        {[0, 1].map((i) => (
          <div key={i}>
            <div className="mb-2 h-4 w-1/3 animate-pulse rounded bg-neutral-200" />
            <div className="space-y-1.5">
              {[0, 1, 2].map((j) => (
                <div key={j} className="h-3.5 animate-pulse rounded bg-neutral-100" />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Component ──────────────────────────────────────────────────────────────────

export default function BriefingStep() {
  const { session } = useOnboardingSession();
  const { mutate, isPending, isSuccess } = useActivationMutation();
  const [approvedBriefingId, setApprovedBriefingId] = useState<string | null>(null);

  // Try to resolve the briefing ID from the session's ingest job
  const briefingQueryKey = ['onboarding', 'first-briefing', session?.ingest_job_id];

  const { data: briefing, isLoading, error } = useQuery<BriefingContent, Error>({
    queryKey: briefingQueryKey,
    queryFn: async () => {
      // First try to get the briefing from the approval inbox
      const inboxResponse = await apiClient.get<{
        items: Array<{ id: string; item_type: string; status: string; content: Record<string, unknown> }>;
      }>('/api/v1/inbox?item_type=briefing_draft&status=pending&limit=1');

      const firstItem = inboxResponse.data.items[0];

      if (firstItem) {
        // Inline briefing data from inbox content
        const content = firstItem.content as {
          title?: string;
          summary?: string;
          sections?: Array<{ heading: string; body: string }>;
        };
        return {
          id: firstItem.id,
          title: content.title ?? 'Your First Briefing',
          summary: content.summary ?? '',
          sections: content.sections ?? [],
          created_at: new Date().toISOString(),
        };
      }

      // Fallback: try direct briefing endpoint if we have a job ID
      if (session?.ingest_job_id) {
        const briefingResponse = await apiClient.get<BriefingContent>(
          `/api/v1/briefings/${session.ingest_job_id}`
        );
        return briefingResponse.data;
      }

      throw new Error('No briefing available yet');
    },
    enabled: !!session,
    retry: 5,
    retryDelay: 3_000,
  });

  function handleApprove() {
    if (!briefing) return;
    setApprovedBriefingId(briefing.id);
    mutate({ briefing_id: briefing.id, accepted_as_is: true });
  }

  // Show complete screen after successful activation
  if (isSuccess || (approvedBriefingId !== null && isSuccess)) {
    return <OnboardingComplete />;
  }

  return (
    <div className="rounded-2xl border border-neutral-200 bg-white p-8 shadow-sm">
      <h2 className="mb-1 text-xl font-bold text-neutral-900">Your first briefing</h2>
      <p className="mb-6 text-sm text-neutral-500">
        Context OS drafted this from your connected tools. Review it and approve to activate your workspace.
      </p>

      {/* Briefing content */}
      <div className="mb-6 rounded-xl bg-neutral-50 border border-neutral-200 p-5">
        {isLoading && <BriefingSkeleton />}

        {error && !briefing && (
          <div className="flex items-center gap-2 text-sm text-amber-700">
            <span
              className="h-4 w-4 animate-spin rounded-full border-2 border-amber-200 border-t-amber-600"
              aria-hidden="true"
            />
            Waiting for briefing draft… this usually takes 1–2 minutes after ingest.
          </div>
        )}

        {briefing && (
          <article className="prose prose-sm max-w-none">
            <h3 className="mb-3 text-base font-bold text-neutral-900">{briefing.title}</h3>
            {briefing.summary && (
              <p className="mb-4 text-sm leading-relaxed text-neutral-700">{briefing.summary}</p>
            )}
            {briefing.sections.map((section, idx) => (
              <section key={idx}>
                <h4 className="mb-1.5 text-sm font-semibold text-neutral-800">{section.heading}</h4>
                <p className="mb-4 text-sm leading-relaxed text-neutral-600">{section.body}</p>
              </section>
            ))}
            <p className="mt-2 text-xs text-neutral-400">
              Generated at {new Date(briefing.created_at).toLocaleString()}
            </p>
          </article>
        )}
      </div>

      <button
        type="button"
        onClick={handleApprove}
        disabled={!briefing || isPending}
        className={[
          'flex w-full items-center justify-center gap-2 rounded-xl py-3 text-sm font-semibold',
          'transition-all duration-150 focus-visible:outline-none',
          'focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1',
          briefing && !isPending
            ? 'bg-blue-600 text-white hover:bg-blue-700'
            : 'cursor-not-allowed bg-neutral-100 text-neutral-400',
        ].join(' ')}
      >
        {isPending ? (
          <>
            <span
              className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"
              aria-hidden="true"
            />
            Activating…
          </>
        ) : (
          'Approve and activate workspace'
        )}
      </button>

      <p className="mt-3 text-center text-xs text-neutral-400">
        You can always edit briefings later from the inbox.
      </p>
    </div>
  );
}
