/**
 * ScopeStep — select which projects/repos/channels to include.
 *
 * - Fetches available resources per connected source
 * - Pre-selects all returned items (allow deselection)
 * - Shows selection count
 * - On confirm: calls useScopeMutation
 */
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { useOnboardingSession, useScopeMutation } from '@/lib/hooks/useOnboardingSession';

// ── Types ──────────────────────────────────────────────────────────────────────

interface AvailableResources {
  jira_projects: Array<{ id: string; name: string }>;
  github_repos: Array<{ id: string; name: string }>;
  slack_channels: Array<{ id: string; name: string }>;
}

// ── Resource Checkbox Group ────────────────────────────────────────────────────

interface ResourceGroupProps {
  title: string;
  items: Array<{ id: string; name: string }>;
  selectedIds: Set<string>;
  onToggle: (id: string) => void;
  countLabel: string;
}

function ResourceGroup({ title, items, selectedIds, onToggle, countLabel }: ResourceGroupProps) {
  if (items.length === 0) return null;

  return (
    <section>
      <div className="mb-2 flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-neutral-700">{title}</h3>
        <span className="text-xs text-neutral-400">{countLabel}</span>
      </div>
      <div className="space-y-2 rounded-xl border border-neutral-200 p-1">
        {items.map((item) => {
          const checked = selectedIds.has(item.id);
          return (
            <label
              key={item.id}
              className={[
                'flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5',
                'transition-colors duration-100 hover:bg-neutral-50',
              ].join(' ')}
            >
              <input
                type="checkbox"
                checked={checked}
                onChange={() => onToggle(item.id)}
                className="h-4 w-4 rounded border-neutral-300 accent-blue-600"
              />
              <span className="text-sm text-neutral-800">{item.name}</span>
            </label>
          );
        })}
      </div>
    </section>
  );
}

// ── Skeleton ───────────────────────────────────────────────────────────────────

function ResourcesSkeleton() {
  return (
    <div className="space-y-4">
      {[0, 1, 2].map((i) => (
        <div key={i} className="space-y-2 rounded-xl border border-neutral-100 p-3">
          <div className="h-4 w-1/3 animate-pulse rounded bg-neutral-200" />
          {[0, 1, 2].map((j) => (
            <div key={j} className="h-9 animate-pulse rounded-lg bg-neutral-100" />
          ))}
        </div>
      ))}
    </div>
  );
}

// ── Component ──────────────────────────────────────────────────────────────────

