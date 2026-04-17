import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

export const CHANNEL_ASSIGNMENTS_KEY = 'channel-assignments';

export type ChannelAssignment = {
  id: number;
  user_name: string;
  permission_level: string;
  assigned_at: string;
};

export const useChannelAssignments = (channelId: number, options?: { enabled?: boolean }) => {
  return useQuery({
    queryKey: [CHANNEL_ASSIGNMENTS_KEY, channelId],
    queryFn: () => api.get<ChannelAssignment[]>(`/channels/${channelId}/assignments`).then(res => res.data),
    enabled: !!channelId && (options?.enabled !== false),
  });
};
