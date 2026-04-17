import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

export const CHANNEL_ASSIGNMENTS_KEY = 'channel-assignments';

export type ChannelAssignment = {
  id: number;
  user_name: string;
  permission_level: string;
  assigned_at: string;
};

export type PaginatedResponse<T> = {
  total: number;
  items: T[];
};

export const useChannelAssignments = (channelId: number, options?: { enabled?: boolean }) => {
  return useQuery({
    queryKey: [CHANNEL_ASSIGNMENTS_KEY, channelId],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<ChannelAssignment>>(`/channels/${channelId}/assignments`);
      return response.data;
    },
    enabled: !!channelId && (options?.enabled !== false),
  });
};
