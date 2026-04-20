import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import api from '../services/api';

export const CHANNEL_CONTACTS_KEY = 'channel-contacts';

export type ChannelContact = {
  id: number;
  channel_id: number;
  name: string;
  title?: string;
  phone?: string;
  email?: string;
  is_primary: boolean;
  notes?: string;
  created_at?: string;
};

export type ChannelContactPayload = {
  name: string;
  title?: string;
  phone?: string;
  email?: string;
  is_primary?: boolean;
  notes?: string;
};

export const useChannelContacts = (channelId: number, options?: { enabled?: boolean }) => {
  return useQuery({
    queryKey: [CHANNEL_CONTACTS_KEY, channelId],
    queryFn: async () => {
      const response = await api.get<ChannelContact[]>(`/channels/${channelId}/contacts`);
      return response.data;
    },
    enabled: !!channelId && (options?.enabled !== false),
  });
};

export const useCreateChannelContact = (channelId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: ChannelContactPayload) => {
      const response = await api.post<ChannelContact>(`/channels/${channelId}/contacts`, payload);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CHANNEL_CONTACTS_KEY, channelId] });
    },
  });
};

export const useUpdateChannelContact = (channelId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ contactId, payload }: { contactId: number; payload: ChannelContactPayload }) => {
      const response = await api.put<ChannelContact>(`/channels/${channelId}/contacts/${contactId}`, payload);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CHANNEL_CONTACTS_KEY, channelId] });
    },
  });
};

export const useDeleteChannelContact = (channelId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (contactId: number) => {
      await api.delete(`/channels/${channelId}/contacts/${contactId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CHANNEL_CONTACTS_KEY, channelId] });
    },
  });
};
