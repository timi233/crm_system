import { useSelector } from 'react-redux';
import { RootState } from '../store/store';

interface User {
  id: number;
  name: string;
  email: string;
  role: string;
  open_id?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

export const useAuth = (): AuthState => {
  const { user, token, isAuthenticated } = useSelector((state: RootState) => state.auth);
  return { user, token, isAuthenticated };
};