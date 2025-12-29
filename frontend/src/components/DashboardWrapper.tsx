/**
 * Wrapper component that extracts session ID from URL params and passes it to Dashboard.
 */

import { useParams, Navigate } from 'react-router-dom';
import { Dashboard } from './Dashboard';

export function DashboardWrapper() {
  const { sessionId } = useParams<{ sessionId: string }>();

  if (!sessionId) {
    return <Navigate to="/" replace />;
  }

  return <Dashboard sessionId={sessionId} />;
}
