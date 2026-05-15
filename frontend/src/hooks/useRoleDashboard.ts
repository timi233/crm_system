import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

export const ROLE_DASHBOARD_KEY = 'role-dashboard';

export type DashboardMetricCard = {
  key: string;
  title: string;
  value: number;
  unit?: string;
  trend?: number | null;
  status?: 'normal' | 'warning' | 'danger' | 'success' | string;
  link?: string | null;
};

export type DashboardTodoItem = {
  key: string;
  title: string;
  description?: string | null;
  priority?: 'low' | 'normal' | 'medium' | 'high' | string;
  due_date?: string | null;
  link?: string | null;
};

export type DashboardRiskItem = {
  key: string;
  title: string;
  description?: string | null;
  severity?: 'low' | 'medium' | 'high' | 'critical' | string;
  link?: string | null;
};

export type DashboardQuickAction = {
  key: string;
  title: string;
  link: string;
  capability?: string | null;
};

export type DashboardReportStatus = {
  daily?: string | null;
  weekly?: string | null;
  daily_draft_id?: number | null;
  weekly_draft_id?: number | null;
};

export type DashboardWorkbench = {
  role: string;
  scope: 'personal' | 'team' | 'global' | string;
  metrics: DashboardMetricCard[];
  todos: DashboardTodoItem[];
  risks: DashboardRiskItem[];
  quick_actions: DashboardQuickAction[];
  report_status?: DashboardReportStatus | null;
  generated_at: string;
};

export const useRoleDashboard = () => {
  return useQuery({
    queryKey: [ROLE_DASHBOARD_KEY, 'workbench'],
    queryFn: () => api.get<DashboardWorkbench>('/dashboard/workbench').then((res) => res.data),
  });
};
