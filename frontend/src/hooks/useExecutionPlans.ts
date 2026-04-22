import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import api from '../services/api';

export const EXECUTION_PLANS_QUERY_KEY = 'execution-plans';

export type ExecutionPlan = {
  id: number;
  channel_id: number;
  user_id: number;
  plan_type: 'monthly' | 'weekly';
  plan_category?: 'general' | 'training';
  plan_period: string;
  plan_content: string;
  execution_status?: string | null;
  key_obstacles?: string | null;
  next_steps?: string | null;
  status: 'planned' | 'in-progress' | 'completed' | 'archived';
  channel_name?: string | null;
  user_name?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type ExecutionPlanPayload = Omit<
  ExecutionPlan,
  'id' | 'channel_name' | 'user_name' | 'created_at' | 'updated_at'
>;

export type ExecutionPlanFilters = {
  channel_id?: number;
  user_id?: number;
  plan_status?: string;
  plan_type?: string;
  plan_category?: string;
  plan_period?: string;
};

export const useExecutionPlans = (filters?: ExecutionPlanFilters, enabled: boolean = true) => {
  return useQuery({
    queryKey: [EXECUTION_PLANS_QUERY_KEY, filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.channel_id) params.append('channel_id', String(filters.channel_id));
      if (filters?.user_id) params.append('user_id', String(filters.user_id));
      if (filters?.plan_status) params.append('plan_status', filters.plan_status);
      if (filters?.plan_type) params.append('plan_type', filters.plan_type);
      if (filters?.plan_category) params.append('plan_category', filters.plan_category);
      if (filters?.plan_period) params.append('plan_period', filters.plan_period);
      const response = await api.get<ExecutionPlan[]>(
        `/execution-plans/${params.toString() ? `?${params.toString()}` : ''}`
      );
      return response.data;
    },
    enabled,
  });
};

export const useCreateExecutionPlan = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ExecutionPlanPayload) => {
      const response = await api.post<ExecutionPlan>('/execution-plans/', payload);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [EXECUTION_PLANS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: ['channel-training-overview'] });
      queryClient.invalidateQueries({ queryKey: ['channel-full-view'] });
      queryClient.invalidateQueries({ queryKey: ['channel-execution-plans'] });
    },
  });
};

export const useUpdateExecutionPlan = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: Partial<ExecutionPlanPayload> }) => {
      const response = await api.put<ExecutionPlan>(`/execution-plans/${id}`, payload);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [EXECUTION_PLANS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [EXECUTION_PLANS_QUERY_KEY, variables.id] });
      queryClient.invalidateQueries({ queryKey: ['channel-training-overview'] });
      queryClient.invalidateQueries({ queryKey: ['channel-full-view'] });
      queryClient.invalidateQueries({ queryKey: ['channel-execution-plans'] });
    },
  });
};

export const useDeleteExecutionPlan = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/execution-plans/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [EXECUTION_PLANS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: ['channel-training-overview'] });
      queryClient.invalidateQueries({ queryKey: ['channel-full-view'] });
      queryClient.invalidateQueries({ queryKey: ['channel-execution-plans'] });
    },
  });
};
