import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

export const CHANNEL_WORK_ORDERS_KEY = 'channel-work-orders';

export type ChannelWorkOrder = {
  id: number;
  work_order_no: string;
  order_type: string;
  status: string;
  customer_name: string;
  description: string;
};

export type PaginatedResponse<T> = {
  total: number;
  items: T[];
};

export const useChannelWorkOrders = (channelId: number, options?: { enabled?: boolean }) => {
  return useQuery({
    queryKey: [CHANNEL_WORK_ORDERS_KEY, channelId],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<ChannelWorkOrder>>(`/channels/${channelId}/work-orders`);
      return response.data;
    },
    enabled: !!channelId && (options?.enabled !== false),
  });
};
