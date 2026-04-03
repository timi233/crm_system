import api from './api';
import { User } from '../store/slices/authSlice';

interface LoginCredentials {
  email: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  refresh_token: string;
}

interface AuthUser extends User {
  role: 'admin' | 'sales' | 'business' | 'finance';
  avatar?: string;
}

interface FeishuLoginResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<{ user: AuthUser; token: string }> => {
    const urlParams = new URLSearchParams();
    urlParams.append('username', credentials.email);
    urlParams.append('password', credentials.password);
    
    const response = await api.post<LoginResponse>('/auth/login', urlParams, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    const token = response.data.access_token;
    
    const payload = JSON.parse(atob(token.split('.')[1]));
    const user: AuthUser = {
      id: payload.sub,
      name: 'User',
      email: credentials.email,
      role: payload.role,
    };
    
    return { user, token };
  },
  
  feishuLogin: async (code: string): Promise<{ user: AuthUser; token: string }> => {
    const response = await api.post<FeishuLoginResponse>('/auth/feishu/login', { code });
    return {
      user: response.data.user,
      token: response.data.access_token,
    };
  },
  
  getFeishuOAuthUrl: async (): Promise<string> => {
    const response = await api.get<{ url: string }>('/auth/feishu/url');
    return response.data.url;
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