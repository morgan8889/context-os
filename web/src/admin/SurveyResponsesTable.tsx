/**
 * SurveyResponsesTable — view all tenant survey responses.
 *
 * Columns: Org Name, Pain Option (color badge), Free Text (truncated), Answered At
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchSurveyResponses } from '@/lib/api/admin';
import type { SurveyResponseRow } from '@/lib/api/admin';
import { adminKeys } from './FunnelView';

// ── Pain Option Colors ─────────────────────────────────────────────────────────

const PAIN_OPTION_CONFIG: Record<string, { label: string; cls: string }> = {
  briefings: {
    label: 'Weekly Briefing',
    cls: 'bg-blue-100 text-blue-700',
  },
  dependencies: {
    label: 'Cross-team Deps',
    cls: 'bg-purple-100 text-purple-700',
  },
  decision_retrieval: {
    label: 'Decision Retrieval',
    cls: 'bg-green-100 text-green-700',
  },
  architecture_review_cycle_time: {
    label: 'Architecture Review',
    cls: 'bg-orange-100 text-orange-700',
  },
  something_else: {
    label: 'Something Else',
    cls: 'bg-neutral-100 text-neutral-600',
  },
};

function PainOptionBadge({ option }: { option: string }) {
  const config = PAIN_OPTION_CONFIG[option] ?? { label: option, cls: 'bg-neutral-100 text-neutral-600' };
  return (
    <span
      className={[
        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
        config.cls,
      ].join(' ')}
    >
      {config.label}
    </span>
  );
}

// ── Free Text Cell ─────────────────────────────────────────────────────────────

function FreeTextCell({ text }: { text: string | null }) {
  const [expanded, setExpanded] = useState(false);

  if (!text) return <span className="text-neutral-300">—</span>;

  const isLong = text.length > 80;
  const display = isLong && !expanded ? `${text.slice(0, 80)}…` : text;

  return (
    <span>
      <span className="text-neutral-700">{display}</span>
      {isLong && (
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="ml-1.5 text-xs text-blue-600 underline-offset-2 hover:underline"
        >
          {expanded ? 'Collapse' : 'Expand'}
        </button>
      )}
    </span>
  );
}

// ── Component ──────────────────────────────────────────────────────────────────

export default function SurveyResponsesTable() {
  const { data: responses, isLoading, error } = useQuery<SurveyResponseRow[], Error>({
    queryKey: adminKeys.surveyResponses,
    queryFn: fetchSurveyResponses,
    staleTime: 60_000,
  });

  if (isLoading) {
    return (
      <div className="p-8">
        <h1 className="mb-6 text-xl font-bold text-neutral-900">Survey Responses</h1>
        <div className="space-y-2">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-12 animate-pulse rounded-lg bg-neutral-100" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <h1 className="mb-6 text-xl font-bold text-neutral-900">Survey Responses</h1>
        <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-700">
          Failed to load responses: {error.message}
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-bold text-neutral-900">Survey Responses</h1>
        <span className="text-sm text-neutral-400">{responses?.length ?? 0} responses</span>
      </div>

      <div className="overflow-hidden rounded-xl border border-neutral-200 bg-white shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-200 bg-neutral-50">
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-neutral-500">
                Org Name
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-neutral-500">
                Pain Area
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-neutral-500">
                Free Text
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-neutral-500">
                Answered At
              </th>
            </tr>
          </thead>
          <tbody>
            {(responses ?? []).map((row) => (
              <tr
                key={`${row.tenant_id}-${row.answered_at}`}
                className="border-b border-neutral-100 last:border-0 hover:bg-neutral-50"
              >
                <td className="px-4 py-3 font-medium text-neutral-900">{row.tenant_name}</td>
                <td className="px-4 py-3">
                  <PainOptionBadge option={row.pain_option} />
                </td>
                <td className="max-w-xs px-4 py-3">
                  <FreeTextCell text={row.free_text} />
                </td>
                <td className="px-4 py-3 text-neutral-500">
                  {new Date(row.answered_at).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </td>
              </tr>
            ))}
            {(responses?.length ?? 0) === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-sm text-neutral-400">
                  No survey responses yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
