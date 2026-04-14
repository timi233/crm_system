import api from './api';
import { DispatchApplicationRequest, DispatchApplicationResponse } from '../types/dispatch';

export const createDispatchFromLead = async (
  leadId: number,
  request: DispatchApplicationRequest
): Promise<DispatchApplicationResponse> => {
  const response = await api.post<DispatchApplicationResponse>(
    `/leads/${leadId}/create-dispatch`,
    request
  );
  return response.data;
};

export const createDispatchFromOpportunity = async (
  opportunityId: number,
  request: DispatchApplicationRequest
): Promise<DispatchApplicationResponse> => {
  const response = await api.post<DispatchApplicationResponse>(
    `/opportunities/${opportunityId}/create-dispatch`,
    request
  );
  return response.data;
};

export const createDispatchFromProject = async (
  projectId: number,
  request: DispatchApplicationRequest
): Promise<DispatchApplicationResponse> => {
  const response = await api.post<DispatchApplicationResponse>(
    `/projects/${projectId}/create-dispatch`,
    request
  );
  return response.data;
};