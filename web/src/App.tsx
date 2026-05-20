import { useAuth } from '@clerk/react';
import { type ReactNode } from 'react';
import * as RadixTooltip from '@radix-ui/react-tooltip';

function ProtectedRoute({ children }: { children: ReactNode }) {
  // Dev-only bypass: VITE_DEV_BYPASS_AUTH=true skips Clerk for local visual testing
  if (import.meta.env['VITE_DEV_BYPASS_AUTH'] === 'true') {
    return <>{children}</>;
  }

  const { isSignedIn, isLoaded } = useAuth();

  if (!isLoaded) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  if (!isSignedIn) {
    window.location.href = '/sign-in';
    return null;
  }

  return <>{children}</>;
}

export { ProtectedRoute };

export default function App({ children }: { children?: ReactNode }) {
  return (
    <RadixTooltip.Provider delayDuration={500}>
      <ProtectedRoute>{children}</ProtectedRoute>
    </RadixTooltip.Provider>
  );
}
