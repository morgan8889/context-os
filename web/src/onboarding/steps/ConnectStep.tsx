/**
 * ConnectStep — OAuth integration cards for Jira, GitHub, and Slack.
 *
 * - Opens OAuth popup for each source
 * - Polls GET /onboarding/session every 2s to detect connections
 * - Shows green checkmark on connected sources
 * - "Continue" enabled when at least one integration is connected
 */
import { type ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { onboardingKeys } from '@/lib/hooks/useOnboardingSession';
import type { OnboardingSession } from '@/lib/hooks/useOnboardingSession';

// ── Integration Config ─────────────────────────────────────────────────────────

interface Integration {
  source: string;
  name: string;
  description: string;
  icon: ReactNode;
}

const INTEGRATIONS: Integration[] = [
  {
    source: 'jira',
    name: 'Jira',
    description: 'Pull initiatives, epics, and cross-team dependencies from your projects.',
    icon: (
      <svg viewBox="0 0 32 32" className="h-8 w-8" aria-hidden="true">
        <defs>
          <linearGradient id="jira-grad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#2684FF" />
            <stop offset="100%" stopColor="#0052CC" />
          </linearGradient>
        </defs>
        <rect width="32" height="32" rx="6" fill="url(#jira-grad)" />
        <path
          d="M17.19 6.26L10.31 13.1a1.73 1.73 0 000 2.45l6.88 6.84a1.73 1.73 0 002.45 0l6.88-6.84a1.73 1.73 0 000-2.45l-6.88-6.84a1.73 1.73 0 00-2.45 0z"
          fill="white"
          opacity="0.9"
        />
        <path
          d="M17.19 22.39l-6.88-6.84a1.73 1.73 0 010-2.45l6.88 6.84a1.73 1.73 0 002.45 0l6.88-6.84a1.73 1.73 0 010 2.45l-6.88 6.84a1.73 1.73 0 01-2.45 0z"
          fill="white"
          opacity="0.4"
        />
      </svg>
    ),
  },
  {
    source: 'github',
    name: 'GitHub',
    description: 'Sync pull requests, code reviews, and repository signals.',
    icon: (
      <svg viewBox="0 0 32 32" className="h-8 w-8" aria-hidden="true">
        <rect width="32" height="32" rx="6" fill="#24292E" />
        <path
          fillRule="evenodd"
          clipRule="evenodd"
          d="M16 5C9.925 5 5 9.925 5 16c0 4.867 3.152 8.997 7.524 10.452.55.101.75-.238.75-.528 0-.261-.01-1.126-.015-2.044-3.06.665-3.707-1.474-3.707-1.474-.501-1.272-1.224-1.61-1.224-1.61-.999-.683.076-.669.076-.669 1.105.078 1.686 1.134 1.686 1.134.981 1.68 2.574 1.195 3.201.914.1-.71.384-1.195.699-1.47-2.442-.278-5.008-1.22-5.008-5.432 0-1.2.428-2.18 1.133-2.948-.114-.279-.491-1.396.106-2.91 0 0 .924-.296 3.025 1.127A10.54 10.54 0 0116 9.756c.936.004 1.879.127 2.759.37 2.1-1.423 3.021-1.127 3.021-1.127.599 1.514.222 2.631.108 2.91.706.768 1.13 1.748 1.13 2.948 0 4.222-2.57 5.151-5.018 5.42.394.34.745 1.01.745 2.036 0 1.47-.013 2.657-.013 3.017 0 .293.198.635.754.527C23.85 24.994 27 20.866 27 16c0-6.075-4.925-11-11-11z"
          fill="white"
        />
      </svg>
    ),
  },
  {
    source: 'slack',
    name: 'Slack',
    description: 'Capture decision threads and team signals from your channels.',
    icon: (
      <svg viewBox="0 0 32 32" className="h-8 w-8" aria-hidden="true">
        <rect width="32" height="32" rx="6" fill="#4A154B" />
        <g transform="translate(6 6)">
          <path d="M5.4 14.4a2 2 0 110 4 2 2 0 010-4zm0-4.8a2 2 0 110 4 2 2 0 010-4zm4.8 0a2 2 0 110 4 2 2 0 010-4zm0-4.8a2 2 0 110 4 2 2 0 010-4zM14.6 9.6a2 2 0 110 4 2 2 0 010-4zm0 4.8a2 2 0 110 4 2 2 0 010-4zm-4.8 0a2 2 0 110 4 2 2 0 010-4zm0 4.8a2 2 0 110 4 2 2 0 010-4z" fill="white" />
        </g>
      </svg>
    ),
  },
];

// ── Checkmark Icon ─────────────────────────────────────────────────────────────

function CheckBadge() {
  return (
    <span
      className="flex h-6 w-6 items-center justify-center rounded-full bg-green-500 text-white"
      aria-label="Connected"
    >
      <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" fill="currentColor" aria-hidden="true">
        <path d="M13.485 1.431a1.473 1.473 0 0 0-2.084 0l-6.25 6.25-.952-.952a1.473 1.473 0 1 0-2.083 2.083l2 2a1.473 1.473 0 0 0 2.083 0l7.292-7.292a1.473 1.473 0 0 0 0-2.083z" />
      </svg>
    </span>
  );
}

// ── Component ──────────────────────────────────────────────────────────────────

interface ConnectStepProps {
  /** Injected in tests to skip the real query. */
  connectedIntegrations?: string[] | undefined;
  onContinue?: (() => void) | undefined;
}

export default function ConnectStep({ connectedIntegrations: propConnected, onContinue }: ConnectStepProps) {
  // Poll every 2s to detect newly connected integrations
  const { data: session } = useQuery<OnboardingSession, Error>({
    queryKey: onboardingKeys.session(),
    queryFn: async () => {
      const response = await apiClient.get<OnboardingSession>('/onboarding/session');
      return response.data;
    },
    refetchInterval: 2_000,
    staleTime: 0,
    enabled: propConnected === undefined,
  });

  const connected = propConnected ?? session?.connected_integrations ?? [];
  const canContinue = connected.length >= 1;

  function openOAuth(source: string) {
    window.open(
      `/oauth/connect/${source}/start`,
      `oauth_${source}`,
      'width=600,height=700,scrollbars=yes,resizable=yes'
    );
  }

  return (
    <div className="rounded-2xl border border-neutral-200 bg-white p-8 shadow-sm">
      <h2 className="mb-1 text-xl font-bold text-neutral-900">Connect your tools</h2>
      <p className="mb-6 text-sm text-neutral-500">
        Context OS reads data from your existing tools — it never writes. Connect at least one to
        continue.
      </p>

      <div className="space-y-4">
        {INTEGRATIONS.map((integration) => {
          const isConnected = connected.includes(integration.source);

          return (
            <div
              key={integration.source}
              className={[
                'flex items-start gap-4 rounded-xl border p-5 transition-colors duration-150',
                isConnected ? 'border-green-200 bg-green-50' : 'border-neutral-200 bg-white',
              ].join(' ')}
            >
              {/* Icon */}
              <div className="shrink-0 pt-0.5">{integration.icon}</div>

              {/* Text */}
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-neutral-900">
                    {integration.name}
                  </span>
                  {isConnected && <CheckBadge />}
                </div>
                <p className="mt-0.5 text-xs text-neutral-500">{integration.description}</p>

                {/* Action */}
                {!isConnected && (
                  <div className="mt-3 flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => openOAuth(integration.source)}
                      className={[
                        'rounded-lg border border-neutral-200 bg-white px-4 py-1.5',
                        'text-xs font-medium text-neutral-700 shadow-sm',
                        'transition-all duration-150 hover:border-neutral-300 hover:bg-neutral-50',
                        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500',
                      ].join(' ')}
                    >
                      Connect {integration.name}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        /* Skip: no-op, user moves on without this integration */
                      }}
                      className="text-xs text-neutral-400 underline-offset-2 hover:text-neutral-600 hover:underline"
                    >
                      Skip (not recommended)
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-8">
        <button
          type="button"
          disabled={!canContinue}
          onClick={onContinue}
          className={[
            'flex w-full items-center justify-center rounded-xl py-3 text-sm font-semibold',
            'transition-all duration-150 focus-visible:outline-none',
            'focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1',
            canContinue
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'cursor-not-allowed bg-neutral-100 text-neutral-400',
          ].join(' ')}
        >
          Continue
        </button>
        {!canContinue && (
          <p className="mt-2 text-center text-xs text-neutral-400">
            Connect at least one tool to continue
          </p>
        )}
      </div>
    </div>
  );
}
