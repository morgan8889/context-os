/**
 * InboxView — Full Inbox implementation.
 *
 * Fetches pending approval items from GET /api/v1/inbox?status=pending,
 * renders a card list with approve / reject actions backed by TanStack Query
 * mutations with optimistic updates.
 */

import { useState, useEffect, useRef, type ChangeEvent } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { apiClient } from '@/lib/api/client';
import { inboxKeys } from '@/lib/api/queryKeys';
import { HintTooltip } from '@/design-system/primitives/HintTooltip';
import { FirstVisitCallout } from '@/design-system/primitives/FirstVisitCallout';
import type { ApiApprovalItem } from '@/types/api';

// ── API helpers ───────────────────────────────────────────────────────────────

interface InboxListResponse {
  items: ApiApprovalItem[];
  next_cursor: string | null;
}

async function fetchInboxItems(): Promise<InboxListResponse> {
  const res = await apiClient.get<InboxListResponse>('/api/v1/inbox', {
    params: { status: 'pending' },
  });
  return res.data;
}

async function approveItem(id: string): Promise<void> {
  await apiClient.post(`/api/v1/inbox/${id}/approve`, {});
}

async function rejectItem(id: string, reason: string): Promise<void> {
  await apiClient.post(`/api/v1/inbox/${id}/reject`, { reason });
}

// ── Relative date formatting ──────────────────────────────────────────────────

const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });

function relativeDate(isoString: string): string {
  const diffMs = new Date(isoString).getTime() - Date.now();
  const diffSecs = Math.round(diffMs / 1_000);
  const diffMins = Math.round(diffSecs / 60);
  const diffHours = Math.round(diffMins / 60);
  const diffDays = Math.round(diffHours / 24);

  if (Math.abs(diffSecs) < 60) return rtf.format(diffSecs, 'second');
  if (Math.abs(diffMins) < 60) return rtf.format(diffMins, 'minute');
  if (Math.abs(diffHours) < 24) return rtf.format(diffHours, 'hour');
  return rtf.format(diffDays, 'day');
}

// ── Type badge colours ────────────────────────────────────────────────────────

const TYPE_BADGE_STYLES: Record<
  string,
  { background: string; color: string; border: string }
> = {
  briefing_draft: {
    background: 'oklch(94% 0.06 220)',
    color: 'oklch(35% 0.2 220)',
    border: 'oklch(80% 0.1 220)',
  },
  proposed_dependency: {
    background: 'oklch(94% 0.06 280)',
    color: 'oklch(35% 0.2 280)',
    border: 'oklch(80% 0.1 280)',
  },
  proposed_risk: {
    background: 'oklch(95% 0.06 25)',
    color: 'oklch(40% 0.22 25)',
    border: 'oklch(82% 0.1 25)',
  },
};

const DEFAULT_BADGE_STYLE = {
  background: 'oklch(94% 0 0)',
  color: 'oklch(35% 0 0)',
  border: 'oklch(80% 0 0)',
};

function typeBadgeStyle(itemType: string) {
  return TYPE_BADGE_STYLES[itemType] ?? DEFAULT_BADGE_STYLE;
}

function typeLabel(itemType: string): string {
  switch (itemType) {
    case 'briefing_draft':
      return 'Briefing Draft';
    case 'proposed_dependency':
      return 'Proposed Dependency';
    case 'proposed_risk':
      return 'Proposed Risk';
    default:
      return itemType.replace(/_/g, ' ');
  }
}

const TYPE_TOOLTIPS: Record<string, string> = {
  briefing_draft:
    'A weekly synthesis drafted by the Operational Synthesizer agent. Approve to schedule delivery; reject to flag an issue.',
  proposed_dependency:
    'A dependency relationship between two initiatives, inferred from your work signals. Approve to record in the graph.',
  proposed_risk:
    'A risk flag raised by the AI against a specific initiative. Approve to acknowledge; reject if it’s not applicable.',
};

// ── Skeleton card ─────────────────────────────────────────────────────────────

