import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

export const ALERTS_KEY = 'alerts';

export type AlertItem = {
  alert_type: string;
  priority: string;
  title: string;
  content: string;
  entity_type?: string;
  entity_id?: number;
  entity_code?: string;
  entity_name?: string;
  created_at: string;
};

export type AlertSummary = {
  high: number;
  medium: number;
  low: number;
  total: number;
};

export type AlertRule = {
  id: number;
  rule_code: string;
  rule_name: string;
  rule_type: string;
  entity_type: string;
  priority: string;
  threshold_days: number;
  threshold_amount: number;
  description?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
};

export type AlertRuleCreate = {
  rule_code: string;
  rule_name: string;
  rule_type: string;
  entity_type: string;
  priority?: string;
  threshold_days?: number;
  threshold_amount?: number;
  description?: string;
  is_active?: boolean;
};

export const useAlerts = () => {
  return useQuery({
    queryKey: [ALERTS_KEY],
    queryFn: () => api.get<AlertItem[]>('/alerts').then(res => res.data),
  });
};

export const useAlertSummary = () => {
  return useQuery({
    queryKey: [ALERTS_KEY, 'summary'],
    queryFn: () => api.get<AlertSummary>('/alerts/summary').then(res => res.data),
  });
};

export const useAlertRules = () => {
  return useQuery({
    queryKey: [ALERTS_KEY, 'rules'],
    queryFn: () => api.get<AlertRule[]>('/alert-rules').then(res => res.data),
  });
};

export const useCreateAlertRule = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (rule: AlertRuleCreate) => 
      api.post<AlertRule>('/alert-rules', rule).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ALERTS_KEY, 'rules'] });
    },
  });
};

export const useUpdateAlertRule = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, rule }: { id: number; rule: AlertRuleCreate }) =>
      api.put<AlertRule>(`/alert-rules/${id}`, rule).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ALERTS_KEY, 'rules'] });
    },
  });
};

export const useDeleteAlertRule = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete(`/alert-rules/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ALERTS_KEY, 'rules'] });
    },
  });
};