import { useQuery } from '@tanstack/react-query';

import api from '../services/api';
import { FollowUp } from './useFollowUps';

export const CHANNEL_FOLLOW_UPS_KEY = 'channel-follow-ups';

export type PaginatedResponse<T> = {
  total: number;
  items: T[];
};

export const useChannelFollowUps = (
  channelId: number,
  options?: { enabled?: boolean; page?: number; pageSize?: number }
) => {
  const page = options?.page ?? 1;
  const pageSize = options?.pageSize ?? 10;
  const skip = (page - 1) * pageSize;

  return useQuery({
    queryKey: [CHANNEL_FOLLOW_UPS_KEY, channelId, page, pageSize],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<FollowUp>>(
        `/channels/${channelId}/follow-ups?skip=${skip}&limit=${pageSize}`
      );
      return response.data;
    },
    enabled: !!channelId && (options?.enabled !== false),
  });
};
