/**
 * AdminShell — platform-operator admin panel container.
 *
 * - Checks Clerk custom claim platform_operator === true
 * - Renders 403 for non-PO users
 * - Renders sidebar nav (Funnel, Survey Responses) + outlet for PO users
 */
import { type ReactNode } from 'react';
import { useUser } from '@clerk/react';
import { Link, useLocation, Outlet } from 'react-router-dom';

// ── 403 Page ───────────────────────────────────────────────────────────────────

function AccessDenied() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-neutral-50 px-4 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
        <svg
          viewBox="0 0 24 24"
          className="h-8 w-8 text-red-600"
          fill="currentColor"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M12 1.5a5.25 5.25 0 00-5.25 5.25v3a3 3 0 00-3 3v6.75a3 3 0 003 3h10.5a3 3 0 003-3v-6.75a3 3 0 00-3-3v-3c0-2.9-2.35-5.25-5.25-5.25zm3.75 8.25v-3a3.75 3.75 0 10-7.5 0v3h7.5z"
            clipRule="evenodd"
          />
        </svg>
      </div>
      <h1 className="mb-2 text-xl font-bold text-neutral-900">Access denied</h1>
      <p className="text-sm text-neutral-500">
        This area requires platform operator permissions.
      </p>
    </div>
  );
}

// ── Nav Item ───────────────────────────────────────────────────────────────────

function NavItem({ to, label, icon }: { to: string; label: string; icon: ReactNode }) {
  const location = useLocation();
  const isActive = location.pathname.startsWith(to);

  return (
    <Link
      to={to}
      className={[
        'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium',
        'transition-colors duration-100',
        isActive
          ? 'bg-blue-50 text-blue-700'
          : 'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900',
      ].join(' ')}
      aria-current={isActive ? 'page' : undefined}
    >
      <span className="h-4 w-4 shrink-0" aria-hidden="true">
        {icon}
      </span>
      {label}
    </Link>
  );
}

// ── Shell ──────────────────────────────────────────────────────────────────────

export default function AdminShell() {
  const { user, isLoaded } = useUser();

  if (!isLoaded) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  // Check platform_operator custom claim
  const isPlatformOperator =
    (user?.publicMetadata as Record<string, unknown> | undefined)?.platform_operator === true ||
    // Also check unsafe metadata (development convenience)
    (user?.unsafeMetadata as Record<string, unknown> | undefined)?.platform_operator === true;

  if (!isPlatformOperator) {
    return <AccessDenied />;
  }

  return (
    <div className="flex min-h-screen bg-neutral-50">
      {/* Sidebar */}
      <aside className="flex w-56 shrink-0 flex-col border-r border-neutral-200 bg-white px-3 py-6">
        {/* Logo */}
        <div className="mb-8 flex items-center gap-2 px-3">
          <div className="h-6 w-6 rounded-md bg-blue-600" aria-hidden="true" />
          <span className="text-sm font-semibold text-neutral-900">Admin Panel</span>
        </div>

        {/* Nav */}
        <nav className="space-y-1" aria-label="Admin navigation">
          <NavItem
            to="/admin/funnel"
            label="Onboarding Funnel"
            icon={
              <svg viewBox="0 0 16 16" fill="currentColor">
                <path d="M1.5 2A.5.5 0 012 1.5h12a.5.5 0 010 1H2A.5.5 0 011.5 2zM3 5.5a.5.5 0 01.5-.5h9a.5.5 0 010 1h-9a.5.5 0 01-.5-.5zm1.5 2.5a.5.5 0 000 1h7a.5.5 0 000-1h-7zm1 3a.5.5 0 000 1h5a.5.5 0 000-1h-5z" />
              </svg>
            }
          />
          <NavItem
            to="/admin/survey-responses"
            label="Survey Responses"
            icon={
              <svg viewBox="0 0 16 16" fill="currentColor">
                <path d="M0 2a2 2 0 012-2h12a2 2 0 012 2v8a2 2 0 01-2 2H4.414a1 1 0 00-.707.293l-2.414 2.414A.5.5 0 010 14.414V2zm3.5 1a.5.5 0 000 1h9a.5.5 0 000-1h-9zm0 2.5a.5.5 0 000 1h9a.5.5 0 000-1h-9zm0 2.5a.5.5 0 000 1h5a.5.5 0 000-1h-5z" />
              </svg>
            }
          />
        </nav>

        {/* Footer */}
        <div className="mt-auto pt-6">
          <div className="rounded-lg bg-amber-50 border border-amber-200 px-3 py-2.5">
            <p className="text-xs font-medium text-amber-800">Platform Operator</p>
            <p className="text-xs text-amber-600 truncate">{user?.primaryEmailAddress?.emailAddress}</p>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
