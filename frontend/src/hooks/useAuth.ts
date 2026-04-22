import { useSelector } from 'react-redux';
import { RootState } from '../store/store';

export const useAuth = () => {
  const { user, token, isAuthenticated, capabilities, capabilitiesLoaded } = useSelector(
    (state: RootState) => state.auth
  );

  const hasCapability = (key: string) => Boolean(capabilities[key]);

  return {
    user,
    token,
    isAuthenticated,
    capabilities,
    capabilitiesLoaded,
    hasCapability,
  };
};
