import { Navigate, Outlet } from 'react-router-dom';

import { useAuth } from '../../hooks/useAuth';

export function PublicOnlyRoute() {
  const { status } = useAuth();

  if (status === 'authenticated') {
    return <Navigate to="/app" replace />;
  }

  return <Outlet />;
}
