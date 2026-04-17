import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

export const NINE_A_QUERY_KEY = 'nine-a';

export type NineA = {
  id: number;
  opportunity_id: number;
  key_events?: string;
  budget?: number;
  decision_chain_influence?: string;
  customer_challenges?: string;
  customer_needs?: string;
  solution_differentiation?: string;
  competitors?: string;
  buying_method?: string;
  close_date?: string;
};

export type NineAVersion = {
  id: number;
  opportunity_id: number;
  version_number: number;
  key_events?: string;
  budget?: number;
  decision_chain_influence?: string;
  customer_challenges?: string;
  customer_needs?: string;
  solution_differentiation?: string;
  competitors?: string;
  buying_method?: string;
  close_date?: string;
  created_at?: string;
  created_by_name?: string;
};

export type NineACreate = {
  key_events?: string;
  budget?: number;
  decision_chain_influence?: string;
  customer_challenges?: string;
  customer_needs?: string;
  solution_differentiation?: string;
  competitors?: string;
  buying_method?: string;
  close_date?: string;
};

export const useNineA = (opportunityId: number) => {
  return useQuery({
    queryKey: [NINE_A_QUERY_KEY, opportunityId],
    queryFn: () => api.get<NineA | null>(`/opportunities/${opportunityId}/nine-a`).then(res => res.data),
    enabled: !!opportunityId,
  });
};

export const useNineAVersions = (opportunityId: number) => {
  return useQuery({
    queryKey: [NINE_A_QUERY_KEY, 'versions', opportunityId],
    queryFn: () => api.get<NineAVersion[]>(`/opportunities/${opportunityId}/nine-a/versions`).then(res => res.data),
    enabled: !!opportunityId,
  });
};

export const useCreateNineA = (opportunityId: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: NineACreate) => 
      api.post<NineA>(`/opportunities/${opportunityId}/nine-a`, data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [NINE_A_QUERY_KEY, opportunityId] });
      queryClient.invalidateQueries({ queryKey: [NINE_A_QUERY_KEY, 'versions', opportunityId] });
    },
  });
};

export const useUpdateNineA = (opportunityId: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: NineACreate) => 
      api.put<NineA>(`/opportunities/${opportunityId}/nine-a`, data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [NINE_A_QUERY_KEY, opportunityId] });
      queryClient.invalidateQueries({ queryKey: [NINE_A_QUERY_KEY, 'versions', opportunityId] });
    },
  });
};