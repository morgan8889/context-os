import { lazy, Suspense, type ReactNode } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './App';

const GalaxyView = lazy(() => import('./views/galaxy/GalaxyView'));
const TopologyView = lazy(() => import('./views/topology/TopologyView'));
const DecisionView = lazy(() => import('./views/decisions/DecisionView'));
const InboxView = lazy(() => import('./inbox/InboxView'));

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
  {
    path: '/galaxy',
    element: (
      <Protected>
        <GalaxyView />
      </Protected>
    ),
  },
  {
    path: '/topology',
    element: (
      <Protected>
        <TopologyView />
      </Protected>
    ),
  },
  {
    path: '/decisions',
    element: (
      <Protected>
        <DecisionView />
      </Protected>
    ),
  },
  {
    path: '/inbox',
    element: (
      <Protected>
        <InboxView />
      </Protected>
    ),
  },
]);
