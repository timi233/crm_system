import api from './api';
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

export interface WorkOrderQueryParams {
  status?: WorkOrderStatus;
  submitter_id?: number;
  channel_id?: number;
}

export const getWorkOrders = async (
  params?: WorkOrderQueryParams
): Promise<WorkOrder[]> => {
  const queryParams = new URLSearchParams();
  if (params?.status) queryParams.append('status', params.status);
  if (params?.submitter_id) queryParams.append('submitter_id', String(params.submitter_id));
  if (params?.channel_id) queryParams.append('channel_id', String(params.channel_id));

  const response = await api.get<WorkOrder[]>(
    `/work-orders/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
  );
  return response.data;
};

export const getWorkOrderById = async (id: number): Promise<WorkOrder> => {
  const response = await api.get<WorkOrder>(`/work-orders/${id}`);
  return response.data;
};

export const createWorkOrder = async (
  workOrder: WorkOrderCreate
): Promise<WorkOrder> => {
  const response = await api.post<WorkOrder>('/work-orders/', workOrder);
  return response.data;
};

export const updateWorkOrder = async (
  id: number,
  workOrder: WorkOrderUpdate
): Promise<WorkOrder> => {
  const response = await api.put<WorkOrder>(`/work-orders/${id}`, workOrder);
  return response.data;
};

export const updateWorkOrderStatus = async (
  id: number,
  statusUpdate: WorkOrderStatusUpdate
): Promise<WorkOrder> => {
  const response = await api.patch<WorkOrder>(
    `/work-orders/${id}/status`,
    statusUpdate
  );
  return response.data;
};

export const assignTechnicians = async (
  id: number,
  assignRequest: WorkOrderAssignRequest
): Promise<WorkOrder> => {
  const response = await api.post<WorkOrder>(
    `/work-orders/${id}/assign`,
    assignRequest
  );
  return response.data;
};

export const deleteWorkOrder = async (id: number): Promise<void> => {
  await api.delete(`/work-orders/${id}`);
};

export const getEvaluations = async (
  workOrderId?: number
): Promise<Evaluation[]> => {
  const queryParams = workOrderId
    ? `?work_order_id=${workOrderId}`
    : '';
  const response = await api.get<Evaluation[]>(`/evaluations/${queryParams}`);
  return response.data;
};

export const createEvaluation = async (
  evaluation: EvaluationCreate
): Promise<Evaluation> => {
  const response = await api.post<Evaluation>('/evaluations/', evaluation);
  return response.data;
};

export const getEvaluationById = async (id: number): Promise<Evaluation> => {
  const response = await api.get<Evaluation>(`/evaluations/${id}`);
  return response.data;
};
