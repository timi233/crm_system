import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

export const CHANNELS_QUERY_KEY = 'channels';

export type Channel = {
  id: number;
  channel_code: string;
  company_name: string;
  channel_type: string;
  status: string;
  main_contact?: string;
  phone?: string;
  email?: string;
  province?: string;
  city?: string;
  address?: string;
  credit_code?: string;
  bank_name?: string;
  bank_account?: string;
  website?: string;
  wechat?: string;
  cooperation_products?: string;
  cooperation_region?: string;
  discount_rate?: number;
  billing_info?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
  current_user_permission_level?: 'read' | 'write' | 'admin' | null;
  can_edit?: boolean;
  can_delete?: boolean;
};

export type ChannelCreate = Omit<Channel, 'id' | 'channel_code' | 'created_at' | 'updated_at'>;
export type ChannelUpdate = Partial<ChannelCreate>;

export const useChannels = (
  filters?: { channel_type?: string; status?: string },
  enabled: boolean = true
) => {
  return useQuery({
    queryKey: [CHANNELS_QUERY_KEY, filters],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filters?.channel_type) params.append('channel_type', filters.channel_type);
      if (filters?.status) params.append('status', filters.status);
      const url = params.toString() ? `/channels/?${params.toString()}` : '/channels/';
      return api.get<Channel[]>(url).then(res => res.data);
    },
    enabled,
  });
};

export const useChannel = (id: number) => {
  return useQuery({
    queryKey: [CHANNELS_QUERY_KEY, id],
    queryFn: () => api.get<Channel>(`/channels/${id}`).then(res => res.data),
    enabled: !!id,
  });
};

export const useCreateChannel = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (channel: ChannelCreate) => 
      api.post<Channel>('/channels/', channel).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CHANNELS_QUERY_KEY] });
    },
  });
};

export const useUpdateChannel = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, channel }: { id: number; channel: ChannelUpdate }) => 
      api.put<Channel>(`/channels/${id}`, channel).then(res => res.data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [CHANNELS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [CHANNELS_QUERY_KEY, variables.id] });
    },
  });
};

export const useDeleteChannel = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.delete(`/channels/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CHANNELS_QUERY_KEY] });
    },
  });
};
