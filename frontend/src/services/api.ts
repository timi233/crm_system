import axios, { AxiosError } from 'axios';
import { message } from 'antd';

const getApiBaseUrl = () => {
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  const { protocol, hostname } = window.location;
  return `${protocol}//${hostname}:8000`;
};

const API_BASE_URL = getApiBaseUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
      return Promise.reject(error);
    }

    const detail = error.response?.data?.detail;
    const status = error.response?.status;

    if (status === 400 && detail) {
      message.error(detail);
    } else if (status === 403) {
      message.error(detail || '权限不足，无法执行此操作');
    } else if (status === 404) {
      message.error(detail || '请求的资源不存在');
    } else if (status === 500) {
      message.error(detail || '服务器内部错误，请稍后重试');
    } else if (status === 422) {
      message.error(detail || '提交的数据格式不正确');
    } else if (detail) {
      message.error(detail);
    } else if (error.code === 'ERR_NETWORK') {
      message.error('网络连接失败，请检查网络');
    } else if (!error.response) {
      message.error('请求超时或网络异常');
    }

    return Promise.reject(error);
  }
);

export default api;
