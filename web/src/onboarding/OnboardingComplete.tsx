/**
 * OnboardingComplete — success screen shown after briefing approval.
 *
 * Shows transformation thesis copy, then auto-redirects to /galaxy after 3s.
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function OnboardingComplete() {
  const navigate = useNavigate();
  const [countdown, setCountdown] = useState(3);

  useEffect(() => {
    const interval = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          void navigate('/galaxy', { replace: true });
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [navigate]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-neutral-50 px-4 text-center">
      {/* Checkmark */}
      <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-green-100">
        <svg
          viewBox="0 0 48 48"
          className="h-10 w-10 text-green-600"
          fill="currentColor"
          aria-hidden="true"
        >
          <path d="M40.97 7.97a1.5 1.5 0 0 0-2.121 0L18 28.818l-8.849-8.849a1.5 1.5 0 0 0-2.121 2.12l10 10a1.5 1.5 0 0 0 2.121 0l22-22a1.5 1.5 0 0 0 0-2.12z" />
        </svg>
      </div>

      {/* Headline */}
      <h1 className="mb-3 text-3xl font-bold tracking-tight text-neutral-900">
        You just did in 5 minutes
        <br />
        what used to take 60
      </h1>
      <p className="mb-8 max-w-sm text-base text-neutral-500">
        Your workspace is live. Context OS will keep your briefings fresh from now on.
      </p>

      {/* Countdown */}
      <div className="flex items-center gap-2 rounded-full bg-white border border-neutral-200 px-5 py-2.5 text-sm text-neutral-600 shadow-sm">
        <span
          className="h-4 w-4 animate-spin rounded-full border-2 border-neutral-200 border-t-blue-600"
          aria-hidden="true"
        />
        Entering your workspace in {countdown}s…
      </div>

      {/* Manual link */}
      <a
        href="/galaxy"
        className="mt-4 text-sm text-blue-600 underline-offset-2 hover:underline"
      >
        Go now
      </a>
    </div>
  );
}
