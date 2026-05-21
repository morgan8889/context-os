/**
 * OnboardingShell — top-level wrapper that drives the 5-step onboarding wizard.
 *
 * Responsibilities:
 * - Fetch onboarding session on mount
 * - Render progress indicator (5 steps, current highlighted)
 * - Route to correct step component based on session.current_step
 * - Show loading skeleton during initial fetch
 * - Redirect to /galaxy when current_step === 'activated'
 */
import { lazy, Suspense } from 'react';
import { Navigate } from 'react-router-dom';
import { useOnboardingSession } from '@/lib/hooks/useOnboardingSession';

const SurveyStep = lazy(() => import('./steps/SurveyStep'));
const ConnectStep = lazy(() => import('./steps/ConnectStep'));
const ScopeStep = lazy(() => import('./steps/ScopeStep'));
const IngestStep = lazy(() => import('./steps/IngestStep'));
const BriefingStep = lazy(() => import('./steps/BriefingStep'));

// ── Step Config ────────────────────────────────────────────────────────────────

const STEPS = [
  { key: 'survey', label: 'About you' },
  { key: 'connect', label: 'Connect tools' },
  { key: 'scope', label: 'Select scope' },
  { key: 'ingest', label: 'Syncing data' },
  { key: 'briefing', label: 'First briefing' },
] as const;

type StepKey = (typeof STEPS)[number]['key'];

function stepIndex(step: string): number {
  return STEPS.findIndex((s) => s.key === step);
}

// ── Progress Indicator ─────────────────────────────────────────────────────────

interface ProgressBarProps {
  currentStep: string;
}

function ProgressBar({ currentStep }: ProgressBarProps) {
  const currentIdx = stepIndex(currentStep);

  return (
    <nav aria-label="Onboarding progress" className="flex items-center gap-0">
      {STEPS.map((step, idx) => {
        const isComplete = idx < currentIdx;
        const isCurrent = idx === currentIdx;

        return (
          <div key={step.key} className="flex items-center">
            {/* Connector line */}
            {idx > 0 && (
              <div
                className={[
                  'h-0.5 w-8 transition-colors duration-300',
                  isComplete ? 'bg-blue-600' : 'bg-neutral-200',
                ].join(' ')}
                aria-hidden="true"
              />
            )}

            {/* Step circle */}
            <div className="flex flex-col items-center gap-1.5">
              <div
                className={[
                  'flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold',
                  'transition-all duration-300',
                  isComplete
                    ? 'bg-blue-600 text-white'
                    : isCurrent
                      ? 'bg-blue-600 text-white ring-4 ring-blue-100'
                      : 'bg-neutral-100 text-neutral-400',
                ].join(' ')}
                aria-current={isCurrent ? 'step' : undefined}
              >
                {isComplete ? (
                  <svg viewBox="0 0 16 16" className="h-4 w-4" fill="currentColor" aria-hidden="true">
                    <path d="M13.485 1.431a1.473 1.473 0 0 0-2.084 0l-6.25 6.25-.952-.952a1.473 1.473 0 1 0-2.083 2.083l2 2a1.473 1.473 0 0 0 2.083 0l7.292-7.292a1.473 1.473 0 0 0 0-2.083z" />
                  </svg>
                ) : (
                  idx + 1
                )}
              </div>
              <span
                className={[
                  'text-xs font-medium whitespace-nowrap',
                  isCurrent ? 'text-blue-600' : isComplete ? 'text-neutral-600' : 'text-neutral-400',
                ].join(' ')}
              >
                {step.label}
              </span>
            </div>
          </div>
        );
      })}
    </nav>
  );
}

// ── Skeleton ───────────────────────────────────────────────────────────────────

function OnboardingSkeleton() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-neutral-50 px-4">
      <div className="w-full max-w-lg space-y-8">
        {/* Progress bar skeleton */}
        <div className="flex items-center justify-center gap-4">
          {[0, 1, 2, 3, 4].map((i) => (
            <div key={i} className="flex items-center gap-2">
              {i > 0 && <div className="h-0.5 w-8 animate-pulse rounded bg-neutral-200" />}
              <div className="h-8 w-8 animate-pulse rounded-full bg-neutral-200" />
            </div>
          ))}
        </div>
        {/* Card skeleton */}
        <div className="rounded-2xl border border-neutral-200 bg-white p-8 shadow-sm">
          <div className="space-y-4">
            <div className="h-6 w-2/3 animate-pulse rounded bg-neutral-200" />
            <div className="h-4 w-full animate-pulse rounded bg-neutral-100" />
            <div className="h-4 w-4/5 animate-pulse rounded bg-neutral-100" />
            <div className="mt-8 space-y-3">
              {[0, 1, 2, 3, 4].map((i) => (
                <div key={i} className="h-12 w-full animate-pulse rounded-lg bg-neutral-100" />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Step Loader ────────────────────────────────────────────────────────────────

function StepLoader() {
  return (
    <div className="flex h-40 items-center justify-center">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
    </div>
  );
}

// ── Step Router ────────────────────────────────────────────────────────────────

function renderStep(step: StepKey | 'activated') {
  switch (step) {
    case 'survey':
      return <SurveyStep />;
    case 'connect':
      return <ConnectStep />;
    case 'scope':
      return <ScopeStep />;
    case 'ingest':
      return <IngestStep />;
    case 'briefing':
      return <BriefingStep />;
    case 'activated':
      return <Navigate to="/galaxy" replace />;
  }
}

// ── Shell ──────────────────────────────────────────────────────────────────────

export default function OnboardingShell() {
  const { session, isLoading } = useOnboardingSession();

  if (isLoading) {
    return <OnboardingSkeleton />;
  }

  if (!session) {
    return <OnboardingSkeleton />;
  }

  const { current_step } = session;

  if (current_step === 'activated') {
    return <Navigate to="/galaxy" replace />;
  }

  return (
    <div className="flex min-h-screen flex-col items-center bg-neutral-50 px-4 py-12">
      {/* Header */}
      <div className="mb-10 flex flex-col items-center gap-2 text-center">
        <div className="mb-2 flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-blue-600" aria-hidden="true" />
          <span className="text-lg font-semibold tracking-tight text-neutral-900">Context OS</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-neutral-900">
          Set up your workspace
        </h1>
        <p className="text-sm text-neutral-500">
          Takes about 5 minutes. Your first briefing will be ready after setup.
        </p>
      </div>

      {/* Progress */}
      <div className="mb-10">
        <ProgressBar currentStep={current_step} />
      </div>

      {/* Step content */}
      <div className="w-full max-w-lg">
        <Suspense fallback={<StepLoader />}>
          {renderStep(current_step)}
        </Suspense>
      </div>
    </div>
  );
}
