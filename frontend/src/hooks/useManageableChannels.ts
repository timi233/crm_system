import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

export const useManageableChannels = () => {
  return useQuery({
    queryKey: ['manageable-channels'],
    queryFn: async () => {
      const response = await api.get('/channels/me/manageable');
      return response.data;
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 10,
  });
};