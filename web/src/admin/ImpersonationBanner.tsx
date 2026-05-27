/**
 * ImpersonationBanner — fixed amber top banner shown during impersonation.
 *
 * - Only visible when isImpersonating === true
 * - Shows target tenant name + "read-only" label
 * - "End impersonation" button calls endImpersonation()
 * - data-testid="impersonation-banner" for E2E targeting
 */
import { useImpersonation } from '@/lib/hooks/useImpersonation';

export default function ImpersonationBanner() {
  const { isImpersonating, targetTenantName, endImpersonation } = useImpersonation();

  if (!isImpersonating) return null;

  return (
    <div
      data-testid="impersonation-banner"
      style={{ position: 'fixed', top: 0, zIndex: 9999, width: '100%' }}
      className="flex items-center justify-between gap-4 bg-amber-400 px-4 py-2.5 shadow-md"
      role="alert"
      aria-live="polite"
    >
      <div className="flex items-center gap-2 text-sm font-medium text-amber-900">
        {/* Warning icon */}
        <svg
          viewBox="0 0 20 20"
          className="h-4 w-4 shrink-0 text-amber-800"
          fill="currentColor"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z"
            clipRule="evenodd"
          />
        </svg>
        <span>
          Impersonating:{' '}
          <strong>{targetTenantName ?? 'unknown org'}</strong>
          {' — '}
          <span className="font-normal opacity-80">read-only</span>
        </span>
      </div>

      <button
        type="button"
        onClick={() => void endImpersonation()}
        className={[
          'rounded-md bg-amber-800 px-3 py-1 text-xs font-semibold text-white',
          'transition-colors hover:bg-amber-900',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-900 focus-visible:ring-offset-1',
        ].join(' ')}
      >
        End impersonation
      </button>
    </div>
  );
}
