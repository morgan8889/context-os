/**
 * T016: Failing unit tests for useOnboardingSession hook
 *
 * These tests are written BEFORE the implementation exists and will
 * fail until T017 (implementation) is complete.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { createElement } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// ── Mocks ─────────────────────────────────────────────────────────────────────

vi.mock('@/lib/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

import { apiClient } from '@/lib/api/client';

const mockSession = {
  tenant_id: 'tenant-abc',
  current_step: 'survey' as const,
  survey_answer: null,
  connected_integrations: [],
  scope_selection: null,
  ingest_job_id: null,
  activated_at: null,
};

function makeWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: 0 } },
  });
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: qc }, children);
}

// ── Tests ──────────────────────────────────────────────────────────────────────

describe('useOnboardingSession', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns currentStep correctly after fetch resolves', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockSession });

    const { useOnboardingSession } = await import(
      '@/lib/hooks/useOnboardingSession'
    );

    const { result } = renderHook(() => useOnboardingSession(), {
      wrapper: makeWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.session?.current_step).toBe('survey');
  });

  it('returns isLoading: true during initial fetch', async () => {
    // Never resolves so we can catch the loading state
    vi.mocked(apiClient.get).mockReturnValueOnce(new Promise(() => {}));

    const { useOnboardingSession } = await import(
      '@/lib/hooks/useOnboardingSession'
    );

    const { result } = renderHook(() => useOnboardingSession(), {
      wrapper: makeWrapper(),
    });

    expect(result.current.isLoading).toBe(true);
  });

  it('mutateAdvance survey calls POST /onboarding/survey with correct payload', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockSession });
    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: {} });

    const { useSurveyMutation } = await import(
      '@/lib/hooks/useOnboardingSession'
    );

    const qc = new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: 0 } },
    });
    const wrapper = ({ children }: { children: React.ReactNode }) =>
      createElement(QueryClientProvider, { client: qc }, children);

    const { result } = renderHook(() => useSurveyMutation(), { wrapper });

    await act(async () => {
      result.current.mutate({ option: 'briefings', free_text: undefined });
    });

    expect(apiClient.post).toHaveBeenCalledWith('/onboarding/survey', {
      option: 'briefings',
      free_text: undefined,
    });
  });

  it('session is re-fetched (query invalidated) after survey mutation', async () => {
    const updatedSession = { ...mockSession, survey_answer: { option: 'briefings' }, current_step: 'connect' as const };

    vi.mocked(apiClient.get)
      .mockResolvedValueOnce({ data: mockSession })
      .mockResolvedValueOnce({ data: updatedSession });
    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: {} });

    const { useOnboardingSession, useSurveyMutation } = await import(
      '@/lib/hooks/useOnboardingSession'
    );

    const qc = new QueryClient({
      defaultOptions: { queries: { retry: false, staleTime: 0 }, mutations: { retry: 0 } },
    });
    const wrapper = ({ children }: { children: React.ReactNode }) =>
      createElement(QueryClientProvider, { client: qc }, children);

    const sessionHook = renderHook(() => useOnboardingSession(), { wrapper });
    const mutationHook = renderHook(() => useSurveyMutation(), { wrapper });

    await waitFor(() => expect(sessionHook.result.current.isLoading).toBe(false));

    await act(async () => {
      await mutationHook.result.current.mutateAsync({ option: 'briefings' });
    });

    // After mutation success, query should be invalidated and re-fetched
    await waitFor(() =>
      expect(sessionHook.result.current.session?.current_step).toBe('connect')
    );

    // GET must have been called at least twice (initial + refetch after invalidation)
    expect(apiClient.get).toHaveBeenCalledTimes(2);
  });
});
