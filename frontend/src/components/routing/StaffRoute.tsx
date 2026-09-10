import { Navigate, Outlet } from 'react-router-dom';

import { useAuth } from '../../hooks/useAuth';

export function StaffRoute() {
  const { user } = useAuth();
  if (!user?.is_staff) return <Navigate to="/app" replace />;
  return <Outlet />;
}
