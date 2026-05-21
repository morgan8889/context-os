/**
 * SurveyStep — "Which part of your week would you most want to change?"
 *
 * 5 option buttons. "Something else" reveals a textarea.
 * On submit: calls useSurveyMutation; shows spinner while mutating.
 */
import { useState } from 'react';
import { useSurveyMutation } from '@/lib/hooks/useOnboardingSession';

// ── Option Config ──────────────────────────────────────────────────────────────

const OPTIONS = [
  { value: 'briefings', label: 'Writing my weekly briefing' },
  { value: 'dependencies', label: 'Tracking cross-team dependencies' },
  { value: 'decision_retrieval', label: 'Finding past decisions' },
  { value: 'architecture_review_cycle_time', label: 'Architecture review cycle time' },
  { value: 'something_else', label: 'Something else' },
] as const;

type OptionValue = (typeof OPTIONS)[number]['value'];

// ── Component ──────────────────────────────────────────────────────────────────

export default function SurveyStep() {
  const [selected, setSelected] = useState<OptionValue | null>(null);
  const [freeText, setFreeText] = useState('');

  const { mutate, isPending } = useSurveyMutation();

  function handleSubmit() {
    if (!selected) return;
    mutate({
      option: selected,
      free_text: selected === 'something_else' && freeText.trim() ? freeText.trim() : undefined,
    });
  }

  const canSubmit =
    selected !== null &&
    (selected !== 'something_else' || freeText.trim().length > 0) &&
    !isPending;

  return (
    <div className="rounded-2xl border border-neutral-200 bg-white p-8 shadow-sm">
      <h2 className="mb-1 text-xl font-bold text-neutral-900">
        Which part of your week would you most want to change?
      </h2>
      <p className="mb-6 text-sm text-neutral-500">
        We'll tailor the experience to what matters most to you.
      </p>

      <fieldset className="space-y-3">
        <legend className="sr-only">Choose the area you want to improve most</legend>

        {OPTIONS.map((opt) => {
          const isSelected = selected === opt.value;
          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => setSelected(opt.value)}
              aria-pressed={isSelected}
              className={[
                'w-full rounded-xl border px-5 py-4 text-left text-sm font-medium',
                'transition-all duration-150 focus-visible:outline-none',
                'focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1',
                isSelected
                  ? 'border-blue-600 bg-blue-50 text-blue-700 ring-1 ring-blue-600'
                  : 'border-neutral-200 bg-white text-neutral-700 hover:border-neutral-300 hover:bg-neutral-50',
              ].join(' ')}
            >
              <span className="flex items-center gap-3">
                {/* Selection indicator */}
                <span
                  className={[
                    'flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2',
                    'transition-colors duration-150',
                    isSelected ? 'border-blue-600 bg-blue-600' : 'border-neutral-300 bg-white',
                  ].join(' ')}
                  aria-hidden="true"
                >
                  {isSelected && (
                    <span className="h-2 w-2 rounded-full bg-white" />
                  )}
                </span>
                {opt.label}
              </span>
            </button>
          );
        })}
      </fieldset>

      {/* Free-text textarea for "Something else" */}
      {selected === 'something_else' && (
        <div className="mt-4">
          <label htmlFor="survey-free-text" className="mb-1.5 block text-sm font-medium text-neutral-700">
            Tell us more
          </label>
          <textarea
            id="survey-free-text"
            value={freeText}
            onChange={(e) => setFreeText(e.target.value)}
            rows={3}
            placeholder="Describe the biggest friction in your workflow…"
            className={[
              'w-full resize-none rounded-lg border border-neutral-200 px-3 py-2.5',
              'text-sm text-neutral-900 placeholder:text-neutral-400',
              'focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20',
            ].join(' ')}
          />
        </div>
      )}

      <div className="mt-8">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!canSubmit}
          className={[
            'flex w-full items-center justify-center gap-2 rounded-xl py-3 text-sm font-semibold',
            'transition-all duration-150 focus-visible:outline-none',
            'focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1',
            canSubmit
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'cursor-not-allowed bg-neutral-100 text-neutral-400',
          ].join(' ')}
        >
          {isPending ? (
            <>
              <span
                className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"
                aria-hidden="true"
              />
              Saving…
            </>
          ) : (
            'Continue'
          )}
        </button>
      </div>
    </div>
  );
}
