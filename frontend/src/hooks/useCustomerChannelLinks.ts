import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

export interface CustomerChannelLink {
  id: number;
  customer_id: number;
  channel_id: number;
  channel_name: string;
  channel_code: string;
  role: '主渠道' | '协作渠道' | '历史渠道';
  discount_rate: number;
  start_date: string;
  end_date: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export const useCustomerChannelLinks = (customerId: number) => {
  return useQuery({
    queryKey: ['customer-channel-links', customerId],
    queryFn: () => api.get(`/customer-channel-links?customer_id=${customerId}`).then(res => res.data),
    enabled: !!customerId,
  });
};
