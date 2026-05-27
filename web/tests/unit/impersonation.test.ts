/**
 * T043: Failing unit tests for useImpersonation hook.
 *
 * Written BEFORE implementation. All tests must fail until T044.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { createElement } from 'react';

// Mock admin API
vi.mock('@/lib/api/admin', () => ({
  revokeImpersonation: vi.fn().mockResolvedValue(undefined),
  startImpersonation: vi.fn(),
  fetchFunnel: vi.fn(),
  fetchSurveyResponses: vi.fn(),
}));

// Mock the apiClient to spy on header injection
vi.mock('@/lib/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
  setTokenProvider: vi.fn(),
  setImpersonationTokenProvider: vi.fn(),
}));

import { revokeImpersonation } from '@/lib/api/admin';

// ── Tests ──────────────────────────────────────────────────────────────────────

describe('useImpersonation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('starts with token: null and isImpersonating: false', async () => {
    const { ImpersonationProvider, useImpersonation } = await import(
      '@/lib/hooks/useImpersonation'
    );

    const { result } = renderHook(() => useImpersonation(), {
      wrapper: ({ children }) => createElement(ImpersonationProvider, {}, children),
    });

    expect(result.current.impersonationToken).toBeNull();
    expect(result.current.isImpersonating).toBe(false);
  });

  it('startImpersonation sets token in memory and isImpersonating: true', async () => {
    const { ImpersonationProvider, useImpersonation } = await import(
      '@/lib/hooks/useImpersonation'
    );

    const { result } = renderHook(() => useImpersonation(), {
      wrapper: ({ children }) => createElement(ImpersonationProvider, {}, children),
    });

    const futureExpiry = new Date(Date.now() + 3_600_000).toISOString();

    act(() => {
      result.current.startImpersonation('tok-abc-123', futureExpiry);
    });

    expect(result.current.impersonationToken).toBe('tok-abc-123');
    expect(result.current.isImpersonating).toBe(true);
  });

  it('endImpersonation clears token and calls DELETE /admin/impersonate/revoke', async () => {
    const { ImpersonationProvider, useImpersonation } = await import(
      '@/lib/hooks/useImpersonation'
    );

    const { result } = renderHook(() => useImpersonation(), {
      wrapper: ({ children }) => createElement(ImpersonationProvider, {}, children),
    });

    const futureExpiry = new Date(Date.now() + 3_600_000).toISOString();

    act(() => {
      result.current.startImpersonation('tok-abc-123', futureExpiry);
    });

    await act(async () => {
      await result.current.endImpersonation();
    });

    expect(result.current.impersonationToken).toBeNull();
    expect(result.current.isImpersonating).toBe(false);
    expect(revokeImpersonation).toHaveBeenCalledTimes(1);
  });

  it('token is stored in memory ref, not exposed to localStorage', async () => {
    const { ImpersonationProvider, useImpersonation } = await import(
      '@/lib/hooks/useImpersonation'
    );

    const localStorageSpy = vi.spyOn(Storage.prototype, 'setItem');
    const sessionStorageSpy = vi.spyOn(Storage.prototype, 'setItem');

    const { result } = renderHook(() => useImpersonation(), {
      wrapper: ({ children }) => createElement(ImpersonationProvider, {}, children),
    });

    const futureExpiry = new Date(Date.now() + 3_600_000).toISOString();

    act(() => {
      result.current.startImpersonation('tok-secret', futureExpiry);
    });

    // Token must NOT be in storage
    expect(localStorageSpy).not.toHaveBeenCalledWith(
      expect.stringContaining('impersonat'),
      expect.any(String)
    );
    expect(sessionStorageSpy).not.toHaveBeenCalledWith(
      expect.stringContaining('impersonat'),
      expect.any(String)
    );

    localStorageSpy.mockRestore();
    sessionStorageSpy.mockRestore();
  });
});
