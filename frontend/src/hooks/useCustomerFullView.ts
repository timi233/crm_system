import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { useSelector } from 'react-redux';
import { RootState } from '../store/store';

export const CUSTOMER_FULL_VIEW_KEY = 'customer-full-view';
export const CUSTOMER_FINANCE_VIEW_KEY = 'customer-finance-view';

export type CustomerSummary = {
  leads_count: number;
  opportunities_count: number;
  projects_count: number;
  follow_ups_count: number;
  contracts_count: number;
};

export type RelatedLead = {
  id: number;
  lead_code: string;
  lead_name: string;
  lead_stage: string;
  lead_source: string;
  estimated_budget: number | null;
  sales_owner_name: string;
  converted_to_opportunity: boolean;
};

export type RelatedOpportunity = {
  id: number;
  opportunity_code: string;
  opportunity_name: string;
  opportunity_stage: string;
  expected_contract_amount: number | null;
  sales_owner_name: string;
  channel_name: string | null;
  project_id: number | null;
};

export type RelatedProject = {
  id: number;
  project_code: string;
  project_name: string;
  project_status: string;
  business_type: string;
  downstream_contract_amount: number | null;
  sales_owner_name: string;
};

export type RelatedFollowUp = {
  id: number;
  follow_up_date: string;
  follow_up_method: string;
  follow_up_content: string;
  follow_up_conclusion: string;
  follower_name: string;
};

export type RelatedContract = {
  id: number;
  contract_code: string;
  contract_name: string;
  contract_direction: string;
  contract_status: string;
  contract_amount: number | null;
  signing_date: string | null;
};

export type CustomerFullView = {
  customer: {
    id: number;
    customer_code: string;
    customer_name: string;
    credit_code: string;
    customer_industry: string;
    customer_region: string;
    customer_status: string;
    main_contact: string | null;
    phone: string | null;
    notes: string | null;
    customer_owner_name: string;
  };
  channel: {
    id: number;
    channel_code: string;
    company_name: string;
    channel_type: string;
    status: string;
    main_contact: string | null;
    phone: string | null;
  } | null;
  summary: CustomerSummary;
  leads: RelatedLead[];
  opportunities: RelatedOpportunity[];
  projects: RelatedProject[];
  follow_ups: RelatedFollowUp[];
  contracts: RelatedContract[];
};

// Finance-specific view types
export type PaymentPlanView = {
  id: number;
  contract_code: string;
  contract_name: string;
  plan_stage: string;
  plan_amount: number;
  plan_date: string | null;
  actual_amount: number | null;
  actual_date: string | null;
  payment_status: string;
};

export type ProjectFinanceView = {
  id: number;
  project_code: string;
  project_name: string;
  project_status: string;
  downstream_contract_amount: number;
  upstream_procurement_amount: number | null;
  direct_project_investment: number | null;
  additional_investment: number | null;
  gross_margin: number | null;
  actual_payment_amount: number | null;
  winning_date: string | null;
  acceptance_date: string | null;
  first_payment_date: string | null;
};

export type ContractFinanceView = {
  id: number;
  contract_code: string;
  contract_name: string;
  contract_direction: string;
  contract_status: string;
  contract_amount: number;
  signing_date: string | null;
  effective_date: string | null;
  expiry_date: string | null;
};

export type CustomerFinanceView = {
  customer_id: number;
  customer_name: string;
  customer_code: string;
  credit_code: string;
  customer_status: string;
  contracts: ContractFinanceView[];
  total_contract_amount: number;
  downstream_contract_amount: number;
  upstream_contract_amount: number;
  signed_contract_count: number;
  pending_contract_count: number;
  payment_plans: PaymentPlanView[];
  total_planned_amount: number;
  total_actual_amount: number;
  payment_completion_rate: number;
  projects: ProjectFinanceView[];
  total_project_downstream: number;
  total_project_upstream: number | null;
  total_gross_margin: number | null;
};

export const useCustomerFullView = (customerId: number) => {
  const { user } = useSelector((state: RootState) => state.auth);
  const userRole = user?.role;

  // Finance role uses finance-view endpoint
  if (userRole === 'finance') {
    return useQuery({
      queryKey: [CUSTOMER_FINANCE_VIEW_KEY, customerId],
      queryFn: () => api.get<CustomerFinanceView>(`/customers/${customerId}/finance-view`).then(res => res.data),
      enabled: !!customerId,
    });
  }

  // Other roles use full-view endpoint
  return useQuery({
    queryKey: [CUSTOMER_FULL_VIEW_KEY, customerId],
    queryFn: () => api.get<CustomerFullView>(`/customers/${customerId}/full-view`).then(res => res.data),
    enabled: !!customerId,
  });
};

// Separate hooks for explicit usage
export const useCustomerFinanceView = (customerId: number) => {
  return useQuery({
    queryKey: [CUSTOMER_FINANCE_VIEW_KEY, customerId],
    queryFn: () => api.get<CustomerFinanceView>(`/customers/${customerId}/finance-view`).then(res => res.data),
    enabled: !!customerId,
  });
};

export const useCustomerFullViewOnly = (customerId: number) => {
  return useQuery({
    queryKey: [CUSTOMER_FULL_VIEW_KEY, customerId],
    queryFn: () => api.get<CustomerFullView>(`/customers/${customerId}/full-view`).then(res => res.data),
    enabled: !!customerId,
  });
};