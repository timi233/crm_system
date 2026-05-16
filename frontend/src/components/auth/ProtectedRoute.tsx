import React from 'react';
import { Navigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '../../store/store';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredCapability?: string | string[];
  requireAll?: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredCapability,
  requireAll = false,
}) => {
  const { isAuthenticated, capabilities, capabilitiesLoaded } = useSelector(
    (state: RootState) => state.auth
  );

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requiredCapability) {
    if (!capabilitiesLoaded) {
      return <div style={{ padding: 24 }}>加载权限...</div>;
    }

    const required = Array.isArray(requiredCapability)
      ? requiredCapability
      : [requiredCapability];
    const allowed = requireAll
      ? required.every((key) => Boolean(capabilities[key]))
      : required.some((key) => Boolean(capabilities[key]));

    if (!allowed) {
      return <div style={{ padding: 24 }}>403 无权限访问</div>;
    }
  }

  return <>{children}</>;
};

export default ProtectedRoute;
