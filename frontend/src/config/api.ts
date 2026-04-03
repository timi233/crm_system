const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export { API_BASE_URL };

export const getApiUrl = (path: string) => `${API_BASE_URL}${path}`;

export const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};

export default API_BASE_URL;