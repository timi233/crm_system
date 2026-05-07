import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

export const SALES_TARGET_TREE_KEY = 'sales-target-tree';
export const SALES_TARGET_ACTUAL_KEY = 'actual-performance';

/* ─── Types ─── */

export type MonthNode = {
  id: number;
  period: number;
  target_amount: number;
  gross_profit_target: number;
  remaining_rev: number;
  remaining_gp: number;
};

export type QuarterNode = {
  id: number;
  period: number;
  target_amount: number;
  gross_profit_target: number;
  remaining_rev: number;
  remaining_gp: number;
  months: MonthNode[];
};

export type YearNode = {
  id: number;
  user_id: number;
  target_year: number;
  target_amount: number;
  gross_profit_target: number;
  remaining_rev: number;
  remaining_gp: number;
  quarters: QuarterNode[];
};

export type ActualPerformance = {
  id: number;
  user_id: number;
  target_id: number | null;
  year: number;
  month: number;
  amount_actual: number;
  gross_profit_actual: number;
  created_at?: string;
  updated_at?: string;
};

export type User = {
  id: number;
  name: string;
  role?: string;
};

/* ─── Hooks ─── */

export const useSalesTargetTree = (year?: number) => {
  return useQuery({
    queryKey: [SALES_TARGET_TREE_KEY, year],
    queryFn: () => {
      const params = new URLSearchParams();
      if (year) params.append('year', String(year));
      return api
        .get<YearNode[]>(`/sales-targets/tree?${params.toString()}`)
        .then((r) => r.data);
    },
  });
};

export const useCreateYearTarget = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      user_id: number;
      target_year: number;
      target_amount: number;
      gross_profit_target: number;
    }) => api.post<YearNode>('/sales-targets/year', data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [SALES_TARGET_TREE_KEY] });
    },
  });
};

export const useDecomposeTarget = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      targetId,
      data,
    }: {
      targetId: number;
      data: {
        quarters: Record<number, number>;
        quarters_gp: Record<number, number>;
        months_by_quarter: Record<number, Record<number, number>>;
        months_gp_by_quarter: Record<number, Record<number, number>>;
      };
    }) =>
      api
        .post(`/sales-targets/${targetId}/decompose/`, data)
        .then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [SALES_TARGET_TREE_KEY] });
    },
  });
};

export const useActualRecords = (filters?: {
  user_id?: number;
  year?: number;
  month?: number;
}) => {
  return useQuery({
    queryKey: [SALES_TARGET_ACTUAL_KEY, filters],
    queryFn: () => {
      const p = new URLSearchParams();
      if (filters?.user_id) p.append('user_id', String(filters.user_id));
      if (filters?.year) p.append('year', String(filters.year));
      if (filters?.month) p.append('month', String(filters.month));
      return api
        .get<ActualPerformance[]>(
          `/sales-targets/actual/?${p.toString()}`
        )
        .then((r) => r.data);
    },
  });
};

export const useCreateActual = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      target_id: number | null;
      year: number;
      month: number;
      amount_actual: number;
      gross_profit_actual: number;
    }) =>
      api
        .post<ActualPerformance>('/sales-targets/actual/', data)
        .then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [SALES_TARGET_ACTUAL_KEY] });
      qc.invalidateQueries({ queryKey: [SALES_TARGET_TREE_KEY] });
    },
  });
};

export const useUpdateActual = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: number;
      data: Partial<ActualPerformance>;
    }) =>
      api
        .put<ActualPerformance>(`/sales-targets/actual/${id}`, data)
        .then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [SALES_TARGET_ACTUAL_KEY] });
      qc.invalidateQueries({ queryKey: [SALES_TARGET_TREE_KEY] });
    },
  });
};

export const useUsers = () => {
  return useQuery({
    queryKey: ['users'],
    queryFn: () => api.get<User[]>('/users/').then((r) => r.data),
  });
};
