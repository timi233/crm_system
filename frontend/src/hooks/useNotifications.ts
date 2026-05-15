import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

export const NOTIFICATIONS_KEY = 'notifications';

export type Notification = {
  id: number;
  notification_type: string;
  title: string;
  content: string;
  entity_type: string | null;
  entity_id: number | null;
  entity_code: string | null;
  is_read: boolean;
  created_at: string;
  read_at: string | null;
};

export type NotificationsParams = {
  is_read?: boolean;
  type?: string;
  skip?: number;
  limit?: number;
};

export const useNotifications = (params?: NotificationsParams, enabled: boolean = true) => {
  return useQuery({
    queryKey: [NOTIFICATIONS_KEY, params],
    queryFn: () => {
      const p = new URLSearchParams();
      if (params?.is_read !== undefined) p.append('is_read', String(params.is_read));
      if (params?.type) p.append('type', params.type);
      if (params?.skip !== undefined) p.append('skip', String(params.skip));
      if (params?.limit !== undefined) p.append('limit', String(params.limit));
      return api.get<{ items: Notification[]; total: number }>(`/notifications?${p.toString()}`).then((r) => r.data);
    },
    enabled,
  });
};

export const useUnreadCount = (enabled: boolean = true) => {
  return useQuery({
    queryKey: [NOTIFICATIONS_KEY, 'unread-count'],
    queryFn: () =>
      api.get<{ count: number }>('/notifications/unread-count').then((r) => r.data),
    enabled,
  });
};

export const useMarkNotificationRead = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      api.post<Notification>(`/notifications/${id}/mark-read`).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [NOTIFICATIONS_KEY] });
    },
  });
};

export const useMarkAllRead = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (notificationType?: string) =>
      api.post('/notifications/mark-all-read', notificationType ? { notification_type: notificationType } : undefined).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [NOTIFICATIONS_KEY] });
    },
  });
};