function SkeletonCard() {
  return (
    <div
      className="rounded-xl border px-5 py-4 flex flex-col gap-3"
      style={{
        background: 'oklch(99% 0 0)',
        borderColor: 'oklch(90% 0 0)',
      }}
      aria-hidden="true"
    >
      <div
        className="h-4 w-28 rounded-full animate-pulse"
        style={{ background: 'var(--color-placeholder-grey)' }}
      />
      <div
        className="h-3.5 w-full rounded animate-pulse"
        style={{ background: 'var(--color-placeholder-grey)' }}
      />
      <div
        className="h-3.5 w-3/4 rounded animate-pulse"
        style={{ background: 'var(--color-placeholder-grey)' }}
      />
      <div className="flex gap-2 pt-1">
        <div
          className="h-7 w-20 rounded-lg animate-pulse"
          style={{ background: 'var(--color-placeholder-grey)' }}
        />
        <div
          className="h-7 w-20 rounded-lg animate-pulse"
          style={{ background: 'var(--color-placeholder-grey)' }}
        />
      </div>
    </div>
  );
}

// ── Approval card ─────────────────────────────────────────────────────────────

interface ApprovalCardProps {
  item: ApiApprovalItem;
  onApprove: (id: string) => void;
  onReject: (id: string, reason: string) => void;
  isApproving: boolean;
  isRejecting: boolean;
}

