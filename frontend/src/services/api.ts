import axios, { AxiosError, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios';
import { appMessage } from '../utils/appFeedback';

export const getApiBaseUrl = () => {
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }

  return '/api';
};

export const API_BASE_URL = getApiBaseUrl();

export const getApiUrl = (path: string) => `${API_BASE_URL}${path}`;

export const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export interface AppAxiosRequestConfig extends AxiosRequestConfig {
  skipAuthRedirect?: boolean;
  _retryWithAuth?: boolean;
}

const AUTH_STORAGE_KEYS = ['token', 'user', 'capabilities'];

const clearAuthState = () => {
  AUTH_STORAGE_KEYS.forEach((key) => localStorage.removeItem(key));
  window.dispatchEvent(new CustomEvent('auth:expired'));
};

const formatErrorDetail = (detail: unknown): string | undefined => {
  if (typeof detail === 'string') {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === 'string') {
          return item;
        }
        if (item && typeof item === 'object' && 'msg' in item) {
          const msg = (item as { msg?: unknown }).msg;
          return typeof msg === 'string' ? msg : undefined;
        }
        return undefined;
      })
      .filter((item): item is string => Boolean(item));

    return messages.length > 0 ? messages.join('; ') : undefined;
  }

  if (detail && typeof detail === 'object' && 'msg' in detail) {
    const msg = (detail as { msg?: unknown }).msg;
    return typeof msg === 'string' ? msg : undefined;
  }

  return undefined;
};

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const appConfig = config as InternalAxiosRequestConfig & { skipAuthRedirect?: boolean };
    const token = localStorage.getItem('token');
    if (token) {
      appConfig.headers.Authorization = `Bearer ${token}`;
    }
    return appConfig;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: unknown }>) => {
    const config = error.config as AppAxiosRequestConfig | undefined;
    if (error.response?.status === 401 && !config?.skipAuthRedirect) {
      clearAuthState();

      const currentPath = window.location.pathname;
      const isLoginPage = currentPath === '/login' || currentPath.startsWith('/auth/');

      appMessage.error('登录状态已失效，请重新登录');
      if (!isLoginPage) {
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }

    const detail = formatErrorDetail(error.response?.data?.detail);
    const status = error.response?.status;

    if (status === 400 && detail) {
      appMessage.error(detail);
    } else if (status === 403) {
      appMessage.error(detail || '权限不足，无法执行此操作');
    } else if (status === 404) {
      appMessage.error(detail || '请求的资源不存在');
    } else if (status === 500) {
      appMessage.error(detail || '服务器内部错误，请稍后重试');
    } else if (status === 422) {
      appMessage.error(detail || '提交的数据格式不正确');
    } else if (detail) {
      appMessage.error(detail);
    } else if (error.code === 'ERR_NETWORK') {
      appMessage.error('网络连接失败，请检查网络');
    } else if (!error.response) {
      appMessage.error('请求超时或网络异常');
    }

    return Promise.reject(error);
  }
);

export default api;
