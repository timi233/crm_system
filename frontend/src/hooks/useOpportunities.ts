import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

export const OPPORTUNITIES_QUERY_KEY = 'opportunities';

export type Opportunity = {
  id: number;
  opportunity_code: string;
  opportunity_name: string;
  terminal_customer_id: number;
  terminal_customer_name?: string;
  opportunity_source: string;
  opportunity_stage: string;
  lead_grade: string;
  expected_contract_amount?: number;
  expected_close_date?: string;
  sales_owner_id: number;
  sales_owner_name?: string;
  channel_id?: number;
  channel_name?: string;
  project_id?: number;
  loss_reason?: string;
  created_at?: string;
};

export const useOpportunities = () => {
  return useQuery({
    queryKey: [OPPORTUNITIES_QUERY_KEY],
    queryFn: () => api.get<Opportunity[]>('/opportunities').then(res => res.data),
  });
};

export const useOpportunity = (id: number) => {
  return useQuery({
    queryKey: [OPPORTUNITIES_QUERY_KEY, id],
    queryFn: () => api.get<Opportunity>(`/opportunities/${id}`).then(res => res.data),
    enabled: !!id,
  });
};

export const useCreateOpportunity = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (opportunity: Omit<Opportunity, 'id'>) => 
      api.post<Opportunity>('/opportunities', opportunity).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [OPPORTUNITIES_QUERY_KEY] });
    },
  });
};

export const useUpdateOpportunity = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, opportunity }: { id: number; opportunity: Omit<Opportunity, 'id'> }) => 
      api.put<Opportunity>(`/opportunities/${id}`, opportunity).then(res => res.data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [OPPORTUNITIES_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [OPPORTUNITIES_QUERY_KEY, variables.id] });
    },
  });
};

export const useDeleteOpportunity = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.delete(`/opportunities/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [OPPORTUNITIES_QUERY_KEY] });
    },
  });
};
