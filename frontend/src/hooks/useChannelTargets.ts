import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

export const CHANNEL_TARGETS_KEY = 'channel-targets';

export type ChannelTarget = {
  id: number;
  year: number;
  quarter: string;
  month: string;
  performance_target: number;
  achieved_performance: number;
};

export type PaginatedResponse<T> = {
  total: number;
  items: T[];
};

export const useChannelTargets = (channelId: number, options?: { enabled?: boolean }) => {
  return useQuery({
    queryKey: [CHANNEL_TARGETS_KEY, channelId],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<ChannelTarget>>(`/channels/${channelId}/targets`);
      return response.data;
    },
    enabled: !!channelId && (options?.enabled !== false),
  });
};
