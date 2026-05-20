interface BadgeProps {
  label: string;
  status: 'active' | 'paused' | 'complete' | 'at_risk' | 'blocked' | 'pending' | 'healthy' | 'degraded';
  className?: string;
}

const statusClasses: Record<BadgeProps['status'], string> = {
  active:   'bg-[var(--color-status-active)] text-white',
  healthy:  'bg-[var(--color-status-healthy)] text-white',
  paused:   'bg-[var(--color-status-paused)] text-white',
  pending:  'bg-[var(--color-status-pending)] text-white',
  complete: 'bg-[var(--color-status-complete)] text-white',
  at_risk:  'bg-[var(--color-status-at-risk)] text-white',
  blocked:  'bg-[var(--color-status-blocked)] text-white',
  degraded: 'bg-[var(--color-status-degraded)] text-white',
};

export function Badge({ label, status, className = '' }: BadgeProps) {
  return (
    <span
      className={[
        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
        statusClasses[status],
        className,
      ].join(' ')}
    >
      {label}
    </span>
  );
}
