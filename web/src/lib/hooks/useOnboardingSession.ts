/**
 * useOnboardingSession — TanStack Query hooks for the onboarding flow.
 *
 * Provides:
 *   - useOnboardingSession(): session data + loading state
 *   - useSurveyMutation():    POST /onboarding/survey
 *   - useScopeMutation():     POST /onboarding/scope
 *   - useActivationMutation(): POST /onboarding/activation
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';

// ── Types ──────────────────────────────────────────────────────────────────────

export interface OnboardingSession {
  tenant_id: string;
  current_step: 'survey' | 'connect' | 'scope' | 'ingest' | 'briefing' | 'activated';
  survey_answer: { option: string; free_text?: string } | null;
  connected_integrations: string[];
  scope_selection: {
    jira_projects?: string[];
    github_repos?: string[];
    slack_channels?: string[];
  } | null;
  ingest_job_id: string | null;
  activated_at: string | null;
}

export interface SurveyPayload {
  option: string;
  free_text?: string | undefined;
}

export interface ScopePayload {
  jira_projects?: string[] | undefined;
  github_repos?: string[] | undefined;
  slack_channels?: string[] | undefined;
}

export interface ActivationPayload {
  briefing_id: string;
  accepted_as_is: boolean;
}

// ── Query Keys ─────────────────────────────────────────────────────────────────

export const onboardingKeys = {
  all: ['onboarding'] as const,
  session: () => [...onboardingKeys.all, 'session'] as const,
  ingestStatus: () => [...onboardingKeys.all, 'ingest-status'] as const,
} as const;

function getMockStep(): OnboardingSession['current_step'] | null {
  if (typeof window === 'undefined') return null;
  const mock = new URLSearchParams(window.location.search).get('mock');
  const steps: OnboardingSession['current_step'][] = [
    'survey',
    'connect',
    'scope',
    'ingest',
    'briefing',
    'activated',
  ];
  return steps.includes(mock as OnboardingSession['current_step'])
    ? (mock as OnboardingSession['current_step'])
    : null;
}

function mockSession(step: OnboardingSession['current_step']): OnboardingSession {
  return {
    tenant_id: 'org_visual_test',
    current_step: step,
    survey_answer: step === 'survey' ? null : { option: 'briefings' },
    connected_integrations:
      step === 'survey' || step === 'connect' ? [] : ['github'],
    scope_selection:
      step === 'scope' || step === 'ingest' || step === 'briefing' || step === 'activated'
        ? { github_repos: ['context-os'] }
        : null,
    ingest_job_id:
      step === 'ingest' || step === 'briefing' || step === 'activated'
        ? 'ingest_visual_test'
        : null,
    activated_at: step === 'activated' ? new Date(0).toISOString() : null,
  };
}

// ── Hooks ─────────────────────────────────────────────────────────────────────

/**
 * Fetches the current onboarding session state.
 *
 * @returns session data, loading state, and a refetch function.
 */
export function useOnboardingSession() {
  const mockStep = getMockStep();
  const { data: session, isLoading, refetch } = useQuery<OnboardingSession, Error>(
    {
      queryKey: onboardingKeys.session(),
      queryFn: async () => {
        if (mockStep) return mockSession(mockStep);
        const response = await apiClient.get<OnboardingSession>('/onboarding/session');
        return response.data;
      },
      ...(mockStep ? { refetchInterval: false as const } : {}),
      staleTime: 0,
    }
  );

  return { session: session ?? null, isLoading, refetch };
}

/**
 * Mutation for submitting the survey step.
 * Invalidates the session query on success.
 */
export function useSurveyMutation() {
  const queryClient = useQueryClient();

  return useMutation<unknown, Error, SurveyPayload>({
    mutationFn: async (payload) => {
      const response = await apiClient.post('/onboarding/survey', payload);
      return response.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: onboardingKeys.session() });
    },
  });
}

/**
 * Mutation for submitting the scope selection step.
 * Invalidates the session query on success.
 */
export function useScopeMutation() {
  const queryClient = useQueryClient();

  return useMutation<unknown, Error, ScopePayload>({
    mutationFn: async (payload) => {
      const response = await apiClient.post('/onboarding/scope', payload);
      return response.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: onboardingKeys.session() });
    },
  });
}

/**
 * Mutation for approving the first briefing and activating the tenant.
 * Invalidates the session query on success.
 */
export function useActivationMutation() {
  const queryClient = useQueryClient();

  return useMutation<unknown, Error, ActivationPayload>({
    mutationFn: async (payload) => {
      const response = await apiClient.post('/onboarding/activation', payload);
      return response.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: onboardingKeys.session() });
    },
  });
}
