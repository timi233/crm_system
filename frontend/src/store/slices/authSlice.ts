import { createSlice, PayloadAction } from '@reduxjs/toolkit';

import { AppRole } from '../../utils/roles';

export interface User {
  id: number;
  name: string;
  email: string;
  role: AppRole;
}

export type AuthCapabilities = Record<string, boolean>;

interface AuthState {
  user: User | null;
  token: string | null;
  capabilities: AuthCapabilities;
  capabilitiesLoaded: boolean;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

const getInitialState = (): AuthState => {
  const storedToken = localStorage.getItem('token');
  const storedUser = localStorage.getItem('user');
  const storedCapabilities = localStorage.getItem('capabilities');
  return {
    user: storedUser ? JSON.parse(storedUser) : null,
    token: storedToken,
    capabilities: storedCapabilities ? JSON.parse(storedCapabilities) : {},
    capabilitiesLoaded: !!storedCapabilities,
    isAuthenticated: !!storedToken,
    loading: false,
    error: null,
  };
};

const initialState = getInitialState();

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    loginStart: (state) => {
      state.loading = true;
      state.error = null;
    },
    loginSuccess: (state, action: PayloadAction<{ user: User; token: string }>) => {
      state.user = action.payload.user;
      state.token = action.payload.token;
      state.capabilities = {};
      state.capabilitiesLoaded = false;
      state.isAuthenticated = true;
      state.loading = false;
      state.error = null;
      localStorage.setItem('token', action.payload.token);
      localStorage.setItem('user', JSON.stringify(action.payload.user));
      localStorage.removeItem('capabilities');
    },
    loginFailure: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.error = action.payload;
    },
    logout: (state) => {
      state.user = null;
      state.token = null;
      state.capabilities = {};
      state.capabilitiesLoaded = false;
      state.isAuthenticated = false;
      state.loading = false;
      state.error = null;
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      localStorage.removeItem('capabilities');
    },
    setUser: (state, action: PayloadAction<User>) => {
      state.user = action.payload;
      localStorage.setItem('user', JSON.stringify(action.payload));
    },
    setCapabilities: (state, action: PayloadAction<AuthCapabilities>) => {
      state.capabilities = action.payload;
      state.capabilitiesLoaded = true;
      localStorage.setItem('capabilities', JSON.stringify(action.payload));
    },
    clearCapabilities: (state) => {
      state.capabilities = {};
      state.capabilitiesLoaded = false;
      localStorage.removeItem('capabilities');
    },
  },
});

export const {
  loginStart,
  loginSuccess,
  loginFailure,
  logout,
  setUser,
  setCapabilities,
  clearCapabilities,
} = authSlice.actions;
export default authSlice.reducer;
