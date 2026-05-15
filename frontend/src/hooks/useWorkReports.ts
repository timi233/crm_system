import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

export const WORK_REPORTS_KEY = 'work-reports';

export type WorkReport = {
  id: number;
  report_type: 'daily' | 'weekly';
  report_date: string;
  week_start?: string;
  week_end?: string;
  owner_id: number;
  owner_role?: string;
  status: 'draft' | 'submitted' | 'withdrawn';
  structured_snapshot?: StructuredSnapshot;
  remark?: string;
  source_report_ids?: number[];
  submitted_at?: string;
  withdrawn_at?: string;
  created_at?: string;
  updated_at?: string;
};

export type StructuredSnapshot = {
  follow_ups?: { count: number; items: Array<{ id: number; content?: string; type?: string }> };
  leads?: { count: number; items: Array<{ id: number; name?: string; status?: string }> };
  opportunities?: { count: number; items: Array<{ id: number; name?: string; stage?: string; amount?: number }> };
  projects?: { count: number; items: Array<{ id: number; name?: string; status?: string }> };
  contracts?: { count: number; items: Array<{ id: number; code?: string; amount?: number }> };
  work_orders?: { count: number; items: Array<{ id: number; title?: string; status?: string }> };
  channels?: { count: number; items: Array<{ id: number; name?: string; status?: string }> };
  daily_reports?: Array<{
    id: number;
    report_date: string;
    status: string;
    summary: Record<string, number>;
  }>;
  summary?: Record<string, number>;
  source_report_ids?: number[];
};

export type WorkReportListParams = {
  report_type?: 'daily' | 'weekly';
  owner_id?: number;
  status?: 'draft' | 'submitted' | 'withdrawn';
  date_from?: string;
  date_to?: string;
  skip?: number;
  limit?: number;
};

export type GenerateDraftRequest = {
  report_type: 'daily' | 'weekly';
  report_date: string;
};

export type CreateWorkReportRequest = {
  report_type: 'daily' | 'weekly';
  report_date: string;
  remark?: string;
};

export type UpdateWorkReportRequest = {
  remark?: string;
};

export const useWorkReports = (params?: WorkReportListParams, enabled: boolean = true) => {
  return useQuery({
    queryKey: [WORK_REPORTS_KEY, params],
    queryFn: () => {
      const p = new URLSearchParams();
      if (params?.report_type) p.append('report_type', params.report_type);
      if (params?.owner_id) p.append('owner_id', String(params.owner_id));
      if (params?.status) p.append('status', params.status);
      if (params?.date_from) p.append('date_from', params.date_from);
      if (params?.date_to) p.append('date_to', params.date_to);
      if (params?.skip) p.append('skip', String(params.skip));
      if (params?.limit) p.append('limit', String(params.limit));
      return api.get<WorkReport[]>(`/work-reports/?${p.toString()}`).then((r) => r.data);
    },
    enabled,
  });
};

export const useWorkReport = (id: number, enabled: boolean = true) => {
  return useQuery({
    queryKey: [WORK_REPORTS_KEY, id],
    queryFn: () => api.get<WorkReport>(`/work-reports/${id}`).then((r) => r.data),
    enabled,
  });
};

export const useTeamWorkReports = (params?: {
  report_type?: 'daily' | 'weekly';
  status?: 'draft' | 'submitted' | 'withdrawn';
  date_from?: string;
  date_to?: string;
  skip?: number;
  limit?: number;
}, enabled: boolean = true) => {
  return useQuery({
    queryKey: [WORK_REPORTS_KEY, 'team', params],
    queryFn: () => {
      const p = new URLSearchParams();
      if (params?.report_type) p.append('report_type', params.report_type);
      if (params?.status) p.append('status', params.status);
      if (params?.date_from) p.append('date_from', params.date_from);
      if (params?.date_to) p.append('date_to', params.date_to);
      if (params?.skip) p.append('skip', String(params.skip));
      if (params?.limit) p.append('limit', String(params.limit));
      return api.get<WorkReport[]>(`/work-reports/team?${p.toString()}`).then((r) => r.data);
    },
    enabled,
  });
};

export const useGenerateDraft = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: GenerateDraftRequest) =>
      api.post<WorkReport>('/work-reports/generate-draft', data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [WORK_REPORTS_KEY] });
    },
  });
};

export const useCreateWorkReport = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateWorkReportRequest) =>
      api.post<WorkReport>('/work-reports/', data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [WORK_REPORTS_KEY] });
    },
  });
};

export const useUpdateWorkReport = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateWorkReportRequest }) =>
      api.put<WorkReport>(`/work-reports/${id}`, data).then((r) => r.data),
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: [WORK_REPORTS_KEY] });
      qc.invalidateQueries({ queryKey: [WORK_REPORTS_KEY, variables.id] });
    },
  });
};

export const useSubmitWorkReport = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      api.post<WorkReport>(`/work-reports/${id}/submit`).then((r) => r.data),
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: [WORK_REPORTS_KEY] });
      qc.invalidateQueries({ queryKey: [WORK_REPORTS_KEY, id] });
    },
  });
};

export const useWithdrawWorkReport = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      api.post<WorkReport>(`/work-reports/${id}/withdraw`).then((r) => r.data),
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: [WORK_REPORTS_KEY] });
      qc.invalidateQueries({ queryKey: [WORK_REPORTS_KEY, id] });
    },
  });
};

export const useRegenerateSnapshot = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      api.post<WorkReport>(`/work-reports/${id}/regenerate`).then((r) => r.data),
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: [WORK_REPORTS_KEY] });
      qc.invalidateQueries({ queryKey: [WORK_REPORTS_KEY, id] });
    },
  });
};
