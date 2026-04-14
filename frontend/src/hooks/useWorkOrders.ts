import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getWorkOrders,
  getWorkOrderById,
  createWorkOrder,
  updateWorkOrder,
  updateWorkOrderStatus,
  assignTechnicians,
  deleteWorkOrder,
  getEvaluations,
  createEvaluation,
  getEvaluationById,
} from '../services/workOrderService';
import {
  WorkOrder,
  WorkOrderCreate,
  WorkOrderUpdate,
  WorkOrderStatusUpdate,
  WorkOrderAssignRequest,
  Evaluation,
  EvaluationCreate,
  WorkOrderStatus,
} from '../types/workOrder';

export const WORK_ORDERS_QUERY_KEY = 'workOrders';
export const EVALUATIONS_QUERY_KEY = 'evaluations';

export type { WorkOrder };

export const useWorkOrders = (params?: {
  status?: WorkOrderStatus;
  submitter_id?: number;
  channel_id?: number;
}) => {
  return useQuery({
    queryKey: [WORK_ORDERS_QUERY_KEY, params],
    queryFn: () => getWorkOrders(params),
  });
};

export const useWorkOrder = (id: number | null) => {
  return useQuery({
    queryKey: [WORK_ORDERS_QUERY_KEY, id],
    queryFn: () => getWorkOrderById(id!),
    enabled: !!id,
  });
};

export const useCreateWorkOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (workOrder: WorkOrderCreate) => createWorkOrder(workOrder),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [WORK_ORDERS_QUERY_KEY] });
    },
  });
};

export const useUpdateWorkOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, workOrder }: { id: number; workOrder: WorkOrderUpdate }) =>
      updateWorkOrder(id, workOrder),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [WORK_ORDERS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [WORK_ORDERS_QUERY_KEY, variables.id] });
    },
  });
};

export const useUpdateWorkOrderStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, statusUpdate }: { id: number; statusUpdate: WorkOrderStatusUpdate }) =>
      updateWorkOrderStatus(id, statusUpdate),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [WORK_ORDERS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [WORK_ORDERS_QUERY_KEY, variables.id] });
    },
  });
};

export const useAssignTechnicians = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, assignRequest }: { id: number; assignRequest: WorkOrderAssignRequest }) =>
      assignTechnicians(id, assignRequest),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [WORK_ORDERS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [WORK_ORDERS_QUERY_KEY, variables.id] });
    },
  });
};

export const useDeleteWorkOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteWorkOrder(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [WORK_ORDERS_QUERY_KEY] });
    },
  });
};

export const useEvaluations = (workOrderId?: number) => {
  return useQuery({
    queryKey: [EVALUATIONS_QUERY_KEY, workOrderId],
    queryFn: () => getEvaluations(workOrderId),
    enabled: workOrderId !== undefined,
  });
};

export const useCreateEvaluation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (evaluation: EvaluationCreate) => createEvaluation(evaluation),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [EVALUATIONS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [WORK_ORDERS_QUERY_KEY] });
    },
  });
};

export const useEvaluation = (id: number | null) => {
  return useQuery({
    queryKey: [EVALUATIONS_QUERY_KEY, id],
    queryFn: () => getEvaluationById(id!),
    enabled: !!id,
  });
};

export const useUsers = () => {
  return useQuery({
    queryKey: ['users'],
    queryFn: () => import('../services/api').then(api => api.default.get('/users').then(res => res.data)),
  });
};

export const useChannels = (filters?: { channel_type?: string; status?: string }) => {
  return useQuery({
    queryKey: ['channels', filters],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filters?.channel_type) params.append('channel_type', filters.channel_type);
      if (filters?.status) params.append('status', filters.status);
      const url = params.toString() ? `/channels?${params.toString()}` : '/channels';
      return import('../services/api').then(api => api.default.get(url).then(res => res.data));
    },
  });
};
