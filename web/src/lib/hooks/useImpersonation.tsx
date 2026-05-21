/**
 * useImpersonation — in-memory impersonation token management.
 *
 * - Stores token in a React ref (NOT localStorage or sessionStorage)
 * - startImpersonation(): sets token, schedules auto-expiry
 * - endImpersonation(): clears token, calls DELETE /admin/impersonate/revoke
 * - Exposes isImpersonating + impersonationToken for header injection
 */
import {
  createContext,
  useContext,
  useRef,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
  type FC,
} from 'react';
import { revokeImpersonation } from '@/lib/api/admin';

// ── Types ──────────────────────────────────────────────────────────────────────

export interface ImpersonationContextValue {
  /** The active impersonation token, or null when not impersonating. */
  impersonationToken: string | null;
  /** Whether an impersonation session is currently active. */
  isImpersonating: boolean;
  /** Target org display name (set alongside the token). */
  targetTenantName: string | null;
  /**
   * Activate an impersonation session.
   * @param token    - Short-lived HS256 token from POST /admin/impersonate/:orgId
   * @param expiresAt - ISO datetime string; auto-ends the session at this time
   */
  startImpersonation: (token: string, expiresAt: string, targetName?: string) => void;
  /** Deactivate impersonation and revoke the token server-side (best-effort). */
  endImpersonation: () => Promise<void>;
}

// ── Context ────────────────────────────────────────────────────────────────────

const ImpersonationContext = createContext<ImpersonationContextValue | null>(null);

// ── Provider ───────────────────────────────────────────────────────────────────

/**
 * ImpersonationProvider — wrap the application root to enable impersonation.
 */
export const ImpersonationProvider: FC<{ children: ReactNode }> = ({ children }) => {
  // Token lives in a ref so it never leaks into storage
  const tokenRef = useRef<string | null>(null);

  // Reactive state (drives header injection and UI)
  const [impersonationToken, setImpersonationToken] = useState<string | null>(null);
  const [targetTenantName, setTargetTenantName] = useState<string | null>(null);

  // Auto-expiry timer handle
  const expiryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const endImpersonation = useCallback(async () => {
    // Clear the timer if it hasn't fired yet
    if (expiryTimerRef.current !== null) {
      clearTimeout(expiryTimerRef.current);
      expiryTimerRef.current = null;
    }

    tokenRef.current = null;
    setImpersonationToken(null);
    setTargetTenantName(null);

    // Best-effort revocation — never block the UI on this
    try {
      await revokeImpersonation();
    } catch {
      // Swallow — the session will expire server-side regardless
    }
  }, []);

  const startImpersonation = useCallback(
    (token: string, expiresAt: string, targetName?: string) => {
      // Clear any previous session
      if (expiryTimerRef.current !== null) {
        clearTimeout(expiryTimerRef.current);
      }

      tokenRef.current = token;
      setImpersonationToken(token);
      setTargetTenantName(targetName ?? null);

      // Schedule automatic expiry
      const msUntilExpiry = new Date(expiresAt).getTime() - Date.now();
      if (msUntilExpiry > 0) {
        expiryTimerRef.current = setTimeout(() => {
          void endImpersonation();
        }, msUntilExpiry);
      } else {
        // Token already expired — don't activate
        void endImpersonation();
      }
    },
    [endImpersonation]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (expiryTimerRef.current !== null) {
        clearTimeout(expiryTimerRef.current);
      }
    };
  }, []);

  return (
    <ImpersonationContext.Provider
      value={{
        impersonationToken,
        isImpersonating: impersonationToken !== null,
        targetTenantName,
        startImpersonation,
        endImpersonation,
      }}
    >
      {children}
    </ImpersonationContext.Provider>
  );
};

// ── Hook ───────────────────────────────────────────────────────────────────────

/**
 * useImpersonation — access the impersonation context.
 *
 * Must be used inside <ImpersonationProvider>.
 */
export function useImpersonation(): ImpersonationContextValue {
  const ctx = useContext(ImpersonationContext);
  if (ctx === null) {
    throw new Error('useImpersonation must be used within <ImpersonationProvider>');
  }
  return ctx;
}

/**
 * getImpersonationTokenRef — returns the ref used internally.
 * Exposed for use by the axios interceptor so it doesn't need React context.
 *
 * This is the recommended pattern for injecting auth tokens into an axios
 * interceptor without re-registering the interceptor on every render.
 */
let _globalTokenRef: React.MutableRefObject<string | null> | null = null;

export function registerImpersonationTokenRef(
  ref: React.MutableRefObject<string | null>
): void {
  _globalTokenRef = ref;
}

export function getImpersonationToken(): string | null {
  return _globalTokenRef?.current ?? null;
}
