import * as RadixTooltip from '@radix-ui/react-tooltip';
import { type ReactNode } from 'react';

interface NodeTooltipProps {
  children: ReactNode;
  title: string;
  body: ReactNode;
  side?: 'top' | 'right' | 'bottom' | 'left';
}

export function NodeTooltip({ children, title, body, side = 'right' }: NodeTooltipProps) {
  return (
    <RadixTooltip.Root delayDuration={500}>
      <RadixTooltip.Trigger asChild>{children}</RadixTooltip.Trigger>
      <RadixTooltip.Portal>
        <RadixTooltip.Content
          side={side}
          sideOffset={8}
          className={[
            'z-50 w-[300px] max-w-[300px] rounded-lg p-3',
            'bg-white border border-black/10 shadow-[var(--shadow-panel)]',
            'pointer-events-none',
            'data-[state=delayed-open]:animate-in data-[state=closed]:animate-out',
            'data-[state=delayed-open]:fade-in-0 data-[state=closed]:fade-out-0',
          ].join(' ')}
        >
          <p className="text-sm font-semibold text-[oklch(20%_0_0)] mb-1.5">{title}</p>
          <div className="text-xs text-[oklch(45%_0_0)] leading-relaxed">{body}</div>
          <RadixTooltip.Arrow className="fill-white stroke-black/10" />
        </RadixTooltip.Content>
      </RadixTooltip.Portal>
    </RadixTooltip.Root>
  );
}