function ApprovalCard({
  item,
  onApprove,
  onReject,
  isApproving,
  isRejecting,
}: ApprovalCardProps) {
  const [rejectExpanded, setRejectExpanded] = useState(false);
  const [rejectReason, setRejectReason] = useState('');

  const badgeStyle = typeBadgeStyle(item.item_type);
  const hasFailureFlags =
    item.failure_flags !== null && item.failure_flags.length > 0;

  // Extract a human-readable summary from content
  const contentSummary =
    [item.content['summary'], item.content['title'], item.content['description']]
      .find((v): v is string => typeof v === 'string') ?? 'No summary available.';

  function handleRejectSubmit() {
    onReject(item.id, rejectReason);
    setRejectExpanded(false);
    setRejectReason('');
  }

  return (
    <motion.article
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.97, transition: { duration: 0.15 } }}
      transition={{ duration: 0.2, ease: [0.0, 0, 0.2, 1] }}
      className="rounded-xl border flex flex-col gap-3 px-5 py-4"
      style={{
        background: 'oklch(99.5% 0 0)',
        borderColor: hasFailureFlags ? 'oklch(80% 0.1 55)' : 'oklch(91% 0 0)',
        boxShadow: 'var(--shadow-node)',
      }}
      aria-label={`Approval item: ${typeLabel(item.item_type)}`}
    >
      {/* Header row: type badge + date */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <span className="inline-flex items-center">
          <span
            className="rounded-full px-2.5 py-0.5 text-xs font-semibold"
            style={{
              background: badgeStyle.background,
              color: badgeStyle.color,
              border: `1px solid ${badgeStyle.border}`,
            }}
          >
            {typeLabel(item.item_type)}
          </span>
          {TYPE_TOOLTIPS[item.item_type] && (
            <HintTooltip content={TYPE_TOOLTIPS[item.item_type]} />
          )}
        </span>
        <time
          dateTime={item.created_at}
          className="text-xs shrink-0"
          style={{ color: 'oklch(55% 0 0)' }}
        >
          {relativeDate(item.created_at)}
        </time>
      </div>

      {/* Failure flags warning list */}
      {hasFailureFlags && (
        <div
          className="rounded-lg px-3 py-2"
          style={{ background: 'oklch(96% 0.06 55)', border: '1px solid oklch(82% 0.1 55)' }}
        >
          <div className="flex items-center gap-1 mb-1">
            <span className="text-xs font-semibold" style={{ color: 'oklch(40% 0.15 55)' }}>
              Failure flags
            </span>
            <HintTooltip
              content="Failure flags are quality checks the AI ran on its own draft. They don't block approval — they're signals to review before deciding."
              side="right"
            />
          </div>
        <ul
          className="flex flex-col gap-1"
          aria-label="AI failure flags"
        >
          {item.failure_flags!.map((flag, i) => (
            <li
              key={i}
              className="text-xs font-medium flex items-start gap-1.5"
              style={{ color: 'oklch(40% 0.15 55)' }}
            >
              <span aria-hidden="true">&#9888;</span>
              <span>
                {flag.type}: {flag.detail}
              </span>
            </li>
          ))}
        </ul>
        </div>
      )}

      {/* Content summary */}
      <p className="text-sm leading-relaxed" style={{ color: 'oklch(20% 0 0)' }}>
        {contentSummary}
      </p>

      {/* Action buttons */}
      <div className="flex items-center gap-2 pt-1 flex-wrap">
        <button
          onClick={() => onApprove(item.id)}
          disabled={isApproving || isRejecting}
          className="rounded-lg px-3.5 py-1.5 text-sm font-medium transition-colors duration-[var(--motion-duration-everyday)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[oklch(60%_0.2_145)] disabled:opacity-50"
          style={{
            background: 'oklch(72% 0.2 145)',
            color: 'oklch(100% 0 0)',
          }}
          aria-label="Approve this item"
        >
          {isApproving ? 'Approving…' : 'Approve'}
        </button>

        <button
          onClick={() => setRejectExpanded((v) => !v)}
          disabled={isApproving || isRejecting}
          className="rounded-lg px-3.5 py-1.5 text-sm font-medium transition-colors duration-[var(--motion-duration-everyday)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[oklch(60%_0.22_25)] disabled:opacity-50"
          style={{
            background: rejectExpanded ? 'oklch(94% 0.06 25)' : 'oklch(96% 0 0)',
            color: 'oklch(45% 0.2 25)',
            border: '1px solid oklch(85% 0.08 25)',
          }}
          aria-expanded={rejectExpanded}
          aria-label="Reject this item"
        >
          {isRejecting ? 'Rejecting…' : 'Reject'}
        </button>
      </div>

      {/* Inline reject reason textarea */}
      <AnimatePresence>
        {rejectExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.18, ease: [0.0, 0, 0.2, 1] }}
            className="overflow-hidden"
          >
            <div className="flex flex-col gap-2 pt-1">
              <label
                htmlFor={`reject-reason-${item.id}`}
                className="text-xs font-medium"
                style={{ color: 'oklch(40% 0 0)' }}
              >
                Reason (optional)
              </label>
              <textarea
                id={`reject-reason-${item.id}`}
                value={rejectReason}
                onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setRejectReason(e.target.value)}
                rows={3}
                placeholder="Explain why this item is being rejected…"
                className="w-full resize-none rounded-lg border px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[oklch(60%_0.2_220)]"
                style={{
                  background: 'oklch(99% 0 0)',
                  borderColor: 'oklch(85% 0 0)',
                  color: 'oklch(15% 0 0)',
                }}
              />
              <div className="flex gap-2">
                <button
                  onClick={handleRejectSubmit}
                  disabled={isRejecting}
                  className="rounded-lg px-3 py-1.5 text-sm font-medium transition-colors duration-[var(--motion-duration-everyday)] focus-visible:outline-none focus-visible:ring-2 disabled:opacity-50"
                  style={{
                    background: 'oklch(60% 0.22 25)',
                    color: 'oklch(100% 0 0)',
                  }}
                >
                  Confirm Reject
                </button>
                <button
                  onClick={() => {
                    setRejectExpanded(false);
                    setRejectReason('');
                  }}
                  className="rounded-lg px-3 py-1.5 text-sm font-medium transition-colors duration-[var(--motion-duration-everyday)] focus-visible:outline-none focus-visible:ring-2"
                  style={{
                    background: 'oklch(96% 0 0)',
                    color: 'oklch(40% 0 0)',
                    border: '1px solid oklch(88% 0 0)',
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.article>
  );
}

