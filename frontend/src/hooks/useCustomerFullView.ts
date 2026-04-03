import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

export const CUSTOMER_FULL_VIEW_KEY = 'customer-full-view';

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

export const useCustomerFullView = (customerId: number) => {
  return useQuery({
    queryKey: [CUSTOMER_FULL_VIEW_KEY, customerId],
    queryFn: () => api.get<CustomerFullView>(`/customers/${customerId}/full-view`).then(res => res.data),
    enabled: !!customerId,
  });
};