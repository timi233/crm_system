import { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import authApi from '../../services/authService';
import { clearCapabilities, logout, setCapabilities, setUser } from '../../store/slices/authSlice';
import { RootState } from '../../store/store';

const AuthBootstrap = () => {
  const dispatch = useDispatch();
  const { isAuthenticated, token, user, capabilitiesLoaded } = useSelector(
    (state: RootState) => state.auth
  );
  const [retryTick, setRetryTick] = useState(0);
  const retryTimerRef = useRef<number | null>(null);

  useEffect(() => {
    if (!isAuthenticated || !token) {
      if (retryTimerRef.current) {
        window.clearTimeout(retryTimerRef.current);
        retryTimerRef.current = null;
      }
      dispatch(clearCapabilities());
      return;
    }

    if (capabilitiesLoaded) {
      return;
    }

    let cancelled = false;

    const loadCapabilities = async () => {
      try {
        const response = await authApi.getCapabilities();
        if (cancelled) {
          return;
        }
        if (user && user.role !== response.role) {
          dispatch(setUser({ ...user, role: response.role }));
        }
        dispatch(setCapabilities(response.capabilities));
      } catch (error: any) {
        if (cancelled) {
          return;
        }
        if (error?.response?.status === 401) {
          dispatch(logout());
        } else {
          dispatch(clearCapabilities());
          retryTimerRef.current = window.setTimeout(() => {
            setRetryTick((value) => value + 1);
          }, 3000);
        }
      }
    };

    void loadCapabilities();

    return () => {
      cancelled = true;
      if (retryTimerRef.current) {
        window.clearTimeout(retryTimerRef.current);
        retryTimerRef.current = null;
      }
    };
  }, [capabilitiesLoaded, dispatch, isAuthenticated, retryTick, token, user]);

  return null;
};

export default AuthBootstrap;
