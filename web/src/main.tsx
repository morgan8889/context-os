import { StrictMode, useEffect, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import { ClerkProvider, useAuth, useUser } from '@clerk/react';
import { QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from 'react-router-dom';
import * as RadixTooltip from '@radix-ui/react-tooltip';
import { queryClient } from './lib/api/queryClient';
import { setTokenProvider, setImpersonationTokenProvider } from './lib/api/client';
import { router } from './router';
import { initOtel, initOtelWithTenantId, instrumentQueryClient } from './lib/telemetry/otel';
import { ImpersonationProvider, useImpersonation } from './lib/hooks/useImpersonation';
import './design-system/globals.css';

const PUBLISHABLE_KEY = import.meta.env['VITE_CLERK_PUBLISHABLE_KEY'] as string;

// Initialise telemetry early — no-op if the env var is unset
initOtel({
  endpoint: import.meta.env['VITE_OTEL_EXPORTER_OTLP_ENDPOINT'] as string | undefined,
  tenantId: null,
});
// Instrument QueryClient once
instrumentQueryClient(queryClient);

function ImpersonationTokenWirer() {
  const { impersonationToken } = useImpersonation();
  const tokenRef = useRef(impersonationToken);

  useEffect(() => {
    tokenRef.current = impersonationToken;
  }, [impersonationToken]);

  useEffect(() => {
    setImpersonationTokenProvider(() => tokenRef.current);
  }, []);

  return null;
}

function ClerkTokenWirer() {
  const { getToken } = useAuth();
  const { user } = useUser();

  useEffect(() => {
    setTokenProvider(() => getToken());
  }, [getToken]);

  // Once we have a Clerk user, extract the org/tenant ID and wire into OTEL
  useEffect(() => {
    if (!user) return;
    // Clerk v5: org membership available via user.organizationMemberships
    const orgId =
      (user as { primaryOrganizationId?: string }).primaryOrganizationId ??
      null;
    if (orgId) {
      initOtelWithTenantId(orgId);
    }
  }, [user]);

  return null;
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ClerkProvider publishableKey={PUBLISHABLE_KEY}>
      <QueryClientProvider client={queryClient}>
        <ImpersonationProvider>
          <RadixTooltip.Provider delayDuration={500}>
            <ClerkTokenWirer />
            <ImpersonationTokenWirer />
            <RouterProvider router={router} />
          </RadixTooltip.Provider>
        </ImpersonationProvider>
      </QueryClientProvider>
    </ClerkProvider>
  </StrictMode>
);
