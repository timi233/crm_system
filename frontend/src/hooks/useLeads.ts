import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

export const LEADS_QUERY_KEY = 'leads';

export type Lead = {
  id: number;
  lead_code: string;
  lead_name: string;
  terminal_customer_id: number;
  terminal_customer_name?: string;
  source_channel_id?: number;
  source_channel_name?: string;
  channel_id?: number;
  channel_name?: string;
  lead_stage: string;
  lead_source?: string;
  contact_person?: string;
  contact_phone?: string;
  products?: string[];
  estimated_budget?: number;
  has_confirmed_requirement: boolean;
  has_confirmed_budget: boolean;
  converted_to_opportunity: boolean;
  opportunity_id?: number;
  sales_owner_id: number;
  sales_owner_name?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
};

// 创建时只提交可写字段，排除只读字段（xxx_name 结尾的引用名称）和自动生成字段
export type LeadCreate = {
  lead_name: string;
  terminal_customer_id: number;
  source_channel_id?: number;
  channel_id?: number;
  lead_stage: string;
  lead_source?: string;
  contact_person?: string;
  contact_phone?: string;
  products?: string[];
  estimated_budget?: number;
  has_confirmed_requirement?: boolean;
  has_confirmed_budget?: boolean;
  sales_owner_id: number;
  notes?: string;
};

export type LeadUpdate = Partial<LeadCreate>;

export type LeadConvertRequest = {
  opportunity_name: string;
  expected_contract_amount: number;
  opportunity_source?: string;
};

export const useLeads = () => {
  return useQuery({
    queryKey: [LEADS_QUERY_KEY],
    queryFn: () => api.get<Lead[]>('/leads').then(res => res.data),
  });
};

export const useLead = (id: number) => {
  return useQuery({
    queryKey: [LEADS_QUERY_KEY, id],
    queryFn: () => api.get<Lead>(`/leads/${id}`).then(res => res.data),
    enabled: !!id,
  });
};

export const useCreateLead = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (lead: LeadCreate) => 
      api.post<Lead>('/leads', lead).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [LEADS_QUERY_KEY] });
    },
  });
};

export const useUpdateLead = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, lead }: { id: number; lead: LeadUpdate }) => 
      api.put<Lead>(`/leads/${id}`, lead).then(res => res.data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [LEADS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [LEADS_QUERY_KEY, variables.id] });
    },
  });
};

export const useDeleteLead = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.delete(`/leads/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [LEADS_QUERY_KEY] });
    },
  });
};

export const useConvertLeadToOpportunity = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, request }: { id: number; request: LeadConvertRequest }) => 
      api.post(`/leads/${id}/convert`, request).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [LEADS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: ['opportunities'] });
    },
  });
};