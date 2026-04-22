import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import api from '../services/api';

export const UNIFIED_TARGETS_QUERY_KEY = 'unified-targets';

export type UnifiedTarget = {
  id: number;
  target_type: 'channel' | 'person';
  channel_id?: number | null;
  user_id?: number | null;
  year: number;
  quarter?: number | null;
  month?: number | null;
  performance_target?: number | null;
  opportunity_target?: number | null;
  project_count_target?: number | null;
  development_goal?: string | null;
  achieved_performance?: number | null;
  achieved_opportunity?: number | null;
  achieved_project_count?: number | null;
  channel_name?: string | null;
  user_name?: string | null;
};

export type UnifiedTargetPayload = Omit<
  UnifiedTarget,
  | 'id'
  | 'achieved_performance'
  | 'achieved_opportunity'
  | 'achieved_project_count'
  | 'channel_name'
  | 'user_name'
>;

export type UnifiedTargetFilters = {
  channel_id?: number;
  user_id?: number;
  year?: number;
  quarter?: number;
  month?: number;
};

export const useUnifiedTargets = (filters?: UnifiedTargetFilters, enabled: boolean = true) => {
  return useQuery({
    queryKey: [UNIFIED_TARGETS_QUERY_KEY, filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.channel_id) params.append('channel_id', String(filters.channel_id));
      if (filters?.user_id) params.append('user_id', String(filters.user_id));
      if (filters?.year) params.append('year', String(filters.year));
      if (filters?.quarter) params.append('quarter', String(filters.quarter));
      if (filters?.month) params.append('month', String(filters.month));
      const response = await api.get<UnifiedTarget[]>(
        `/unified-targets/${params.toString() ? `?${params.toString()}` : ''}`
      );
      return response.data;
    },
    enabled,
  });
};

export const useCreateUnifiedTarget = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: UnifiedTargetPayload) => {
      const response = await api.post<UnifiedTarget>('/unified-targets/', payload);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [UNIFIED_TARGETS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: ['channel-performance-overview'] });
      queryClient.invalidateQueries({ queryKey: ['channel-full-view'] });
    },
  });
};

export const useUpdateUnifiedTarget = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: Partial<UnifiedTargetPayload> }) => {
      const response = await api.put<UnifiedTarget>(`/unified-targets/${id}`, payload);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [UNIFIED_TARGETS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [UNIFIED_TARGETS_QUERY_KEY, variables.id] });
      queryClient.invalidateQueries({ queryKey: ['channel-performance-overview'] });
      queryClient.invalidateQueries({ queryKey: ['channel-full-view'] });
    },
  });
};

export const useDeleteUnifiedTarget = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/unified-targets/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [UNIFIED_TARGETS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: ['channel-performance-overview'] });
      queryClient.invalidateQueries({ queryKey: ['channel-full-view'] });
    },
  });
};