// ── Empty state ───────────────────────────────────────────────────────────────

function EmptyState() {
  return (
    <div
      className="flex flex-col items-center justify-center gap-4 py-20 px-6 text-center"
      role="status"
      aria-live="polite"
    >
      <div
        className="flex h-14 w-14 items-center justify-center rounded-full"
        style={{ background: 'var(--color-placeholder-grey)' }}
        aria-hidden="true"
      >
        <svg
          width="28"
          height="28"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ color: 'oklch(60% 0 0)' }}
        >
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
          <polyline points="22 4 12 14.01 9 11.01" />
        </svg>
      </div>
      <p className="text-sm font-medium" style={{ color: 'oklch(35% 0 0)' }}>
        No pending items — your AI agents are keeping up with the work
      </p>
    </div>
  );
}

// ── Error state ───────────────────────────────────────────────────────────────

function ErrorState({ message }: { message: string }) {
  return (
    <div
      className="flex flex-col items-center gap-2 py-16"
      role="alert"
      style={{ color: 'oklch(45% 0.2 25)' }}
    >
      <span className="text-sm font-medium">Failed to load inbox</span>
      <span className="text-xs" style={{ color: 'oklch(55% 0 0)' }}>
        {message}
      </span>
    </div>
  );
}

// ── Generate Briefing ─────────────────────────────────────────────────────────

type BriefingStatus = 'idle' | 'generating' | 'done' | 'error';

interface BriefingStatusResponse {
  status: string;
  run_id: string;
}

function GenerateBriefingButton({ onDone }: { onDone: () => void }) {
  const [status, setStatus] = useState<BriefingStatus>('idle');
  const [msg, setMsg] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  async function handleGenerate() {
    setStatus('generating');
    setMsg(null);
    try {
      const res = await apiClient.post<{ run_id: string }>('/api/v1/briefing/generate', {});
      const runId = res.data.run_id;

      pollRef.current = setInterval(async () => {
        try {
          const statusRes = await apiClient.get<BriefingStatusResponse>(
            `/api/v1/briefing/status/${runId}`
          );
          if (statusRes.data.status === 'completed' || statusRes.data.status === 'approved') {
            clearInterval(pollRef.current!);
            setStatus('done');
            setMsg('Briefing ready — check the list below.');
            onDone();
            setTimeout(() => { setStatus('idle'); setMsg(null); }, 4000);
          } else if (statusRes.data.status === 'failed') {
            clearInterval(pollRef.current!);
            setStatus('error');
            setMsg('Briefing generation failed.');
          }
        } catch {
          clearInterval(pollRef.current!);
          setStatus('error');
          setMsg('Could not check briefing status.');
        }
      }, 3000);
    } catch (err) {
      setStatus('error');
      const detail = err instanceof Error ? err.message : 'Unknown error';
      setMsg(
        detail.includes('404') || detail.includes('no ingest')
          ? 'Connect GitHub first to generate a briefing.'
          : detail
      );
    }
  }

  return (
    <div className="flex flex-col gap-1">
      <button
        onClick={handleGenerate}
        disabled={status === 'generating'}
        className="rounded-lg px-3.5 py-1.5 text-sm font-medium transition-colors shrink-0 focus-visible:outline-none focus-visible:ring-2"
        style={{
          background: status === 'done' ? 'oklch(45% 0.12 145)' : 'oklch(55% 0.2 250)',
          color: 'oklch(97% 0 0)',
          opacity: status === 'generating' ? 0.6 : 1,
          cursor: status === 'generating' ? 'default' : 'pointer',
        }}
      >
        {status === 'generating' ? 'Generating…' : status === 'done' ? 'Done' : 'Generate Briefing'}
      </button>
      {msg && (
        <p
          className="text-xs"
          style={{ color: status === 'error' ? 'oklch(55% 0.2 25)' : 'oklch(45% 0.15 145)' }}
        >
          {msg}
        </p>
      )}
    </div>
  );
}

