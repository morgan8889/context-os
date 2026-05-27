/**
 * SignUp — Clerk-powered sign-up page with transformation thesis context.
 */
import { SignUp as ClerkSignUp } from '@clerk/react';

export default function SignUp() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-neutral-50 px-4">
      {/* Value proposition */}
      <div className="mb-10 max-w-sm text-center">
        <div className="mb-4 flex items-center justify-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-blue-600" aria-hidden="true" />
          <span className="text-xl font-bold tracking-tight text-neutral-900">Context OS</span>
        </div>
        <p className="text-base leading-relaxed text-neutral-600">
          Right now your weekly briefing takes ~60 minutes to write.
          <br />
          <strong className="text-neutral-900">
            Context OS drafts it in 5 from your Jira / GitHub / Slack;
          </strong>{' '}
          you review and approve.
        </p>
      </div>

      {/* Clerk sign-up widget */}
      <ClerkSignUp
        signInUrl="/sign-in"
        fallbackRedirectUrl="/onboarding"
      />

      <p className="mt-6 text-xs text-neutral-400">
        Already have an account?{' '}
        <a href="/sign-in" className="text-blue-600 underline-offset-2 hover:underline">
          Sign in
        </a>
      </p>
    </div>
  );
}
