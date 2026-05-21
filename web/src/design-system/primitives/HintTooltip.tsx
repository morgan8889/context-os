import { Tooltip } from '@/design-system/components/Tooltip';

interface HintTooltipProps {
  content: string | undefined;
  side?: 'top' | 'right' | 'bottom' | 'left';
}

export function HintTooltip({ content, side = 'top' }: HintTooltipProps) {
  if (!content) return null;

  return (
    <Tooltip content={content} side={side} delayDuration={300}>
      <button
        type="button"
        aria-label="More information"
        className="ml-1 inline-flex cursor-help items-center align-middle focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-500 rounded-full"
        style={{ verticalAlign: 'middle' }}
      >
        <svg
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
          aria-hidden="true"
        >
          <circle cx="6" cy="6" r="5.5" stroke="oklch(65% 0 0)" />
          <text
            x="6"
            y="9"
            textAnchor="middle"
            fontSize="7"
            fontWeight="600"
            fill="oklch(65% 0 0)"
            fontFamily="sans-serif"
          >
            ?
          </text>
        </svg>
      </button>
    </Tooltip>
  );
}
