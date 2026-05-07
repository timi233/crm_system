import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

export const ACTUAL_KEY = 'actual-performance';

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

export const useActualRecords = (filters?: { user_id?: number; year?: number; month?: number }) => {
  return useQuery({
    queryKey: [ACTUAL_KEY, filters],
    queryFn: () => {
      const p = new URLSearchParams();
      if (filters?.user_id) p.append('user_id', String(filters.user_id));
      if (filters?.year) p.append('year', String(filters.year));
      if (filters?.month) p.append('month', String(filters.month));
      return api.get<ActualPerformance[]>(`/sales-targets/actual/?${p.toString()}`).then(r => r.data);
    },
  });
};

export const useCreateActual = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Omit<ActualPerformance, 'id' | 'created_at' | 'updated_at'>) => 
      api.post<ActualPerformance>('/sales-targets/actual/', data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: [ACTUAL_KEY] }),
  });
};

export const useUpdateActual = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<ActualPerformance> }) =>
      api.put<ActualPerformance>(`/sales-targets/actual/${id}`, data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: [ACTUAL_KEY] }),
  });
};

export const useDeleteActual = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete(`/sales-targets/actual/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: [ACTUAL_KEY] }),
  });
};
