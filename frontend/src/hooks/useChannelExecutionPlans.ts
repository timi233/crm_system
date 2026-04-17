import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

export const CHANNEL_EXECUTION_PLANS_KEY = 'channel-execution-plans';

export type ChannelExecutionPlan = {
  id: number;
  plan_type: string;
  plan_period: string;
  status: string;
  plan_content: string;
};

export type PaginatedResponse<T> = {
  total: number;
  items: T[];
};

export const useChannelExecutionPlans = (channelId: number, options?: { enabled?: boolean }) => {
  return useQuery({
    queryKey: [CHANNEL_EXECUTION_PLANS_KEY, channelId],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<ChannelExecutionPlan>>(`/channels/${channelId}/execution-plans`);
      return response.data;
    },
    enabled: !!channelId && (options?.enabled !== false),
  });
};
