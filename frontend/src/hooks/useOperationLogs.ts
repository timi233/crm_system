import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

export type OperationLog = {
  id: number;
  user_id: number;
  user_name: string;
  action_type: string;
  entity_type: string;
  entity_id: number;
  entity_code: string | null;
  entity_name: string | null;
  old_value: Record<string, unknown> | null;
  new_value: Record<string, unknown> | null;
  description: string | null;
  ip_address: string | null;
  created_at: string;
};

export type OperationLogFilters = {
  entity_type?: string;
  entity_id?: number;
  user_id?: number;
  action_type?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
};

export const useOperationLogs = (filters?: OperationLogFilters) => {
  return useQuery({
    queryKey: ['operationLogs', filters],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filters?.entity_type) params.append('entity_type', filters.entity_type);
      if (filters?.entity_id) params.append('entity_id', String(filters.entity_id));
      if (filters?.user_id) params.append('user_id', String(filters.user_id));
      if (filters?.action_type) params.append('action_type', filters.action_type);
      if (filters?.start_date) params.append('start_date', filters.start_date);
      if (filters?.end_date) params.append('end_date', filters.end_date);
      if (filters?.limit) params.append('limit', String(filters.limit));
      const url = params.toString() ? `/operation-logs?${params.toString()}` : '/operation-logs';
      return api.get<OperationLog[]>(url).then(res => res.data);
    },
  });
};

export const useOperationLog = (id: number) => {
  return useQuery({
    queryKey: ['operationLog', id],
    queryFn: () => api.get<OperationLog>(`/operation-logs/${id}`).then(res => res.data),
    enabled: !!id,
  });
};

export const useEntityLogs = (entityType: string, entityId: number, limit = 50) => {
  return useQuery({
    queryKey: ['entityLogs', entityType, entityId],
    queryFn: () => api.get<OperationLog[]>(`/operation-logs/entity/${entityType}/${entityId}?limit=${limit}`).then(res => res.data),
    enabled: !!entityType && !!entityId,
  });
};

export const useUserLogs = (userId: number, limit = 50) => {
  return useQuery({
    queryKey: ['userLogs', userId],
    queryFn: () => api.get<OperationLog[]>(`/operation-logs/user/${userId}?limit=${limit}`).then(res => res.data),
    enabled: !!userId,
  });
};

export const ACTION_TYPE_LABELS: Record<string, string> = {
  CREATE: '创建',
  UPDATE: '更新',
  DELETE: '删除',
  CONVERT: '转换',
  STAGE_CHANGE: '阶段变更',
  STATUS_CHANGE: '状态变更',
};

export const ENTITY_TYPE_LABELS: Record<string, string> = {
  customer: '客户',
  lead: '线索',
  opportunity: '商机',
  project: '项目',
  contract: '合同',
  channel: '渠道',
  follow_up: '跟进记录',
};

export const getActionColor = (actionType: string): string => {
  const colors: Record<string, string> = {
    CREATE: 'green',
    UPDATE: 'blue',
    DELETE: 'red',
    CONVERT: 'purple',
    STAGE_CHANGE: 'orange',
    STATUS_CHANGE: 'cyan',
  };
  return colors[actionType] || 'default';
};