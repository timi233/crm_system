import { useSelector } from 'react-redux';
import { RootState } from '../store/store';
import { User } from '../store/slices/authSlice';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

export const useAuth = (): AuthState => {
  const { user, token, isAuthenticated } = useSelector((state: RootState) => state.auth);
  return { user, token, isAuthenticated };
};