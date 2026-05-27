import { type ReactNode } from 'react';
import { Outlet, NavLink, useMatch } from 'react-router-dom';
import * as RadixTooltip from '@radix-ui/react-tooltip';

interface NavItem {
  to: string;
  label: string;
  description: string;
  icon: ReactNode;
}

function GalaxyIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <circle cx="12" cy="12" r="8" strokeDasharray="2 3" />
      <line x1="12" y1="4" x2="12" y2="9" />
      <line x1="12" y1="15" x2="12" y2="20" />
      <line x1="4" y1="12" x2="9" y2="12" />
      <line x1="15" y1="12" x2="20" y2="12" />
    </svg>
  );
}

function TopologyIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="9" width="6" height="6" rx="1" />
      <rect x="16" y="4" width="6" height="6" rx="1" />
      <rect x="16" y="14" width="6" height="6" rx="1" />
      <line x1="8" y1="12" x2="16" y2="7" />
      <line x1="8" y1="12" x2="16" y2="17" />
    </svg>
  );
}

function DecisionsIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <rect x="9" y="2" width="6" height="5" rx="1" />
      <rect x="2" y="17" width="6" height="5" rx="1" />
      <rect x="16" y="17" width="6" height="5" rx="1" />
      <line x1="12" y1="7" x2="12" y2="13" />
      <line x1="12" y1="13" x2="5" y2="17" />
      <line x1="12" y1="13" x2="19" y2="17" />
    </svg>
  );
}

function InboxIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="22 13 16 13 14 16 10 16 8 13 2 13" />
      <path d="M5.5 5.1L2 13v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.5-7.9A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.74 1.1z" />
    </svg>
  );
}

const NAV_ITEMS: NavItem[] = [
  {
    to: '/galaxy',
    label: 'Galaxy',
    description: 'Initiatives & signals',
    icon: <GalaxyIcon />,
  },
  {
    to: '/topology',
    label: 'Topology',
    description: 'Team workflows',
    icon: <TopologyIcon />,
  },
  {
    to: '/decisions',
    label: 'Decisions',
    description: 'Architectural decisions',
    icon: <DecisionsIcon />,
  },
  {
    to: '/inbox',
    label: 'Inbox',
    description: 'Pending approvals',
    icon: <InboxIcon />,
  },
];

function NavItemButton({ item }: { item: NavItem }) {
  const isActive = Boolean(useMatch(item.to));
  const base = 'flex h-11 w-11 items-center justify-center rounded-lg transition-colors duration-[150ms] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[oklch(65%_0.25_250)]';
  const activeClass = 'bg-[oklch(65%_0.25_250/0.15)] text-[oklch(75%_0.2_250)]';
  const inactiveClass = 'text-[oklch(55%_0_0)] hover:bg-white/5 hover:text-[oklch(75%_0_0)]';

  return (
    <RadixTooltip.Root>
      <RadixTooltip.Trigger asChild>
        <NavLink
          to={item.to}
          aria-label={item.label}
          aria-current={isActive ? 'page' : undefined}
          className={`${base} ${isActive ? activeClass : inactiveClass}`}
        >
          {item.icon}
        </NavLink>
      </RadixTooltip.Trigger>
      <RadixTooltip.Portal>
        <RadixTooltip.Content
          side="right"
          sideOffset={12}
          className={[
            'z-50 select-none rounded-md px-3 py-2',
            'bg-[oklch(20%_0_0)] shadow-lg',
            'data-[state=delayed-open]:animate-in data-[state=delayed-open]:fade-in-0',
            'data-[state=closed]:animate-out data-[state=closed]:fade-out-0',
          ].join(' ')}
        >
          <p className="text-xs font-semibold text-[oklch(90%_0_0)]">{item.label}</p>
          <p className="text-xs text-[oklch(60%_0_0)]">{item.description}</p>
          <RadixTooltip.Arrow className="fill-[oklch(20%_0_0)]" />
        </RadixTooltip.Content>
      </RadixTooltip.Portal>
    </RadixTooltip.Root>
  );
}

export default function AppShell() {
  return (
    <div className="flex h-screen">
      {/* Fixed left sidebar */}
      <nav
        className="fixed left-0 top-0 z-40 flex h-full w-14 flex-col items-center border-r border-white/[0.06] bg-[oklch(11%_0_0)] py-3"
        aria-label="Main navigation"
      >
        {/* Logo mark */}
        <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-lg bg-[oklch(65%_0.25_250/0.15)]">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="oklch(75% 0.2 250)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        </div>

        {/* Nav items */}
        <div className="flex flex-1 flex-col items-center gap-1">
          {NAV_ITEMS.map((item) => (
            <NavItemButton key={item.to} item={item} />
          ))}
        </div>
      </nav>

      {/* Content area — offset by sidebar width */}
      <main className="ml-14 flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
