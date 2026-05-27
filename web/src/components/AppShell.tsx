import { type ReactNode, type MouseEvent } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { inboxKeys } from '@/lib/api/queryKeys';
import { Tooltip } from '@/design-system/components/Tooltip';
import type { ApiApprovalItem } from '@/types/api';

interface InboxListResponse {
  items: ApiApprovalItem[];
  next_cursor: string | null;
}

async function fetchInboxCount(): Promise<InboxListResponse> {
  const res = await apiClient.get<InboxListResponse>('/api/v1/inbox', {
    params: { status: 'pending' },
  });
  return res.data;
}

const INBOX_QUERY_KEY = inboxKeys.list({ status: 'pending' });

// ── Nav icons ─────────────────────────────────────────────────────────────────

function GalaxyIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <circle cx="10" cy="10" r="2" />
      <ellipse cx="10" cy="10" rx="8" ry="3" stroke="currentColor" strokeWidth="1.5" fill="none" transform="rotate(-30 10 10)" />
      <ellipse cx="10" cy="10" rx="8" ry="3" stroke="currentColor" strokeWidth="1.5" fill="none" transform="rotate(30 10 10)" />
    </svg>
  );
}

function TopologyIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <circle cx="10" cy="4" r="2" />
      <circle cx="4" cy="15" r="2" />
      <circle cx="16" cy="15" r="2" />
      <line x1="10" y1="6" x2="4" y2="13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="10" y1="6" x2="16" y2="13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function DecisionsIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <rect x="7" y="2" width="6" height="4" rx="1.5" fill="currentColor" />
      <line x1="10" y1="6" x2="10" y2="9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="5" y1="9" x2="15" y2="9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="5" y1="9" x2="5" y2="12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="15" y1="9" x2="15" y2="12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <rect x="2" y="12" width="6" height="4" rx="1.5" fill="currentColor" />
      <rect x="12" y="12" width="6" height="4" rx="1.5" fill="currentColor" />
    </svg>
  );
}

function InboxIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <rect x="2" y="3" width="16" height="14" rx="2" stroke="currentColor" strokeWidth="1.5" />
      <path d="M2 11h4l2 3h4l2-3h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function HelpIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="1.5" />
      <text x="8" y="12" textAnchor="middle" fontSize="9" fontWeight="600" fill="currentColor" fontFamily="sans-serif">?</text>
    </svg>
  );
}

// ── Nav item ──────────────────────────────────────────────────────────────────

interface NavItemProps {
  to: string;
  label: string;
  icon: ReactNode;
  badge?: number;
}

function NavItem({ to, label, icon, badge }: NavItemProps) {
  const { pathname } = useLocation();
  const isActive = pathname === to || pathname.startsWith(to + '/');

  return (
    <Tooltip content={label} side="right" delayDuration={400}>
      <NavLink
        to={to}
        aria-label={label}
        className="relative flex h-10 w-10 items-center justify-center rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
        style={{
          color: isActive ? 'oklch(95% 0 0)' : 'oklch(50% 0 0)',
          background: isActive ? 'oklch(100% 0 0 / 0.10)' : 'transparent',
        }}
      >
        {icon}
        {badge !== undefined && badge > 0 && (
          <span
            aria-label={`${badge} pending approvals`}
            className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full text-[9px] font-bold leading-none"
            style={{
              background: 'oklch(60% 0.22 25)',
              color: 'oklch(100% 0 0)',
            }}
          >
            {badge > 9 ? '9+' : badge}
          </span>
        )}
      </NavLink>
    </Tooltip>
  );
}

// ── AppShell ──────────────────────────────────────────────────────────────────

export default function AppShell() {
  const location = useLocation();
  const isInbox = location.pathname === '/inbox';

  const { data } = useQuery({
    queryKey: INBOX_QUERY_KEY,
    queryFn: fetchInboxCount,
    staleTime: 30_000,
    refetchInterval: 30_000,
  });

  const pendingCount = data?.items?.length ?? 0;

  return (
    <div className="flex h-screen w-screen overflow-hidden">
      {/* Sidebar */}
      <nav
        aria-label="Main navigation"
        className="relative flex h-full shrink-0 flex-col items-center py-3 gap-1"
        style={{
          width: 56,
          background: 'oklch(10% 0 0)',
          borderRight: '1px solid oklch(100% 0 0 / 0.08)',
          zIndex: 40,
        }}
      >
        <NavItem to="/galaxy" label="Galaxy" icon={<GalaxyIcon />} />
        <NavItem to="/topology" label="Topology" icon={<TopologyIcon />} />
        <NavItem to="/decisions" label="Decisions" icon={<DecisionsIcon />} />
        <NavItem
          to="/inbox"
          label="Inbox"
          icon={<InboxIcon />}
          badge={isInbox ? 0 : pendingCount}
        />

        {/* Help link pinned to bottom */}
        <div className="mt-auto">
          <Tooltip content="Docs coming soon" side="right" delayDuration={400}>
            <a
              href="#"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Documentation and help"
              className="flex h-9 w-9 items-center justify-center rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              style={{ color: 'oklch(40% 0 0)' }}
              onClick={(e: MouseEvent<HTMLAnchorElement>) => e.preventDefault()}
            >
              <HelpIcon />
            </a>
          </Tooltip>
        </div>
      </nav>

      {/* Content area */}
      <main className="flex flex-1 flex-col overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