// ── Log Signal ────────────────────────────────────────────────────────────────

const SIGNAL_TYPES = [
  { value: 'observation', label: 'Observation' },
  { value: 'risk', label: 'Risk' },
  { value: 'blocker', label: 'Blocker' },
  { value: 'decision', label: 'Decision' },
] as const;

type SignalType = typeof SIGNAL_TYPES[number]['value'];

function LogSignalForm() {
  const [expanded, setExpanded] = useState(false);
  const [content, setContent] = useState('');
  const [signalType, setSignalType] = useState<SignalType>('observation');
  const [logStatus, setLogStatus] = useState<'idle' | 'saving' | 'done' | 'error'>('idle');

  async function handleLog() {
    if (!content.trim()) return;
    setLogStatus('saving');
    try {
      await apiClient.post('/api/v1/graph/signals', {
        content: content.trim(),
        signal_type: signalType,
      });
      setLogStatus('done');
      setContent('');
      setTimeout(() => { setLogStatus('idle'); setExpanded(false); }, 2500);
    } catch {
      setLogStatus('error');
    }
  }

  if (!expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="rounded-lg px-3.5 py-1.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2"
        style={{
          background: 'oklch(96% 0 0)',
          color: 'oklch(35% 0 0)',
          border: '1px solid oklch(87% 0 0)',
        }}
      >
        Log Signal
      </button>
    );
  }

  return (
    <div
      className="rounded-xl border p-4 flex flex-col gap-3"
      style={{ background: 'oklch(99% 0 0)', borderColor: 'oklch(90% 0 0)' }}
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold" style={{ color: 'oklch(20% 0 0)' }}>
          Log a signal
        </span>
        <button
          onClick={() => { setExpanded(false); setContent(''); setLogStatus('idle'); }}
          className="text-xs"
          style={{ color: 'oklch(55% 0 0)' }}
        >
          Cancel
        </button>
      </div>
      <textarea
        rows={3}
        placeholder="What's happening? e.g. &quot;Customer escalated billing issue&quot;"
        value={content}
        onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setContent(e.target.value)}
        className="w-full resize-none rounded-lg border px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[oklch(60%_0.2_250)]"
        style={{ background: 'oklch(99% 0 0)', borderColor: 'oklch(85% 0 0)', color: 'oklch(15% 0 0)' }}
      />
      <div className="flex items-center gap-3">
        <select
          value={signalType}
          onChange={(e: ChangeEvent<HTMLSelectElement>) => setSignalType(e.target.value as SignalType)}
          className="rounded-lg border px-2.5 py-1.5 text-sm focus-visible:outline-none"
          style={{ background: 'oklch(98% 0 0)', borderColor: 'oklch(85% 0 0)', color: 'oklch(20% 0 0)' }}
        >
          {SIGNAL_TYPES.map((t) => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </select>
        <button
          onClick={handleLog}
          disabled={logStatus === 'saving' || !content.trim()}
          className="rounded-lg px-3.5 py-1.5 text-sm font-medium transition-colors focus-visible:outline-none disabled:opacity-50"
          style={{ background: 'oklch(55% 0.2 250)', color: 'oklch(97% 0 0)' }}
        >
          {logStatus === 'saving' ? 'Saving…' : logStatus === 'done' ? 'Logged' : 'Log'}
        </button>
      </div>
      {logStatus === 'done' && (
        <p className="text-xs" style={{ color: 'oklch(45% 0.15 145)' }}>
          Signal logged — it will inform your next briefing.
        </p>
      )}
      {logStatus === 'error' && (
        <p className="text-xs" style={{ color: 'oklch(55% 0.2 25)' }}>
          Failed to log signal. Try again.
        </p>
      )}
    </div>
  );
}

// ── Main view ─────────────────────────────────────────────────────────────────

