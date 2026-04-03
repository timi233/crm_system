import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

export const REPORTS_KEY = 'reports';

export type SalesFunnelData = {
  leads: {
    total: number;
    by_stage: Record<string, number>;
    converted: number;
    lost: number;
  };
  opportunities: {
    total: number;
    by_stage: Record<string, number>;
    total_amount: number;
    won: number;
    lost: number;
  };
  projects: {
    total: number;
    by_status: Record<string, number>;
    total_amount: number;
  };
  contracts: {
    total: number;
    by_status: Record<string, number>;
    total_amount: number;
  };
  conversion_rates: {
    lead_to_opportunity: number;
    opportunity_to_project: number;
  };
};

export type PerformanceData = {
  by_user: {
    user_id: number;
    user_name: string;
    contract_count: number;
    contract_amount: number;
    received_amount: number;
    pending_amount: number;
    gross_margin: number;
  }[];
  by_month: {
    month: string;
    contract_amount: number;
    contract_count: number;
  }[];
  total_contract_amount: number;
  total_received_amount: number;
  total_pending_amount: number;
};

export type PaymentProgressData = {
  total_plan_amount: number;
  total_actual_amount: number;
  total_pending_amount: number;
  overdue_amount: number;
  overdue_count: number;
  contracts: {
    contract_id: number;
    contract_code: string;
    contract_name: string;
    contract_amount: number;
    plan_amount: number;
    actual_amount: number;
    pending_amount: number;
    overdue_amount: number;
    progress_percentage: number;
    payment_count: number;
    completed_count: number;
  }[];
  progress_percentage: number;
};

export const useSalesFunnel = (startDate?: string, endDate?: string, salesOwnerId?: number) => {
  return useQuery({
    queryKey: [REPORTS_KEY, 'sales-funnel', startDate, endDate, salesOwnerId],
    queryFn: () => {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (salesOwnerId) params.append('sales_owner_id', String(salesOwnerId));
      const url = params.toString() ? `/reports/sales-funnel?${params}` : '/reports/sales-funnel';
      return api.get<SalesFunnelData>(url).then(res => res.data);
    },
  });
};

export const usePerformance = (startDate?: string, endDate?: string, salesOwnerId?: number) => {
  return useQuery({
    queryKey: [REPORTS_KEY, 'performance', startDate, endDate, salesOwnerId],
    queryFn: () => {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (salesOwnerId) params.append('sales_owner_id', String(salesOwnerId));
      const url = params.toString() ? `/reports/performance?${params}` : '/reports/performance';
      return api.get<PerformanceData>(url).then(res => res.data);
    },
  });
};

export const usePaymentProgress = (startDate?: string, endDate?: string, salesOwnerId?: number) => {
  return useQuery({
    queryKey: [REPORTS_KEY, 'payment-progress', startDate, endDate, salesOwnerId],
    queryFn: () => {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (salesOwnerId) params.append('sales_owner_id', String(salesOwnerId));
      const url = params.toString() ? `/reports/payment-progress?${params}` : '/reports/payment-progress';
      return api.get<PaymentProgressData>(url).then(res => res.data);
    },
  });
};