import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

export const CONTRACTS_QUERY_KEY = 'contracts';

export type ContractProduct = {
  id: number;
  contract_id: number;
  product_id: number;
  product_name: string;
  quantity: number;
  unit_price: number;
  discount: number;
  amount: number;
  notes?: string;
};

export type PaymentPlan = {
  id: number;
  contract_id: number;
  plan_stage: string;
  plan_amount: number;
  plan_date?: string;
  actual_amount: number;
  actual_date?: string;
  payment_status: string;
  notes?: string;
};

export type Contract = {
  id: number;
  contract_code: string;
  contract_name: string;
  project_id: number;
  project_name?: string;
  contract_direction: string;
  contract_status: string;
  terminal_customer_id?: number;
  terminal_customer_name?: string;
  channel_id?: number;
  channel_name?: string;
  contract_amount: number;
  signing_date?: string;
  effective_date?: string;
  expiry_date?: string;
  contract_file_url?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
  products: ContractProduct[];
  payment_plans: PaymentPlan[];
};

export type ContractCreate = {
  contract_name: string;
  project_id: number;
  contract_direction: string;
  contract_status?: string;
  terminal_customer_id?: number;
  channel_id?: number;
  contract_amount: number;
  signing_date?: string;
  effective_date?: string;
  expiry_date?: string;
  contract_file_url?: string;
  notes?: string;
  products?: {
    product_id: number;
    product_name: string;
    quantity: number;
    unit_price: number;
    discount?: number;
    amount: number;
    notes?: string;
  }[];
  payment_plans?: {
    plan_stage: string;
    plan_amount: number;
    plan_date?: string;
    actual_amount?: number;
    actual_date?: string;
    payment_status?: string;
    notes?: string;
  }[];
};

export type ContractUpdate = Partial<ContractCreate>;

export const useContracts = (projectId?: number) => {
  return useQuery({
    queryKey: [CONTRACTS_QUERY_KEY, projectId],
    queryFn: () => {
      const params = new URLSearchParams();
      if (projectId) params.append('project_id', String(projectId));
      const url = projectId ? `/contracts?${params.toString()}` : '/contracts';
      return api.get<Contract[]>(url).then(res => res.data);
    },
  });
};

export const useContract = (id: number) => {
  return useQuery({
    queryKey: [CONTRACTS_QUERY_KEY, id],
    queryFn: () => api.get<Contract>(`/contracts/${id}`).then(res => res.data),
    enabled: !!id,
  });
};

export const useCreateContract = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (contract: ContractCreate) => 
      api.post<Contract>('/contracts', contract).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CONTRACTS_QUERY_KEY] });
    },
  });
};

export const useUpdateContract = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, contract }: { id: number; contract: ContractUpdate }) => 
      api.put<Contract>(`/contracts/${id}`, contract).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CONTRACTS_QUERY_KEY] });
    },
  });
};

export const useDeleteContract = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete(`/contracts/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CONTRACTS_QUERY_KEY] });
    },
  });
};