export default function InboxView() {
  const qc = useQueryClient();

  const queryKey = inboxKeys.list({ status: 'pending' });

  const {
    data,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey,
    queryFn: fetchInboxItems,
    staleTime: 30_000,
  });

  // Shared optimistic-removal callbacks for approve/reject mutations.
  const optimisticRemove = {
    onMutate: async ({ id }: { id: string }) => {
      await qc.cancelQueries({ queryKey });
      const prev = qc.getQueryData<InboxListResponse>(queryKey);
      if (prev) {
        qc.setQueryData<InboxListResponse>(queryKey, {
          ...prev,
          items: prev.items.filter((item) => item.id !== id),
        });
      }
      return prev ? { prev } : {};
    },
    onError: (_err: unknown, _vars: unknown, ctx: { prev?: InboxListResponse } | undefined) => {
      if (ctx?.prev) qc.setQueryData(queryKey, ctx.prev);
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey });
    },
  };

  const approveMutation = useMutation({
    mutationFn: ({ id }: { id: string }) => approveItem(id),
    ...optimisticRemove,
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      rejectItem(id, reason),
    ...optimisticRemove,
  });

  const items = data?.items ?? [];

  return (
    <div
      data-view="inbox"
      className="flex h-full flex-col overflow-hidden"
      style={{ background: 'oklch(97% 0 0)' }}
    >
      {/* Header */}
      <header
        className="shrink-0 border-b px-6 py-4"
        style={{
          background: 'oklch(100% 0 0)',
          borderColor: 'oklch(91% 0 0)',
        }}
      >
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-base font-semibold" style={{ color: 'oklch(12% 0 0)' }}>
              Inbox
            </h1>
            <p className="mt-0.5 text-xs" style={{ color: 'oklch(50% 0 0)' }}>
              Review and approve AI-generated drafts before they enter the knowledge graph.
            </p>
          </div>
          <div className="flex items-start gap-2 shrink-0 pt-0.5">
            <GenerateBriefingButton onDone={() => qc.invalidateQueries({ queryKey })} />
            <LogSignalForm />
          </div>
        </div>
      </header>

      {/* Scrollable content area */}
      <div className="flex-1 overflow-y-auto px-6 py-5">
        {/* First-visit view orientation callout */}
        <FirstVisitCallout
          storageKey="ctx_os_visited_inbox"
          title="Your Approval Queue"
          description="Context-OS drafts briefings, proposes dependencies, and flags risks for your review. Approve to add to the knowledge graph; reject with a reason to send back to the AI."
        />
        {isLoading && (
          <div className="flex flex-col gap-4 max-w-2xl mx-auto" aria-busy="true" aria-label="Loading inbox items">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
        )}

        {isError && (
          <ErrorState
            message={
              error instanceof Error ? error.message : 'Unknown error'
            }
          />
        )}

        {!isLoading && !isError && items.length === 0 && <EmptyState />}

        {!isLoading && !isError && items.length > 0 && (
          <>
            {/* First-approval orientation hint (shown above the list, only once) */}
            <FirstVisitCallout
              storageKey="ctx_os_inbox_hint"
              title="Your first approval"
              description="Read the summary, check for failure flags, then approve or reject with a reason."
              position="bottom-center"
            />

            <ul
              className="flex flex-col gap-4 max-w-2xl mx-auto"
              aria-label="Pending approval items"
            >
              <AnimatePresence mode="popLayout">
                {items.map((item) => (
                  <li key={item.id} className="list-none">
                    <ApprovalCard
                      item={item}
                      onApprove={(id) => approveMutation.mutate({ id })}
                      onReject={(id, reason) =>
                        rejectMutation.mutate({ id, reason })
                      }
                      isApproving={
                        approveMutation.isPending &&
                        approveMutation.variables?.id === item.id
                      }
                      isRejecting={
                        rejectMutation.isPending &&
                        rejectMutation.variables?.id === item.id
                      }
                    />
                  </li>
                ))}
              </AnimatePresence>
            </ul>
          </>
        )}
      </div>
    </div>
  );
}