export default function ScopeStep() {
  const { session } = useOnboardingSession();
  const { mutate, isPending } = useScopeMutation();

  const connected = session?.connected_integrations ?? [];

  const { data: resources, isLoading } = useQuery<AvailableResources, Error>({
    queryKey: ['onboarding', 'resources'],
    queryFn: async () => {
      const results = await Promise.all(
        connected.map((source) =>
          apiClient
            .get<{ items: Array<{ id: string; name: string }> }>(
              `/api/v1/integrations/${source}/resources`
            )
            .then((r) => ({ source, items: r.data.items }))
            .catch(() => ({ source, items: [] as Array<{ id: string; name: string }> }))
        )
      );

      const out: AvailableResources = {
        jira_projects: [],
        github_repos: [],
        slack_channels: [],
      };

      for (const { source, items } of results) {
        if (source === 'jira') out.jira_projects = items;
        if (source === 'github') out.github_repos = items;
        if (source === 'slack') out.slack_channels = items;
      }

      return out;
    },
    enabled: connected.length > 0,
  });

  // Pre-select everything on load
  const [selectedJira, setSelectedJira] = useState<Set<string>>(new Set());
  const [selectedGithub, setSelectedGithub] = useState<Set<string>>(new Set());
  const [selectedSlack, setSelectedSlack] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (resources) {
      setSelectedJira(new Set(resources.jira_projects.map((p) => p.id)));
      setSelectedGithub(new Set(resources.github_repos.map((r) => r.id)));
      setSelectedSlack(new Set(resources.slack_channels.map((c) => c.id)));
    }
  }, [resources]);

  function toggle(set: Set<string>, setFn: React.Dispatch<React.SetStateAction<Set<string>>>, id: string) {
    setFn((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  const totalSelected = selectedJira.size + selectedGithub.size + selectedSlack.size;
  const jiraCount = resources?.jira_projects.length ?? 0;
  const githubCount = resources?.github_repos.length ?? 0;
  const slackCount = resources?.slack_channels.length ?? 0;

  function buildSummary() {
    const parts: string[] = [];
    if (jiraCount > 0) parts.push(`${selectedJira.size} project${selectedJira.size !== 1 ? 's' : ''}`);
    if (githubCount > 0) parts.push(`${selectedGithub.size} repo${selectedGithub.size !== 1 ? 's' : ''}`);
    if (slackCount > 0) parts.push(`${selectedSlack.size} channel${selectedSlack.size !== 1 ? 's' : ''}`);
    return parts.join(', ') || 'Nothing selected';
  }

  function handleConfirm() {
    mutate({
      jira_projects: jiraCount > 0 ? Array.from(selectedJira) : undefined,
      github_repos: githubCount > 0 ? Array.from(selectedGithub) : undefined,
      slack_channels: slackCount > 0 ? Array.from(selectedSlack) : undefined,
    });
  }

  return (
    <div className="rounded-2xl border border-neutral-200 bg-white p-8 shadow-sm">
      <h2 className="mb-1 text-xl font-bold text-neutral-900">Choose what to sync</h2>
      <p className="mb-2 text-sm text-neutral-500">
        We'll index the selected resources to build your first briefing.
      </p>

      {/* Selection summary */}
      <div className="mb-6 rounded-lg bg-blue-50 px-4 py-2.5 text-sm font-medium text-blue-700">
        {buildSummary()} selected
      </div>

      {isLoading ? (
        <ResourcesSkeleton />
      ) : (
        <div className="space-y-5">
          {jiraCount > 0 && (
            <ResourceGroup
              title="Jira Projects"
              items={resources?.jira_projects ?? []}
              selectedIds={selectedJira}
              onToggle={(id) => toggle(selectedJira, setSelectedJira, id)}
              countLabel={`${selectedJira.size}/${jiraCount} selected`}
            />
          )}
          {githubCount > 0 && (
            <ResourceGroup
              title="GitHub Repositories"
              items={resources?.github_repos ?? []}
              selectedIds={selectedGithub}
              onToggle={(id) => toggle(selectedGithub, setSelectedGithub, id)}
              countLabel={`${selectedGithub.size}/${githubCount} selected`}
            />
          )}
          {slackCount > 0 && (
            <ResourceGroup
              title="Slack Channels"
              items={resources?.slack_channels ?? []}
              selectedIds={selectedSlack}
              onToggle={(id) => toggle(selectedSlack, setSelectedSlack, id)}
              countLabel={`${selectedSlack.size}/${slackCount} selected`}
            />
          )}
          {jiraCount === 0 && githubCount === 0 && slackCount === 0 && (
            <p className="py-4 text-center text-sm text-neutral-400">
              No resources found. Go back and connect an integration.
            </p>
          )}
        </div>
      )}

      <div className="mt-8">
        <button
          type="button"
          onClick={handleConfirm}
          disabled={totalSelected === 0 || isPending || isLoading}
          className={[
            'flex w-full items-center justify-center gap-2 rounded-xl py-3 text-sm font-semibold',
            'transition-all duration-150 focus-visible:outline-none',
            'focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1',
            totalSelected > 0 && !isPending && !isLoading
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
              Confirming…
            </>
          ) : (
            'Confirm and start sync'
          )}
        </button>
      </div>
    </div>
  );
}
