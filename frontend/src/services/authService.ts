import api, { AppAxiosRequestConfig } from './api';
import { AuthCapabilities, User } from '../store/slices/authSlice';
import { AppRole } from '../utils/roles';

interface LoginCredentials {
  email: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  refresh_token: string;
}

interface AuthUser extends User {
  role: AppRole;
  avatar?: string;
}

interface FeishuLoginResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

interface AuthCapabilitiesResponse {
  role: AppRole;
  capabilities: AuthCapabilities;
}

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<{ user: AuthUser; token: string }> => {
    const urlParams = new URLSearchParams();
    urlParams.append('username', credentials.email);
    urlParams.append('password', credentials.password);

    const requestConfig: AppAxiosRequestConfig = {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      skipAuthRedirect: true,
    };

    const response = await api.post<LoginResponse>('/auth/login', urlParams, requestConfig);
    const token = response.data.access_token;
    
    const payload = JSON.parse(atob(token.split('.')[1]));
    const user: AuthUser = {
      id: Number(payload.sub),
      name: 'User',
      email: credentials.email,
      role: payload.role,
    };
    
    return { user, token };
  },
  
  feishuLogin: async (code: string, state: string): Promise<{ user: AuthUser; token: string }> => {
    const requestConfig: AppAxiosRequestConfig = {
      skipAuthRedirect: true,
    };
    const response = await api.post<FeishuLoginResponse>(
      '/auth/feishu/login',
      { code, state },
      requestConfig
    );
    return {
      user: response.data.user,
      token: response.data.access_token,
    };
  },
  
  getFeishuOAuthUrl: async (): Promise<string> => {
    const response = await api.get<{ url: string }>('/auth/feishu/url');
    return response.data.url;
  },

  getCapabilities: async (): Promise<AuthCapabilitiesResponse> => {
    const response = await api.get<AuthCapabilitiesResponse>('/auth/me/capabilities');
    return response.data;
  },
  
  logout: async (): Promise<void> => {
    return Promise.resolve();
  },
  
  refreshToken: async (refreshToken: string): Promise<LoginResponse> => {
    const response = await api.post<LoginResponse>('/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  }
};

export default authApi;
