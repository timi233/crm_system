import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

export const FOLLOW_UPS_QUERY_KEY = 'follow-ups';

export type FollowUp = {
  id: number;
  terminal_customer_id?: number;
  terminal_customer_name?: string;
  lead_id?: number;
  lead_name?: string;
  opportunity_id?: number;
  opportunity_name?: string;
  project_id?: number;
  project_name?: string;
  follower_id: number;
  follower_name?: string;
  follow_up_date: string;
  follow_up_method: string;
  follow_up_content: string;
  follow_up_conclusion: string;
  next_action?: string;
  next_follow_up_date?: string;
  created_at?: string;
};

export type FollowUpCreate = {
  terminal_customer_id?: number;
  lead_id?: number;
  opportunity_id?: number;
  project_id?: number;
  follow_up_date: string;
  follow_up_method: string;
  follow_up_content: string;
  follow_up_conclusion: string;
  next_action?: string;
  next_follow_up_date?: string;
};

export type FollowUpFilters = {
  terminal_customer_id?: number;
  lead_id?: number;
  opportunity_id?: number;
  project_id?: number;
};

export const useFollowUps = (filters?: FollowUpFilters) => {
  return useQuery({
    queryKey: [FOLLOW_UPS_QUERY_KEY, filters],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filters?.terminal_customer_id) params.append('terminal_customer_id', String(filters.terminal_customer_id));
      if (filters?.lead_id) params.append('lead_id', String(filters.lead_id));
      if (filters?.opportunity_id) params.append('opportunity_id', String(filters.opportunity_id));
      if (filters?.project_id) params.append('project_id', String(filters.project_id));
      const url = params.toString() ? `/follow-ups/?${params.toString()}` : '/follow-ups/';
      return api.get<FollowUp[]>(url).then(res => res.data);
    },
  });
};

export const useFollowUp = (id: number) => {
  return useQuery({
    queryKey: [FOLLOW_UPS_QUERY_KEY, id],
    queryFn: () => api.get<FollowUp>(`/follow-ups/${id}`).then(res => res.data),
    enabled: !!id,
  });
};

export const useCreateFollowUp = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (followUp: FollowUpCreate) => 
      api.post<FollowUp>('/follow-ups/', followUp).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [FOLLOW_UPS_QUERY_KEY] });
    },
  });
};

export const useUpdateFollowUp = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<FollowUpCreate> }) => 
      api.put<FollowUp>(`/follow-ups/${id}`, data).then(res => res.data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [FOLLOW_UPS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [FOLLOW_UPS_QUERY_KEY, variables.id] });
    },
  });
};

export const useDeleteFollowUp = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.delete(`/follow-ups/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [FOLLOW_UPS_QUERY_KEY] });
    },
  });
};