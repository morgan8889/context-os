import * as RadixTooltip from '@radix-ui/react-tooltip';
import { type ReactNode } from 'react';

interface TooltipProps {
  children: ReactNode;
  content: ReactNode;
  side?: 'top' | 'right' | 'bottom' | 'left';
  delayDuration?: number;
}

export function Tooltip({ children, content, side = 'top', delayDuration = 500 }: TooltipProps) {
  return (
    <RadixTooltip.Root delayDuration={delayDuration}>
      <RadixTooltip.Trigger asChild>{children}</RadixTooltip.Trigger>
      <RadixTooltip.Portal>
        <RadixTooltip.Content
          side={side}
          sideOffset={6}
          className={[
            'z-50 max-w-xs rounded-md px-3 py-2 text-sm shadow-[var(--shadow-panel)]',
            'bg-white border border-black/10 text-[oklch(20%_0_0)]',
            'pointer-events-none select-none',
            'data-[state=delayed-open]:animate-in data-[state=closed]:animate-out',
            'data-[state=delayed-open]:fade-in-0 data-[state=closed]:fade-out-0',
            'data-[state=delayed-open]:zoom-in-95 data-[state=closed]:zoom-out-95',
          ].join(' ')}
        >
          {content}
          <RadixTooltip.Arrow className="fill-white" />
        </RadixTooltip.Content>
      </RadixTooltip.Portal>
    </RadixTooltip.Root>
  );
}

export { RadixTooltip as TooltipProvider };
