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
}

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<{ user: AuthUser; token: string }> => {
    // FastAPI OAuth2PasswordRequestForm expects application/x-www-form-urlencoded format
    const urlParams = new URLSearchParams();
    urlParams.append('username', credentials.email);
    urlParams.append('password', credentials.password);
    
    const response = await api.post<LoginResponse>('/auth/login', urlParams, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    const token = response.data.access_token;
    
    // Get user info from token or make a separate request
    // For now, we'll decode the token to get user info
    const payload = JSON.parse(atob(token.split('.')[1]));
    const user: AuthUser = {
      id: payload.sub,
      name: 'User', // This would come from a /me endpoint in real app
      email: credentials.email,
      role: payload.role,
    };
    
    return { user, token };
  },
  
  logout: async (): Promise<void> => {
    // In real app, this would call /auth/logout to invalidate tokens
    return Promise.resolve();
  },
  
  refreshToken: async (refreshToken: string): Promise<LoginResponse> => {
    const response = await api.post<LoginResponse>('/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  }
};

export default authApi;