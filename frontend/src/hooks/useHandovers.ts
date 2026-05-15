import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

export const HANDOVER_KEY = 'handovers';

export type HandoverRequest = {
  id: number;
  from_user_id: number;
  to_user_id: number | null;
  team_manager_user_id: number | null;
  status: string;
  scope_config: Record<string, any> | null;
  preview_summary: Record<string, any> | null;
  execution_summary: Record<string, any> | null;
  created_at: string | null;
  decided_at: string | null;
  executed_at: string | null;
  error_message: string | null;
};

export type AssetsPreview = Record<string, { count: number; field: string }>;

export type HandoverListParams = {
  status?: string;
  skip?: number;
  limit?: number;
};

export const useHandoverRequests = (params?: HandoverListParams, enabled: boolean = true) => {
  return useQuery({
    queryKey: [HANDOVER_KEY, params],
    queryFn: () => {
      const p = new URLSearchParams();
      if (params?.status) p.append('status', params.status);
      if (params?.skip !== undefined) p.append('skip', String(params.skip));
      if (params?.limit !== undefined) p.append('limit', String(params.limit));
      return api.get<HandoverRequest[]>(`/handover/requests?${p.toString()}`).then((r) => r.data);
    },
    enabled,
  });
};

export const useHandoverRequest = (id: number, enabled: boolean = true) => {
  return useQuery({
    queryKey: [HANDOVER_KEY, id],
    queryFn: () =>
      api.get<HandoverRequest>(`/handover/requests/${id}`).then((r) => r.data),
    enabled,
  });
};

export const useAssetsPreview = (id: number, enabled: boolean = true) => {
  return useQuery({
    queryKey: [HANDOVER_KEY, id, 'assets'],
    queryFn: () =>
      api.get<AssetsPreview>(`/handover/requests/${id}/assets-preview`).then((r) => r.data),
    enabled,
  });
};

export const useAssignHandover = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: { to_user_id: number; scope_config?: Record<string, any> } }) =>
      api.post<HandoverRequest>(`/handover/requests/${id}/assign`, data).then((r) => r.data),
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: [HANDOVER_KEY] });
      qc.invalidateQueries({ queryKey: [HANDOVER_KEY, id] });
    },
  });
};

export const useExecuteHandover = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      api.post(`/handover/requests/${id}/execute`).then((r) => r.data),
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: [HANDOVER_KEY] });
      qc.invalidateQueries({ queryKey: [HANDOVER_KEY, id] });
    },
  });
};

export const useCancelHandover = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: number; reason?: string }) =>
      api.post(`/handover/requests/${id}/cancel`, reason ? { reason } : undefined).then((r) => r.data),
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: [HANDOVER_KEY] });
      qc.invalidateQueries({ queryKey: [HANDOVER_KEY, id] });
    },
  });
};
