import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

export const DASHBOARD_KEY = 'dashboard';

export type DashboardSummary = {
  leads_count: number;
  opportunities_count: number;
  projects_count: number;
  contracts_count: number;
  pending_followups: number;
  alerts_count: number;
  won_opportunities: number;
  lost_opportunities: number;
  quarterly_target: number;
  quarterly_achieved: number;
  monthly_target: number;
  monthly_achieved: number;
  quarterly_forecast_amount: number;
};

export type DashboardTodoItem = {
  id: number;
  type: string;
  title: string;
  customer_name: string;
  due_date: string | null;
  priority: string;
  entity_type: string;
  entity_id: number;
};

export type DashboardFollowUpItem = {
  id: number;
  customer_name: string;
  follow_up_date: string;
  follow_up_method: string;
  follow_up_content: string;
  follower_name: string;
  entity_type: string;
  entity_id: number;
};

export type DashboardNotificationItem = {
  id: number;
  type: string;
  title: string;
  content: string;
  created_at: string;
  is_read: boolean;
  entity_type?: string;
  entity_id?: number;
  entity_code?: string;
};

export const useDashboardSummary = () => {
  return useQuery({
    queryKey: [DASHBOARD_KEY, 'summary'],
    queryFn: () => api.get<DashboardSummary>('/dashboard/summary').then(res => res.data),
  });
};

export const useDashboardTodos = () => {
  return useQuery({
    queryKey: [DASHBOARD_KEY, 'todos'],
    queryFn: () => api.get<DashboardTodoItem[]>('/dashboard/todos').then(res => res.data),
  });
};

export const useDashboardRecentFollowups = (limit: number = 5) => {
  return useQuery({
    queryKey: [DASHBOARD_KEY, 'recent-followups', limit],
    queryFn: () => api.get<DashboardFollowUpItem[]>(`/dashboard/recent-followups?limit=${limit}`).then(res => res.data),
  });
};

export const useDashboardNotifications = () => {
  return useQuery({
    queryKey: [DASHBOARD_KEY, 'notifications'],
    queryFn: () => api.get<DashboardNotificationItem[]>('/dashboard/notifications').then(res => res.data),
  });
};

export const useMarkNotificationsRead = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (notifications: { entity_type: string; entity_id: number; type: string }[]) =>
      api.post('/dashboard/notifications/mark-read', { notifications }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [DASHBOARD_KEY, 'notifications'] });
    },
  });
};

export type TeamRankItem = {
  rank: number;
  user_id: number;
  user_name: string;
  amount: number;
};

export const useTeamRank = (limit: number = 5) => {
  return useQuery({
    queryKey: [DASHBOARD_KEY, 'team-rank', limit],
    queryFn: () => api.get<TeamRankItem[]>(`/dashboard/team-rank?limit=${limit}`).then(res => res.data),
  });
};