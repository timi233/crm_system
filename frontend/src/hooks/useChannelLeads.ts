import { useQuery } from '@tanstack/react-query';

import api from '../services/api';

export const CHANNEL_LEADS_KEY = 'channel-leads';

export type ChannelLead = {
  id: number;
  lead_code: string;
  lead_name: string;
  stage: string;
  contact_person?: string;
  sales_owner_name?: string;
  created_at?: string;
};

export type PaginatedResponse<T> = {
  total: number;
  items: T[];
};

export const useChannelLeads = (
  channelId: number,
  options?: { enabled?: boolean; page?: number; pageSize?: number }
) => {
  const page = options?.page ?? 1;
  const pageSize = options?.pageSize ?? 10;
  const skip = (page - 1) * pageSize;

  return useQuery({
    queryKey: [CHANNEL_LEADS_KEY, channelId, page, pageSize],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<ChannelLead>>(
        `/channels/${channelId}/leads?skip=${skip}&limit=${pageSize}`
      );
      return response.data;
    },
    enabled: !!channelId && (options?.enabled !== false),
  });
};
