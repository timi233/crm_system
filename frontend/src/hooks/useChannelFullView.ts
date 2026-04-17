import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

export const CHANNEL_FULL_VIEW_KEY = 'channel-full-view';

export type ChannelSummary = {
  customers_count: number;
  opportunities_count: number;
  projects_count: number;
  contracts_count: number;
  work_orders_count: number;
  assignments_count: number;
  execution_plans_count: number;
  targets_count: number;
  total_contract_amount: number;
  active_plans_count: number;
};

export type RelatedCustomer = {
  id: number;
  customer_code: string;
  customer_name: string;
  customer_industry: string;
  customer_region: string;
  customer_status: string;
  customer_owner_name: string;
};

export type ChannelFullView = {
  channel: {
    id: number;
    channel_code: string;
    company_name: string;
    channel_type: string;
    status: string;
    main_contact: string | null;
    phone: string | null;
    email: string | null;
    province: string | null;
    city: string | null;
    address: string | null;
    credit_code: string | null;
    website: string | null;
    wechat: string | null;
    cooperation_region: string | null;
    discount_rate: number | null;
    notes: string | null;
  };
  summary: ChannelSummary;
  customers: RelatedCustomer[];
  opportunities: {
    id: number;
    opportunity_code: string;
    opportunity_name: string;
    opportunity_stage: string;
    expected_contract_amount: number | null;
    terminal_customer_name: string;
    sales_owner_name: string;
    project_id: number | null;
  }[];
  projects: {
    id: number;
    project_code: string;
    project_name: string;
    project_status: string;
    business_type: string;
    downstream_contract_amount: number | null;
    terminal_customer_name: string;
    sales_owner_name: string;
  }[];
  contracts: {
    id: number;
    contract_code: string;
    contract_name: string;
    contract_direction: string;
    contract_status: string;
    contract_amount: number | null;
    signing_date: string | null;
  }[];
  work_orders: {
    id: number;
    work_order_no: string;
    order_type: string;
    status: string;
    customer_name: string;
    description: string;
  }[];
  assignments: {
    id: number;
    user_name: string;
    permission_level: string;
    assigned_at: string;
  }[];
  execution_plans: {
    id: number;
    plan_type: string;
    plan_period: string;
    status: string;
    plan_content: string;
  }[];
  targets: {
    id: number;
    year: number;
    quarter: string;
    month: string;
    performance_target: number;
    achieved_performance: number;
  }[];
};

export const useChannelFullView = (channelId: number) => {
  return useQuery({
    queryKey: [CHANNEL_FULL_VIEW_KEY, channelId],
    queryFn: () => api.get<ChannelFullView>(`/channels/${channelId}/full-view`).then(res => res.data),
    enabled: !!channelId,
  });
};