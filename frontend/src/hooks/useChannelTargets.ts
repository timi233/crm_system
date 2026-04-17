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

export const useChannelTargets = (channelId: number, options?: { enabled?: boolean }) => {
  return useQuery({
    queryKey: [CHANNEL_TARGETS_KEY, channelId],
    queryFn: () => api.get<ChannelTarget[]>(`/channels/${channelId}/targets`).then(res => res.data),
    enabled: !!channelId && (options?.enabled !== false),
  });
};
