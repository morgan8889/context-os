import { lazy, Suspense, type ReactNode } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { SignIn as ClerkSignIn } from '@clerk/react';
import { ProtectedRoute } from './App';

function SignInPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-50 px-4">
      <ClerkSignIn signUpUrl="/sign-up" fallbackRedirectUrl="/galaxy" />
    </div>
  );
}

const AppShell = lazy(() => import('./components/AppShell'));
const GalaxyView = lazy(() => import('./views/galaxy/GalaxyView'));
const TopologyView = lazy(() => import('./views/topology/TopologyView'));
const DecisionView = lazy(() => import('./views/decisions/DecisionView'));
const InboxView = lazy(() => import('./inbox/InboxView'));
const OnboardingView = lazy(() => import('./views/onboarding/OnboardingView'));
const OnboardingShell = lazy(() => import('./onboarding/OnboardingShell'));
const SignUp = lazy(() => import('./pages/SignUp'));
const AdminShell = lazy(() => import('./admin/AdminShell'));

function PageLoader() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
    </div>
  );
}

function Protected({ children }: { children: ReactNode }) {
  return (
    <ProtectedRoute>
      <Suspense fallback={<PageLoader />}>{children}</Suspense>
    </ProtectedRoute>
  );
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/galaxy" replace />,
  },
  // Main app shell — wraps all primary views with persistent sidebar nav
  {
    element: (
      <Protected>
        <AppShell />
      </Protected>
    ),
    children: [
      {
        path: '/galaxy',
        element: <GalaxyView />,
      },
      {
        path: '/topology',
        element: <TopologyView />,
      },
      {
        path: '/decisions',
        element: <DecisionView />,
      },
      {
        path: '/inbox',
        element: <InboxView />,
      },
    ],
  },
  {
    path: '/onboarding',
    element: (
      <Protected>
        <Suspense fallback={<PageLoader />}>
          <OnboardingShell />
        </Suspense>
      </Protected>
    ),
  },
  {
    path: '/connect-github',
    element: (
      <Protected>
        <Suspense fallback={<PageLoader />}>
          <OnboardingView />
        </Suspense>
      </Protected>
    ),
  },
  {
    path: '/sign-up',
    element: (
      <Suspense fallback={<PageLoader />}>
        <SignUp />
      </Suspense>
    ),
  },
  {
    path: '/sign-in',
    element: (
      <Suspense fallback={<PageLoader />}>
        <SignInPage />
      </Suspense>
    ),
  },
  {
    path: '/admin',
    element: (
      <Protected>
        <Suspense fallback={<PageLoader />}>
          <AdminShell />
        </Suspense>
      </Protected>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/admin/funnel" replace />,
      },
      {
        path: 'funnel',
        lazy: async () => {
          const { default: FunnelView } = await import('./admin/FunnelView');
          return { element: <FunnelView /> };
        },
      },
      {
        path: 'survey-responses',
        lazy: async () => {
          const { default: SurveyResponsesTable } = await import('./admin/SurveyResponsesTable');
          return { element: <SurveyResponsesTable /> };
        },
      },
      {
        path: 'orgs/:tenantId',
        lazy: async () => {
          const { default: OrgDetail } = await import('./admin/OrgDetail');
          return { element: <OrgDetail /> };
        },
      },
    ],
  },
]);
