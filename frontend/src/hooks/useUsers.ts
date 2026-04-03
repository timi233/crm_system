import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

export const USERS_QUERY_KEY = 'users';

export type User = {
  id: number;
  name: string;
  email: string;
  role: string;
  sales_leader_id?: number;
  sales_region?: string;
};

export const useUsers = () => {
  return useQuery({
    queryKey: [USERS_QUERY_KEY],
    queryFn: () => api.get<User[]>('/users').then(res => res.data),
  });
};

export const useUser = (id: number) => {
  return useQuery({
    queryKey: [USERS_QUERY_KEY, id],
    queryFn: () => api.get<User>(`/users/${id}`).then(res => res.data),
    enabled: !!id,
  });
};

export const useCreateUser = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (user: Omit<User, 'id'>) => 
      api.post<User>('/users', user).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [USERS_QUERY_KEY] });
    },
  });
};

export const useUpdateUser = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, user }: { id: number; user: Omit<User, 'id'> }) => 
      api.put<User>(`/users/${id}`, user).then(res => res.data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [USERS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [USERS_QUERY_KEY, variables.id] });
    },
  });
};

export const useDeleteUser = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.delete(`/users/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [USERS_QUERY_KEY] });
    },
  });
};
